from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from pydantic import BaseModel
from typing import Dict, List
from services.type_calculation_service import TypeCalculationService
from database.models import SubKeyword

router = APIRouter()


class KeywordSelectionRequest(BaseModel):
    selections: Dict[str, List[int]]  # {"1": [69, 70], "2": [41], "3": [21, 19, 12]}


@router.post("/test/calculate")
def calculate_type(
    request: KeywordSelectionRequest,
    db: Session = Depends(get_db)
):
    """
    마음 유형 테스트 계산 API
    
    Request Body:
    {
        "selections": {
            "1": [69, 70],      // category_id: [sub_keyword_ids]
            "2": [41],
            "3": [21, 19, 12]
        }
    }
    
    Response:
    {
        "primaryType": {
            "id": 1,
            "name": "스트레스 회복자",
            "score": 12.3
        },
        "secondaryType": {
            "id": 3,
            "name": "피로 관리자",
            "score": 10.5
        },
        "finalType": {
            "id": 1,
            "name": "스트레스 조향사",
            "animal": "고슴도치",
            // ... 기타 정보
        }
    }
    """
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


@router.post("/test/debug")
def debug_calculation(
    request: KeywordSelectionRequest,
    db: Session = Depends(get_db)
):
    """
    디버깅 모드 계산 API
    """
    try:
        result = TypeCalculationService.calculate_final_type(request.selections, db, debug=True)
        
        return {
            "status": "success",
            "data": result,
            "message": "디버깅 계산이 완료되었습니다."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"디버깅 계산 중 오류: {str(e)}")


@router.get("/test/genealogy/validate/{final_type_id}")
def validate_genealogy(final_type_id: int, db: Session = Depends(get_db)):
    """
    특정 최종 유형의 족보 검증 API
    """
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