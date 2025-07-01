from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database.connection import get_db
from schemas.consultation import (
    ConsultationCardCreate,
    ConsultationCardResponse
)
from services.consultation.card_service import CardService

router = APIRouter(
    prefix="/api/v1/consultations",
    tags=["consultation-cards"]
)


@router.post("/{consultation_code}/card", response_model=ConsultationCardResponse)
def create_consultation_card(
    consultation_code: str,
    request: ConsultationCardCreate,
    db: Session = Depends(get_db)
) -> ConsultationCardResponse:
    """
    상담 카드 발급
    
    - **consultation_code**: 9자리 상담 코드
    - **additional_notes**: 추가 메모 (선택사항)
    
    완료된 상담에만 카드를 발급할 수 있습니다.
    """
    return CardService.create_consultation_card(
        db=db,
        consultation_code=consultation_code,
        additional_notes=request.additional_notes
    )


@router.get("/{consultation_code}/card", response_model=Optional[ConsultationCardResponse])
def get_consultation_card(
    consultation_code: str,
    db: Session = Depends(get_db)
) -> Optional[ConsultationCardResponse]:
    """
    상담 카드 조회
    
    - **consultation_code**: 9자리 상담 코드
    
    발급된 상담 카드가 없으면 null을 반환합니다.
    """
    return CardService.get_consultation_card(
        db=db,
        consultation_code=consultation_code
    )


@router.put("/{consultation_code}/card", response_model=ConsultationCardResponse)
def update_consultation_card(
    consultation_code: str,
    request: ConsultationCardCreate,
    db: Session = Depends(get_db)
) -> ConsultationCardResponse:
    """
    상담 카드 업데이트 (추가 메모)
    
    - **consultation_code**: 9자리 상담 코드
    - **additional_notes**: 업데이트할 추가 메모
    """
    return CardService.update_consultation_card(
        db=db,
        consultation_code=consultation_code,
        additional_notes=request.additional_notes
    )