from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from database.connection import get_db
from schemas.consultation import (
    ConsultationStartRequest,
    ConsultationResponse,
    ConsultationReconnectRequest,
    ConsultationEndResponse
)
from services.consultation import ConsultationService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/consultations",
    tags=["consultations"]
)


@router.post("/start", response_model=ConsultationResponse)
def start_consultation(
    request: ConsultationStartRequest,
    db: Session = Depends(get_db)
) -> ConsultationResponse:
    """
    새로운 상담 세션 시작
    
    - **nickname**: 사용자 닉네임 (필수)
    - **character_type_preference**: 선호하는 캐릭터 유형 ID (선택)
    - **quick_match**: 빠른 매칭 여부 (기본값: true)
    """
    try:
        return ConsultationService.start_consultation(db, request)
    except Exception as e:
        logger.error(f"상담 시작 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="상담 시작 중 오류가 발생했습니다")


@router.get("/{consultation_code}", response_model=ConsultationResponse)
def get_consultation(
    consultation_code: str,
    db: Session = Depends(get_db)
) -> ConsultationResponse:
    """
    상담 세션 정보 조회
    
    - **consultation_code**: 9자리 상담 코드
    """
    return ConsultationService.get_consultation(db, consultation_code)


@router.post("/{consultation_code}/reconnect", response_model=ConsultationResponse)
def reconnect_consultation(
    consultation_code: str,
    request: ConsultationReconnectRequest,
    db: Session = Depends(get_db)
) -> ConsultationResponse:
    """
    기존 상담 세션 재연결
    
    - **consultation_code**: 9자리 상담 코드
    - **nickname**: 변경할 닉네임 (선택)
    """
    return ConsultationService.reconnect_consultation(
        db, consultation_code, request.nickname
    )


@router.post("/{consultation_code}/end", response_model=Dict[str, Any])
def end_consultation(
    consultation_code: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    상담 종료
    
    - **consultation_code**: 9자리 상담 코드
    """
    return ConsultationService.end_consultation(db, consultation_code)