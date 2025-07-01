from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from schemas.counselor import (
    PendingRequestsResponse,
    ConsultationRequestDetail,
    ConsultationRequestResponse
)
from services.counselor import RequestService

router = APIRouter(
    prefix="/api/v1/counselors/{counselor_id}/dashboard",
    tags=["counselor-dashboard"]
)


@router.get("/requests", response_model=PendingRequestsResponse)
def get_pending_requests(
    counselor_id: int,
    db: Session = Depends(get_db)
) -> PendingRequestsResponse:
    """
    상담사의 대기 중인 상담 요청 목록 조회
    
    - **counselor_id**: 상담사 ID
    
    상담사 대시보드에서 새로운 상담 요청을 확인할 때 사용
    """
    return RequestService.get_pending_requests(db, counselor_id)


@router.post("/requests/{request_id}/accept", response_model=ConsultationRequestDetail)
def accept_consultation_request(
    counselor_id: int,
    request_id: int,
    response_data: ConsultationRequestResponse,
    db: Session = Depends(get_db)
) -> ConsultationRequestDetail:
    """
    상담 요청 수락
    
    - **counselor_id**: 상담사 ID
    - **request_id**: 요청 ID
    - **response_message**: 선택적 응답 메시지
    
    상담사가 상담 요청을 수락하면 해당 상담에 배정되고 상담이 시작됩니다.
    """
    return RequestService.accept_consultation_request(
        db, request_id, counselor_id, response_data
    )


@router.post("/requests/{request_id}/reject", response_model=ConsultationRequestDetail)
def reject_consultation_request(
    counselor_id: int,
    request_id: int,
    response_data: ConsultationRequestResponse,
    db: Session = Depends(get_db)
) -> ConsultationRequestDetail:
    """
    상담 요청 거절
    
    - **counselor_id**: 상담사 ID
    - **request_id**: 요청 ID
    - **response_message**: 선택적 거절 사유
    
    상담사가 상담 요청을 거절하면 다른 상담사에게 재요청이 시도됩니다.
    """
    return RequestService.reject_consultation_request(
        db, request_id, counselor_id, response_data
    )