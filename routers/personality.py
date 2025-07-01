from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from pydantic import BaseModel, Field
from typing import Dict, List
from services.type_calculation_service import TypeCalculationService

router = APIRouter(
    prefix="/api/v1/personality",
    tags=["personality"]
)


class KeywordSelectionRequest(BaseModel):
    """
    키워드 선택 요청 모델
    
    카테고리별로 선택한 키워드 ID 목록을 전달합니다.
    각 카테고리에서 최소 1개, 최대 3개까지 선택 가능합니다.
    """
    selections: Dict[str, List[int]] = Field(
        ...,
        description="카테고리별 선택된 키워드 ID 목록",
        example={
            "1": [69, 70, 71],  # 마음: 걱정, 긴장, 불확실성
            "2": [45, 46, 47],  # 일상: 성취, 인정, 경쟁
            "3": [22, 15, 24]   # 여유: 건강, 평온, 규칙성
        }
    )


@router.post(
    "/calculate",
    summary="🧠 성격 유형 계산",
    description="""
    선택한 키워드를 기반으로 사용자의 성격 유형을 계산합니다.
    
    **계산 과정:**
    1. 3개 카테고리(마음/일상/여유)에서 선택한 키워드 분석
    2. 16개 중간 유형별 점수 계산 (선택 순서별 가중치 적용)
    3. 상위 2개 유형 조합으로 32개 최종 캐릭터 중 하나 결정
    
    **입력 제한:**
    - 각 카테고리별 최소 1개, 최대 3개 키워드 선택
    - 모든 카테고리에서 키워드 선택 필수
    
    **가중치 시스템:**
    - 1순위 선택: 40% 가중치
    - 2순위 선택: 30% 가중치  
    - 3순위 선택: 20% 가중치
    """,
    response_description="계산된 성격 유형 정보와 상세 결과",
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
                        },
                        "message": "성격 유형 계산이 완료되었습니다."
                    }
                }
            }
        },
        400: {
            "description": "잘못된 요청 - 키워드 선택 오류"
        },
        500: {
            "description": "서버 내부 오류"
        }
    }
)
def calculate_personality_type(
    request: KeywordSelectionRequest,
    db: Session = Depends(get_db)
):
    """성격 유형 계산 API"""
    try:
        # 입력 유효성 검증
        if not request.selections:
            raise HTTPException(
                status_code=400, 
                detail="키워드 선택이 필요합니다."
            )
        
        # 카테고리별 선택 제한 확인
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
        
        # 성격 유형 계산 수행
        result = TypeCalculationService.calculate_final_type(request.selections, db)
        
        return {
            "status": "success",
            "data": result,
            "message": "성격 유형 계산이 완료되었습니다."
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"성격 유형 계산 중 오류가 발생했습니다: {str(e)}"
        )


@router.get(
    "/types/intermediate",
    summary="📊 중간 유형 목록 조회",
    description="""
    16개 중간 성격 유형의 전체 목록을 조회합니다.
    
    중간 유형은 키워드 점수 계산 후 1차적으로 분류되는 유형으로,
    이 중 상위 2개가 조합되어 최종 32개 캐릭터 유형이 결정됩니다.
    """
)
def get_intermediate_types(db: Session = Depends(get_db)):
    """중간 유형 목록 조회 API"""
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
            "total_count": len(result),
            "message": f"총 {len(result)}개의 중간 유형을 조회했습니다."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"중간 유형 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get(
    "/types/final/{final_type_id}",
    summary="🎭 최종 캐릭터 유형 상세 조회",
    description="""
    특정 최종 캐릭터 유형의 상세 정보를 조회합니다.
    
    **포함 정보:**
    - 캐릭터 기본 정보 (이름, 동물, 한줄 소개)
    - 성격 특성 (강점, 약점, 행동 패턴)
    - 관계 스타일 및 상세 설명
    - 이미지 파일명 및 아이콘 정보
    """,
    responses={
        200: {
            "description": "조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": {
                            "id": 2,
                            "name": "불안 정복자",
                            "animal": "고슴도치", 
                            "group_name": "실천형 전사",
                            "one_liner": "불안을 두려워하지 않고 행동으로 돌파하는 실천형 전사",
                            "overview": "상세 설명...",
                            "strengths": ["결단력", "실행력"],
                            "weaknesses": ["성급함", "완벽주의"]
                        }
                    }
                }
            }
        },
        404: {
            "description": "해당 유형을 찾을 수 없음"
        }
    }
)
def get_final_type_detail(final_type_id: int, db: Session = Depends(get_db)):
    """최종 캐릭터 유형 상세 조회 API"""
    try:
        final_type = TypeCalculationService.get_final_type_by_id(final_type_id, db)
        
        if not final_type:
            raise HTTPException(
                status_code=404,
                detail=f"ID {final_type_id}에 해당하는 캐릭터 유형을 찾을 수 없습니다."
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
            "message": "캐릭터 유형 조회가 완료되었습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"캐릭터 유형 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get(
    "/demo",
    summary="🎮 데모 계산",
    description="""
    미리 정의된 키워드 조합으로 성격 유형 계산을 시연합니다.
    
    **데모 키워드 조합:**
    - 마음: 걱정(69), 긴장(70)
    - 일상: 과부하(41)  
    - 여유: 활동(21), 경험(19), 상상(12)
    
    개발 및 테스트 목적으로 사용되며, 시스템이 정상 작동하는지 확인할 수 있습니다.
    """
)
def demo_personality_calculation(db: Session = Depends(get_db)):
    """데모 성격 유형 계산 API"""
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
            "message": "데모 계산 중 오류가 발생했습니다. 데이터베이스 설정을 확인해주세요."
        }