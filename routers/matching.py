from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from pydantic import BaseModel
from typing import Dict, List
from services.type_calculation_service import TypeCalculationService
from database.models import SubKeyword

router = APIRouter()

# 라우터 설정을 위한 태그 및 설명 정보
tags_metadata = [
    {
        "name": "유형 계산",
        "description": "마음 유형 테스트 계산 및 검증 관련 API",
    }
]


class KeywordSelectionRequest(BaseModel):
    """
    키워드 선택 요청 모델
    
    카테고리별로 선택한 키워드 ID 목록을 전달합니다.
    """
    selections: Dict[str, List[int]] = {
        "1": [69, 70],     # 마음 카테고리: 키워드 ID 목록
        "2": [41],         # 일상 카테고리: 키워드 ID 목록  
        "3": [21, 19, 12]  # 여유 카테고리: 키워드 ID 목록
    }
    
    class Config:
        json_schema_extra = {
            "example": {
                "selections": {
                    "1": [69, 70, 71],  # 마음: 걱정, 긴장, 불확실성
                    "2": [45, 46, 47],  # 일상: 성취, 인정, 경쟁
                    "3": [22, 15, 24]   # 여유: 건강, 평온, 규칙성
                }
            }
        }


@router.post(
    "/test/calculate",
    summary="🧠 마음 유형 테스트 계산",
    description="""
    선택한 키워드를 기반으로 사용자의 마음 유형을 계산합니다.
    
    **계산 과정:**
    1. 3개 카테고리(마음/일상/여유)에서 선택한 키워드 분석
    2. 16개 중간 유형별 점수 계산 (가중치 적용)
    3. 상위 2개 유형 조합으로 최종 캐릭터 결정
    
    **입력 제한:**
    - 각 카테고리별 최대 3개 키워드 선택
    - 최소 1개 키워드는 필수 선택
    """,
    response_description="계산된 유형 정보와 상세 결과",
    responses={
        200: {
            "description": "계산 성공",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": {
                            "primaryType": {
                                "id": 2,
                                "name": "불안 극복자",
                                "score": 14.5
                            },
                            "secondaryType": {
                                "id": 7,
                                "name": "효율 추구자",
                                "score": 13.0
                            },
                            "finalType": {
                                "id": 2,
                                "name": "불안 정복자",
                                "animal": "고슴도치",
                                "one_liner": "불안을 두려워하지 않고 행동으로 돌파하는 실천형 전사"
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "잘못된 요청 (키워드 선택 오류)"
        },
        500: {
            "description": "서버 내부 오류"
        }
    }
)
def calculate_type(
    request: KeywordSelectionRequest,
    db: Session = Depends(get_db)
):
    try:
        # 입력 유효성 검증
        if not request.selections:
            raise HTTPException(status_code=400, detail="키워드 선택이 필요합니다.")
        
        # 카테고리별 최대 3개 선택 제한 확인
        for category_id, keyword_ids in request.selections.items():
            if len(keyword_ids) > 3:
                raise HTTPException(
                    status_code=400, 
                    detail=f"카테고리 {category_id}에서 최대 3개까지만 선택 가능합니다."
                )
            if len(keyword_ids) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"카테고리 {category_id}에서 최소 1개는 선택해야 합니다."
                )
        
        # 유형 계산 수행
        result = TypeCalculationService.calculate_final_type(request.selections, db)
        
        return {
            "status": "success",
            "data": result,
            "message": "유형 계산이 완료되었습니다."
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"유형 계산 중 오류가 발생했습니다: {str(e)}")


@router.get("/test/types/intermediate")
def get_intermediate_types(db: Session = Depends(get_db)):
    """
    모든 중간 유형 조회 API
    """
    try:
        types = TypeCalculationService.get_all_intermediate_types(db)
        
        result = []
        for type_obj in types:
            result.append({
                "id": type_obj.id,
                "name": type_obj.name,
                "description": type_obj.description,
                "characteristics": type_obj.characteristics,
                "display_order": type_obj.display_order
            })
        
        return {
            "status": "success",
            "data": result,
            "message": f"총 {len(result)}개의 중간 유형을 조회했습니다."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"중간 유형 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/test/types/final/{final_type_id}")
def get_final_type(final_type_id: int, db: Session = Depends(get_db)):
    """
    특정 최종 유형 조회 API
    """
    try:
        final_type = TypeCalculationService.get_final_type_by_id(final_type_id, db)
        
        if not final_type:
            raise HTTPException(
                status_code=404,
                detail=f"ID {final_type_id}에 해당하는 최종 유형을 찾을 수 없습니다."
            )
        
        result = {
            "id": final_type.id,
            "name": final_type.name,
            "animal": final_type.animal,
            "group_name": final_type.group_name,
            "one_liner": final_type.one_liner,
            "overview": final_type.overview,
            "greeting": final_type.greeting,
            "hashtags": final_type.hashtags,
            "strengths": final_type.strengths,
            "weaknesses": final_type.weaknesses,
            "relationship_style": final_type.relationship_style,
            "behavior_pattern": final_type.behavior_pattern,
            "image_filename": final_type.image_filename,
            "image_filename_right": final_type.image_filename_right,
            "strength_icons": final_type.strength_icons,
            "weakness_icons": final_type.weakness_icons
        }
        
        return {
            "status": "success",
            "data": result,
            "message": "최종 유형 조회가 완료되었습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"최종 유형 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/test/demo")
def demo_calculation(db: Session = Depends(get_db)):
    """
    데모 계산 API (테스트용)
    """
    # 예시 키워드 선택
    demo_selections = {
        "1": [69, 70],      # 마음: 걱정(69), 긴장(70)
        "2": [41],          # 일상: 과부하(41)
        "3": [21, 19, 12]   # 여유: 활동(21), 경험(19), 상상(12)
    }
    
    try:
        result = TypeCalculationService.calculate_final_type(demo_selections, db)
        
        return {
            "status": "success",
            "demo_selections": demo_selections,
            "calculation_result": result,
            "message": "데모 계산이 완료되었습니다."
        }
        
    except Exception as e:
        return {
            "status": "error",
            "demo_selections": demo_selections,
            "error": str(e),
            "message": "데모 계산 중 오류가 발생했습니다. DB 데이터 설정을 확인해주세요."
        }


@router.post(
    "/test/debug",
    summary="🔍 디버깅 모드 계산",
    description="""
    개발자용 디버깅 모드로 계산 과정을 상세히 분석합니다.
    
    **디버깅 정보:**
    - 각 키워드별 원점수 및 가중치 적용 점수
    - 카테고리별 점수 합산 과정
    - 16개 유형별 최종 점수 순위
    - 계산 과정 콘솔 출력
    """,
    response_description="상세한 계산 과정 정보 포함"
)
def debug_calculation(
    request: KeywordSelectionRequest,
    db: Session = Depends(get_db)
):
    try:
        result = TypeCalculationService.calculate_final_type(request.selections, db, debug=True)
        
        return {
            "status": "success",
            "data": result,
            "message": "디버깅 계산이 완료되었습니다."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"디버깅 계산 중 오류: {str(e)}")


@router.get(
    "/test/genealogy/validate/{final_type_id}",
    summary="🧬 족보 검증",
    description="""
    특정 최종 유형의 대표 키워드 조합(족보)이 올바르게 해당 유형을 결과로 내는지 검증합니다.
    
    **검증 과정:**
    1. 해당 유형의 정의된 족보 키워드로 계산 수행
    2. 결과가 기대하는 유형과 일치하는지 확인
    3. 불일치 시 점수 조정이 필요한 부분 분석
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
def validate_genealogy(final_type_id: int, db: Session = Depends(get_db)):
    # 32개 유형별 족보 정의
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
        # 추가 족보들은 필요시 확장
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
        raise HTTPException(status_code=500, detail=f"족보 검증 중 오류: {str(e)}")


@router.get("/test/genealogy/validate-all")
def validate_all_genealogies(db: Session = Depends(get_db)):
    """
    모든 정의된 족보 검증 API
    """
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
        # 추가 족보들
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