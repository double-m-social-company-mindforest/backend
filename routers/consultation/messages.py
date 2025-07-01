from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from database.connection import get_db
from schemas.consultation import MessagesHistoryResponse
from services.consultation.message_service import MessageService

router = APIRouter(
    prefix="/api/v1/consultations",
    tags=["consultation-messages"]
)


@router.get("/{consultation_code}/messages", response_model=MessagesHistoryResponse)
def get_consultation_messages(
    consultation_code: str,
    limit: Optional[int] = Query(50, ge=1, le=500, description="조회할 메시지 수 (1-500)"),
    offset: Optional[int] = Query(0, ge=0, description="오프셋"),
    db: Session = Depends(get_db)
) -> MessagesHistoryResponse:
    """
    상담 메시지 히스토리 조회
    
    - **consultation_code**: 9자리 상담 코드
    - **limit**: 조회할 메시지 수 (기본값: 50, 최대: 500)
    - **offset**: 오프셋 (기본값: 0)
    """
    return MessageService.get_messages_history(
        db=db,
        consultation_code=consultation_code,
        limit=limit,
        offset=offset
    )