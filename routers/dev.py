import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from pydantic import BaseModel
from typing import Dict, List
from services.type_calculation_service import TypeCalculationService
from database.models import SubKeyword

# 개발 환경에서만 활성화
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

router = APIRouter(
    prefix="/api/v1/dev",
    tags=["dev-tools"],
    include_in_schema=ENVIRONMENT == "development"  # 개발 환경에서만 API 문서에 포함
)


class KeywordSelectionRequest(BaseModel):
    """키워드 선택 요청 모델 (개발용)"""
    selections: Dict[str, List[int]]


@router.post(
    "/debug/calculate",
    summary="🔍 디버깅 모드 성격 유형 계산",
    description="""
    **⚠️ 개발자 전용 도구**
    
    성격 유형 계산 과정을 상세히 분석하는 디버깅 모드입니다.
    
    **디버깅 정보:**
    - 각 키워드별 원점수 및 가중치 적용 점수
    - 카테고리별 점수 합산 과정
    - 16개 중간 유형별 최종 점수 순위
    - 계산 과정 콘솔 출력
    - 점수 계산 상세 로그
    
    운영 환경에서는 사용할 수 없습니다.
    """,
    response_description="상세한 계산 과정 정보 포함"
)
def debug_personality_calculation(
    request: KeywordSelectionRequest,
    db: Session = Depends(get_db)
):
    """디버깅 모드 성격 유형 계산"""
    if ENVIRONMENT != "development":
        raise HTTPException(
            status_code=403, 
            detail="개발 환경에서만 사용 가능한 기능입니다."
        )
    
    try:
        result = TypeCalculationService.calculate_final_type(
            request.selections, db, debug=True
        )
        
        return {
            "status": "success",
            "environment": ENVIRONMENT,
            "data": result,
            "debug_info": {
                "input_selections": request.selections,
                "calculation_mode": "debug",
                "detailed_logs": "콘솔 로그를 확인하세요."
            },
            "message": "디버깅 계산이 완료되었습니다."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"디버깅 계산 중 오류: {str(e)}"
        )


@router.get(
    "/genealogy/validate/{final_type_id}",
    summary="🧬 족보 검증",
    description="""
    **⚠️ 개발자 전용 도구**
    
    특정 최종 유형의 대표 키워드 조합(족보)이 올바르게 해당 유형을 결과로 내는지 검증합니다.
    
    **검증 과정:**
    1. 해당 유형의 정의된 족보 키워드로 계산 수행
    2. 결과가 기대하는 유형과 일치하는지 확인
    3. 불일치 시 점수 조정이 필요한 부분 분석
    
    **사용 목적:**
    - 알고리즘 정확성 검증
    - 키워드-유형 매핑 검증
    - 점수 가중치 튜닝
    """,
    responses={
        200: {
            "description": "검증 완료",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "validation": {
                            "expected_final_type_id": 2,
                            "calculated_final_type_id": 2,
                            "is_correct": True
                        },
                        "message": "족보 검증 성공"
                    }
                }
            }
        },
        404: {
            "description": "해당 유형의 족보가 정의되지 않음"
        }
    }
)
def validate_type_genealogy(final_type_id: int, db: Session = Depends(get_db)):
    """특정 유형의 족보 검증"""
    if ENVIRONMENT != "development":
        raise HTTPException(
            status_code=403,
            detail="개발 환경에서만 사용 가능한 기능입니다."
        )
    
    # 32개 유형별 족보 정의 (대표적인 키워드 조합)
    genealogies = {
        1: {  # 스트레스 조향사
            "1": [69, 58, 60],  # 마음: 걱정, 피로, 압박감
            "2": [41, 42, 43],  # 일상: 과부하, 압박, 피로
            "3": [14, 13, 16]   # 여유: 명상, 수면, 재충전
        },
        2: {  # 불안 정복자
            "1": [69, 70, 71],  # 마음: 걱정, 긴장, 불확실성
            "2": [45, 46, 47],  # 일상: 성취, 인정, 경쟁
            "3": [22, 15, 24]   # 여유: 건강, 평온, 규칙성
        },
        # 추가 족보들은 필요시 확장 가능
    }
    
    if final_type_id not in genealogies:
        raise HTTPException(
            status_code=404, 
            detail=f"최종 유형 ID {final_type_id}의 족보가 정의되지 않았습니다."
        )
    
    try:
        genealogy = genealogies[final_type_id]
        
        # 족보로 계산 수행 (디버깅 모드)
        result = TypeCalculationService.calculate_final_type(genealogy, db, debug=True)
        
        # 결과 검증
        calculated_final_type_id = result.get("finalType", {}).get("id")
        is_correct = calculated_final_type_id == final_type_id
        
        # 키워드 이름 조회
        keyword_names = {}
        for category_id, keyword_ids in genealogy.items():
            category_keywords = []
            for keyword_id in keyword_ids:
                keyword = db.query(SubKeyword).filter(SubKeyword.id == keyword_id).first()
                if keyword:
                    category_keywords.append(f"{keyword.name}({keyword_id})")
                else:
                    category_keywords.append(f"ID-{keyword_id}")
            keyword_names[f"카테고리_{category_id}"] = category_keywords
        
        return {
            "status": "success" if is_correct else "validation_failed",
            "final_type_id": final_type_id,
            "genealogy_keywords": keyword_names,
            "calculation_result": result,
            "validation": {
                "expected_final_type_id": final_type_id,
                "calculated_final_type_id": calculated_final_type_id,
                "is_correct": is_correct,
                "primary_type": result.get("primaryType", {}),
                "secondary_type": result.get("secondaryType", {})
            },
            "message": f"족보 검증 {'성공' if is_correct else '실패'}: 기대 {final_type_id} → 실제 {calculated_final_type_id}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"족보 검증 중 오류: {str(e)}"
        )


@router.get(
    "/genealogy/validate-all",
    summary="🧬 전체 족보 검증",
    description="""
    **⚠️ 개발자 전용 도구**
    
    정의된 모든 족보를 일괄 검증하여 알고리즘의 전체적인 정확성을 확인합니다.
    
    **검증 결과:**
    - 전체 족보 개수
    - 정확한 족보 개수
    - 정확도 비율
    - 실패한 족보 상세 정보
    
    **사용 목적:**
    - 전체 알고리즘 품질 확인
    - 점수 가중치 변경 후 영향도 분석
    - 회귀 테스트
    """
)
def validate_all_genealogies(db: Session = Depends(get_db)):
    """모든 정의된 족보 검증"""
    if ENVIRONMENT != "development":
        raise HTTPException(
            status_code=403,
            detail="개발 환경에서만 사용 가능한 기능입니다."
        )
    
    genealogies = {
        1: {  # 스트레스 조향사
            "1": [69, 58, 60],  # 마음: 걱정, 피로, 압박감
            "2": [41, 42, 43],  # 일상: 과부하, 압박, 피로
            "3": [14, 13, 16]   # 여유: 명상, 수면, 재충전
        },
        2: {  # 불안 정복자
            "1": [69, 70, 71],  # 마음: 걱정, 긴장, 불확실성
            "2": [45, 46, 47],  # 일상: 성취, 인정, 경쟁
            "3": [22, 15, 24]   # 여유: 건강, 평온, 규칙성
        },
        # 추가 족보들은 확장 가능
    }
    
    results = []
    
    for final_type_id, genealogy in genealogies.items():
        try:
            result = TypeCalculationService.calculate_final_type(genealogy, db, debug=False)
            calculated_final_type_id = result.get("finalType", {}).get("id")
            is_correct = calculated_final_type_id == final_type_id
            
            results.append({
                "final_type_id": final_type_id,
                "expected": final_type_id,
                "calculated": calculated_final_type_id,
                "is_correct": is_correct,
                "final_type_name": result.get("finalType", {}).get("name"),
                "primary_type": result.get("primaryType", {}).get("name"),
                "secondary_type": result.get("secondaryType", {}).get("name")
            })
            
        except Exception as e:
            results.append({
                "final_type_id": final_type_id,
                "error": str(e),
                "is_correct": False
            })
    
    # 통계 계산
    total_count = len(results)
    correct_count = sum(1 for r in results if r.get("is_correct", False))
    incorrect_results = [r for r in results if not r.get("is_correct", False)]
    
    return {
        "status": "success",
        "environment": ENVIRONMENT,
        "summary": {
            "total_genealogies": total_count,
            "correct_count": correct_count,
            "incorrect_count": total_count - correct_count,
            "accuracy_rate": f"{correct_count/total_count*100:.1f}%" if total_count > 0 else "0%"
        },
        "results": results,
        "incorrect_genealogies": incorrect_results,
        "message": f"전체 족보 검증 완료: {correct_count}/{total_count} 성공"
    }


@router.get(
    "/system/info",
    summary="ℹ️ 시스템 정보",
    description="""
    **⚠️ 개발자 전용 도구**
    
    개발 환경의 시스템 정보를 조회합니다.
    """
)
def get_system_info():
    """시스템 정보 조회"""
    if ENVIRONMENT != "development":
        raise HTTPException(
            status_code=403,
            detail="개발 환경에서만 사용 가능한 기능입니다."
        )
    
    return {
        "status": "success",
        "system_info": {
            "environment": ENVIRONMENT,
            "debug_mode": True,
            "api_version": "v1",
            "dev_tools_enabled": True
        },
        "message": "개발 환경 정보입니다."
    }