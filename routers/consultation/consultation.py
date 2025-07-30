from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from database.connection import get_db
from schemas.consultation.consultation import (
    ConsultationStartRequest,
    ConsultationResponse,
    ConsultationReconnectRequest,
    ConsultationEndResponse,
    ReconsultationRequest
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


@router.delete("/{consultation_code}/cancel", response_model=Dict[str, Any])
def cancel_consultation(
    consultation_code: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    상담 취소 (매칭 대기 중 사용자가 나가는 경우)
    
    - **consultation_code**: 9자리 상담 코드
    
    **취소 처리:**
    - 대기 중(waiting) 상담만 취소 가능
    - 상담 데이터와 관련 요청 모두 DB에서 삭제
    - 상담사가 수락 시 자동으로 없는 것으로 표시됨
    - 별도의 알림 취소 처리 없음 (사용자 요구사항)
    """
    return ConsultationService.cancel_consultation(db, consultation_code)


@router.post("/{consultation_code}/end", response_model=ConsultationEndResponse)
def end_consultation(
    consultation_code: str,
    db: Session = Depends(get_db)
) -> ConsultationEndResponse:
    """
    상담 종료
    
    - **consultation_code**: 9자리 상담 코드
    """
    return ConsultationService.end_consultation(db, consultation_code)


@router.post("/reconsult", response_model=ConsultationResponse)
def start_reconsultation(
    request: ReconsultationRequest,
    db: Session = Depends(get_db)
) -> ConsultationResponse:
    """
    이전 상담사와 재상담 시작
    
    - **nickname**: 사용자 닉네임 (필수)
    - **previous_consultation_code**: 이전 상담 코드 (필수)
    - **counselor_id**: 재상담 요청할 상담사 ID (필수)
    
    **재상담 프로세스:**
    1. 이전 상담 정보 확인
    2. 상담사 가용성 확인
    3. 새로운 상담 세션 생성
    4. 해당 상담사에게만 WebSocket 알림 전송
    """
    try:
        return ConsultationService.start_reconsultation(db, request)
    except Exception as e:
        logger.error(f"재상담 시작 중 오류 발생: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="재상담 시작 중 오류가 발생했습니다")