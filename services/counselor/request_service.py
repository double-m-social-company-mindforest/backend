from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import and_
from fastapi import HTTPException
from database.models import (
    ConsultationRequest, 
    Consultation, 
    Counselor,
    CounselorStatus,
    ConsultationStatus
)
from schemas.counselor import (
    ConsultationRequestDetail,
    PendingRequestsResponse,
    ConsultationRequestResponse
)
from services.counselor.matching_service import MatchingService
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RequestService:
    @staticmethod
    def get_pending_requests(
        db: Session, 
        counselor_id: int
    ) -> PendingRequestsResponse:
        """
        상담사의 대기 중인 상담 요청 목록 조회
        
        Args:
            db: 데이터베이스 세션
            counselor_id: 상담사 ID
            
        Returns:
            PendingRequestsResponse: 대기 중인 요청 목록
        """
        # 현재 상담사 정보 조회
        current_counselor = db.query(Counselor).filter(Counselor.id == counselor_id).first()
        if not current_counselor:
            raise HTTPException(status_code=404, detail="상담사를 찾을 수 없습니다")
        
        # 콜대기 상태인 상담사는 모든 pending 요청을 볼 수 있음
        # 다른 상태의 상담사는 본인에게 배정된 요청만 볼 수 있음
        if current_counselor.status == CounselorStatus.waiting_for_call:
            # 모든 pending 요청 조회 (콜대기 상담사용)
            requests = db.query(
                ConsultationRequest,
                Consultation.consultation_code,
                Consultation.user_nickname,
                Consultation.character_name,
                Counselor.name.label('counselor_name')
            ).join(
                Consultation, ConsultationRequest.consultation_id == Consultation.id
            ).join(
                Counselor, ConsultationRequest.counselor_id == Counselor.id
            ).filter(
                ConsultationRequest.status == "pending"
            ).order_by(ConsultationRequest.requested_at.desc()).all()
        else:
            # 본인에게 배정된 요청만 조회 (일반 상담사용)
            requests = db.query(
                ConsultationRequest,
                Consultation.consultation_code,
                Consultation.user_nickname,
                Consultation.character_name,
                Counselor.name.label('counselor_name')
            ).join(
                Consultation, ConsultationRequest.consultation_id == Consultation.id
            ).join(
                Counselor, ConsultationRequest.counselor_id == Counselor.id
            ).filter(
                and_(
                    ConsultationRequest.counselor_id == counselor_id,
                    ConsultationRequest.status == "pending"
                )
            ).order_by(ConsultationRequest.requested_at.desc()).all()
        
        # 응답 객체 생성
        request_details = []
        for req, consultation_code, user_nickname, character_name, counselor_name in requests:
            detail = ConsultationRequestDetail(
                id=req.id,
                consultation_id=req.consultation_id,
                counselor_id=req.counselor_id,
                status=req.status,
                requested_at=req.requested_at,
                responded_at=req.responded_at,
                response_message=req.response_message,
                consultation_code=consultation_code,
                user_nickname=user_nickname,
                character_type_name=character_name,
                counselor_name=counselor_name
            )
            request_details.append(detail)
        
        return PendingRequestsResponse(
            requests=request_details,
            total_count=len(request_details)
        )
    
    @staticmethod
    def accept_consultation_request(
        db: Session,
        request_id: int,
        counselor_id: int,
        response_data: ConsultationRequestResponse
    ) -> ConsultationRequestDetail:
        """
        상담 요청 수락
        
        Args:
            db: 데이터베이스 세션
            request_id: 요청 ID
            counselor_id: 상담사 ID
            response_data: 응답 메시지
            
        Returns:
            ConsultationRequestDetail: 업데이트된 요청 정보
        """
        # 브로드캐스트 시스템: 선착순 수락 처리
        # 트랜잭션으로 race condition 방지
        from sqlalchemy import text
        
        # 해당 상담의 모든 pending 요청 조회 (선착순 경쟁)
        consultation_id = db.execute(
            text("SELECT consultation_id FROM consultation_requests WHERE id = :request_id"),
            {"request_id": request_id}
        ).scalar()
        
        if not consultation_id:
            raise HTTPException(
                status_code=404, 
                detail=f"요청 ID {request_id}가 존재하지 않습니다"
            )
        
        # 해당 상담이 이미 배정되었는지 확인
        consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
        if consultation.counselor_id is not None:
            raise HTTPException(
                status_code=409, 
                detail="이미 다른 상담사가 수락한 상담입니다"
            )
        
        # 현재 요청이 여전히 pending인지 확인
        request = db.query(ConsultationRequest).filter(
            and_(
                ConsultationRequest.id == request_id,
                ConsultationRequest.status == "pending"
            )
        ).first()
        
        if not request:
            raise HTTPException(
                status_code=410, 
                detail="요청이 만료되었거나 이미 처리되었습니다"
            )
        
        # 상담사가 현재 상담 가능한지 확인
        counselor = db.query(Counselor).filter(Counselor.id == counselor_id).first()
        if not counselor:
            raise HTTPException(status_code=404, detail="상담사를 찾을 수 없습니다")
        
        if counselor.status not in [CounselorStatus.online, CounselorStatus.waiting_for_call]:
            raise HTTPException(status_code=400, detail="현재 상담 불가능한 상태입니다")
        
        # 동시 상담 수 확인
        active_count = db.query(Consultation).filter(
            and_(
                Consultation.counselor_id == counselor_id,
                Consultation.status.in_([ConsultationStatus.waiting, ConsultationStatus.active])
            )
        ).count()
        
        if active_count >= counselor.max_concurrent_sessions:
            raise HTTPException(status_code=400, detail="동시 상담 가능 수를 초과했습니다")
        
        # 요청 수락 처리
        request.status = "accepted"
        request.responded_at = func.now()
        request.response_message = response_data.response_message
        
        # 다른 상담사가 요청을 수락한 경우 counselor_id 변경
        if request.counselor_id != counselor_id:
            logger.info(f"요청 {request_id}을 다른 상담사가 수락: 원래={request.counselor_id}, 수락자={counselor_id}")
            request.counselor_id = counselor_id
        
        # 상담사 상태를 busy로 변경
        counselor.status = CounselorStatus.busy
        counselor.last_active_at = func.now()
        
        # 상담에 상담사 배정
        MatchingService.assign_counselor_to_consultation(
            db, request.consultation_id, counselor_id
        )
        
        # 브로드캐스트 시스템: 같은 상담에 대한 다른 모든 pending 요청들 자동 취소
        cancelled_requests = db.query(ConsultationRequest).filter(
            and_(
                ConsultationRequest.consultation_id == request.consultation_id,
                ConsultationRequest.id != request_id,
                ConsultationRequest.status == "pending"
            )
        ).all()
        
        cancelled_count = 0
        for other_req in cancelled_requests:
            other_req.status = "cancelled"  # 브로드캐스트 시스템에서는 cancelled 사용
            other_req.responded_at = func.now()
            other_req.response_message = f"다른 상담사가 먼저 수락했습니다 (수락자: {counselor.name})"
            cancelled_count += 1
        
        logger.info(f"브로드캐스트 수락 완료: 수락자={counselor.name}, 취소된 요청={cancelled_count}개")
        
        db.commit()
        db.refresh(request)
        
        logger.info(f"상담 요청 수락: 요청={request_id}, 상담사={counselor_id}")
        
        # 응답 생성
        consultation = request.consultation
        return ConsultationRequestDetail(
            id=request.id,
            consultation_id=request.consultation_id,
            counselor_id=request.counselor_id,
            status=request.status,
            requested_at=request.requested_at,
            responded_at=request.responded_at,
            response_message=request.response_message,
            consultation_code=consultation.consultation_code,
            user_nickname=consultation.user_nickname,
            character_type_name=consultation.character_name,
            counselor_name=counselor.name
        )
    
    @staticmethod
    def reject_consultation_request(
        db: Session,
        request_id: int,
        counselor_id: int,
        response_data: ConsultationRequestResponse
    ) -> ConsultationRequestDetail:
        """
        상담 요청 거절
        
        Args:
            db: 데이터베이스 세션
            request_id: 요청 ID
            counselor_id: 상담사 ID
            response_data: 응답 메시지
            
        Returns:
            ConsultationRequestDetail: 업데이트된 요청 정보
        """
        # 요청 조회 (콜대기 상담사는 다른 상담사의 요청도 거절 가능)
        request = db.query(ConsultationRequest).filter(
            and_(
                ConsultationRequest.id == request_id,
                ConsultationRequest.status == "pending"
            )
        ).first()
        
        if not request:
            raise HTTPException(status_code=404, detail="요청을 찾을 수 없거나 이미 처리되었습니다")
        
        # 요청 거절 처리
        request.status = "rejected"
        request.responded_at = func.now()
        request.response_message = response_data.response_message or "상담사가 거절했습니다"
        
        db.commit()
        db.refresh(request)
        
        logger.info(f"상담 요청 거절: 요청={request_id}, 상담사={counselor_id}")
        
        # 다른 사용 가능한 상담사에게 재요청 시도
        try:
            consultation = request.consultation
            MatchingService.reassign_consultation(db, consultation.consultation_code)
        except Exception as e:
            logger.warning(f"상담 재배정 실패: {e}")
        
        # 응답 생성
        consultation = request.consultation
        counselor = request.counselor
        return ConsultationRequestDetail(
            id=request.id,
            consultation_id=request.consultation_id,
            counselor_id=request.counselor_id,
            status=request.status,
            requested_at=request.requested_at,
            responded_at=request.responded_at,
            response_message=request.response_message,
            consultation_code=consultation.consultation_code,
            user_nickname=consultation.user_nickname,
            character_type_name=consultation.character_name,
            counselor_name=counselor.name
        )
    
    @staticmethod
    def cleanup_expired_requests(db: Session, expiry_minutes: int = 5):
        """
        만료된 상담 요청 정리
        
        Args:
            db: 데이터베이스 세션
            expiry_minutes: 만료 시간 (분)
        """
        expiry_time = datetime.utcnow() - timedelta(minutes=expiry_minutes)
        
        expired_requests = db.query(ConsultationRequest).filter(
            and_(
                ConsultationRequest.status == "pending",
                ConsultationRequest.requested_at < expiry_time
            )
        ).all()
        
        for request in expired_requests:
            request.status = "expired"
            request.responded_at = func.now()
            request.response_message = "요청 시간이 만료되었습니다"
            
            # 만료된 상담에 대해 다른 상담사에게 재요청 시도
            try:
                consultation = request.consultation
                if consultation.status == ConsultationStatus.waiting:
                    MatchingService.reassign_consultation(db, consultation.consultation_code)
            except Exception as e:
                logger.warning(f"만료된 상담 재배정 실패: {e}")
        
        if expired_requests:
            db.commit()
            logger.info(f"만료된 상담 요청 {len(expired_requests)}개 정리 완료")