from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database.connection import get_db
from services.consultation.music_service import MusicService
from typing import Dict, Any

router = APIRouter(
    prefix="/api/v1/consultations",
    tags=["consultation-music"]
)


@router.get("/{consultation_code}/music-recommendations", response_model=Dict[str, Any])
async def get_music_recommendations(
    consultation_code: str,
    take: int = Query(3, ge=1, le=10, description="추천받을 음원 수 (1-10)"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    상담 중 최근 대화 기반 음원 추천
    
    - **consultation_code**: 9자리 상담 코드
    - **take**: 추천받을 음원 수 (1-10, 기본값: 3)
    
    현재 진행 중인 상담의 최근 대화 내용(최대 1000자)을 분석하여
    Link Music API를 통해 적합한 음원을 추천합니다.
    """
    try:
        return await MusicService.get_music_recommendations(
            db=db,
            consultation_code=consultation_code,
            take=take
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"음원 추천 중 오류가 발생했습니다: {str(e)}"
        )