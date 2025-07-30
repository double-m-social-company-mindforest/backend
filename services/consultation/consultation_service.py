from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from fastapi import HTTPException
from datetime import datetime
import pytz
from database.models import Consultation, ConsultationStatus, FinalType, Counselor, CounselorStatus, ConsultationRequest
from schemas.consultation.consultation import ConsultationStartRequest, ConsultationResponse, ConsultationEndResponse, ReconsultationRequest
from .code_generator import generate_consultation_code
import random
import logging

logger = logging.getLogger(__name__)




class ConsultationService:
    @staticmethod
    def start_consultation(
        db: Session,
        request: ConsultationStartRequest
    ) -> ConsultationResponse:
        """
        새로운 상담 세션 시작 (실제 상담사 매칭)
        
        Args:
            db: 데이터베이스 세션
            request: 상담 시작 요청 정보
            
        Returns:
            ConsultationResponse: 생성된 상담 정보
        """
        # 실제 상담사 매칭 서비스 사용
        from services.counselor.matching_service import MatchingService
        return MatchingService.find_and_assign_counselor(db, request)
    
    @staticmethod
    def get_consultation(db: Session, consultation_code: str) -> ConsultationResponse:
        """
        상담 세션 정보 조회
        
        Args:
            db: 데이터베이스 세션
            consultation_code: 상담 코드
            
        Returns:
            ConsultationResponse: 상담 정보
        """
        consultation = db.query(Consultation).filter(
            Consultation.consultation_code == consultation_code
        ).first()
        
        if not consultation:
            raise HTTPException(status_code=404, detail="상담 세션을 찾을 수 없습니다")
        
        character_type = consultation.character_type
        
        return ConsultationResponse(
            id=consultation.id,
            consultation_code=consultation.consultation_code,
            user_nickname=consultation.user_nickname,
            character_type_id=consultation.character_type_id,
            character_name=consultation.character_name,
            character_animal=character_type.animal,
            character_group=character_type.group_name,
            status=consultation.status,
            created_at=consultation.created_at,
            completed_at=consultation.completed_at,
            is_card_issued=consultation.is_card_issued
        )
    
    @staticmethod
    def reconnect_consultation(
        db: Session,
        consultation_code: str,
        nickname: Optional[str] = None
    ) -> ConsultationResponse:
        """
        기존 상담 세션 재연결
        
        Args:
            db: 데이터베이스 세션
            consultation_code: 상담 코드
            nickname: 변경할 닉네임 (선택사항)
            
        Returns:
            ConsultationResponse: 상담 정보
        """
        consultation = db.query(Consultation).filter(
            Consultation.consultation_code == consultation_code
        ).first()
        
        if not consultation:
            raise HTTPException(status_code=404, detail="상담 세션을 찾을 수 없습니다")
        
        # 종료된 상담은 재연결 불가
        if consultation.status == ConsultationStatus.terminated:
            raise HTTPException(status_code=400, detail="종료된 상담은 재연결할 수 없습니다")
        
        # 닉네임 변경 (선택사항)
        if nickname:
            consultation.user_nickname = nickname
        
        # 상태를 active로 변경
        if consultation.status == ConsultationStatus.waiting:
            consultation.status = ConsultationStatus.active
        
        db.commit()
        db.refresh(consultation)
        
        return ConsultationService.get_consultation(db, consultation_code)
    
    @staticmethod
    def end_consultation(
        db: Session,
        consultation_code: str
    ) -> ConsultationEndResponse:
        """
        상담 종료
        
        Args:
            db: 데이터베이스 세션
            consultation_code: 상담 코드
            
        Returns:
            dict: 종료 결과
        """
        consultation = db.query(Consultation).filter(
            Consultation.consultation_code == consultation_code
        ).first()
        
        if not consultation:
            raise HTTPException(status_code=404, detail="상담 세션을 찾을 수 없습니다")
        
        if consultation.status in [ConsultationStatus.completed, ConsultationStatus.terminated]:
            raise HTTPException(status_code=400, detail="이미 종료된 상담입니다")
        
        # 상담 종료 처리
        consultation.status = ConsultationStatus.completed
        # 한국 시간으로 저장
        kst = pytz.timezone('Asia/Seoul')
        consultation.completed_at = datetime.now(kst)
        
        # 상담사 상태는 항상 waiting_for_call로 유지되므로 별도 처리 불필요
        # if consultation.counselor_id:
        #     counselor = db.query(Counselor).filter(Counselor.id == consultation.counselor_id).first()
        #     if counselor and counselor.status == CounselorStatus.busy:
        #         counselor.status = CounselorStatus.waiting_for_call
        #         counselor.last_active_at = func.now()
        
        db.commit()
        db.refresh(consultation)
        
        return ConsultationEndResponse(
            consultation_code=consultation.consultation_code,
            status=consultation.status,
            completed_at=consultation.completed_at,
            message="상담이 정상적으로 종료되었습니다"
        )
    
    @staticmethod
    def cancel_consultation(
        db: Session,
        consultation_code: str
    ) -> Dict[str, Any]:
        """
        상담 취소 (매칭 대기 중 사용자가 나가는 경우)
        
        사용자 요구사항에 따라 단순히 DB에서 데이터만 삭제
        - 상담사들 알림은 수락 시 어차피 없는 것으로 표시되므로 별도 처리 불필요
        - 상담 데이터와 관련 요청만 삭제
        
        Args:
            db: 데이터베이스 세션
            consultation_code: 상담 코드
            
        Returns:
            dict: 취소 결과
        """
        # 상담 조회
        consultation = db.query(Consultation).filter(
            Consultation.consultation_code == consultation_code
        ).first()
        
        if not consultation:
            raise HTTPException(status_code=404, detail="상담을 찾을 수 없습니다")
        
        # 대기 중인 상담만 취소 가능
        if consultation.status != ConsultationStatus.waiting:
            raise HTTPException(
                status_code=400, 
                detail=f"현재 상태({consultation.status})에서는 취소할 수 없습니다. 대기 중인 상담만 취소 가능합니다."
            )
        
        consultation_id = consultation.id
        
        # 관련된 모든 상담 요청 삭제
        deleted_requests = db.query(ConsultationRequest).filter(
            ConsultationRequest.consultation_id == consultation_id
        ).delete(synchronize_session=False)
        
        # 상담 삭제
        db.delete(consultation)
        
        # 변경사항 커밋
        db.commit()
        
        logger.info(f"상담 취소 완료: 상담코드={consultation_code}, 삭제된 요청={deleted_requests}개")
        
        return {
            "message": "상담이 취소되었습니다",
            "consultation_code": consultation_code,
            "deleted_requests": deleted_requests
        }
    
    @staticmethod
    def start_reconsultation(
        db: Session,
        request: ReconsultationRequest
    ) -> ConsultationResponse:
        """
        이전 상담사와 재상담 시작 (상담 코드만으로 매칭)
        
        Args:
            db: 데이터베이스 세션
            request: 재상담 요청 정보
            
        Returns:
            ConsultationResponse: 생성된 상담 정보
        """
        # 이전 상담 확인
        previous_consultation = db.query(Consultation).filter(
            Consultation.consultation_code == request.previous_consultation_code
        ).first()
        
        if not previous_consultation:
            raise HTTPException(status_code=404, detail="이전 상담을 찾을 수 없습니다")
        
        # 이전 상담에 상담사가 배정되어 있는지 확인
        if not previous_consultation.counselor_id:
            raise HTTPException(status_code=400, detail="이전 상담에 배정된 상담사가 없습니다")
        
        # 상담사 상태 확인 (이전 상담의 상담사 정보 자동 사용)
        counselor = db.query(Counselor).filter(
            Counselor.id == previous_consultation.counselor_id,
            Counselor.is_active == True
        ).first()
        
        if not counselor:
            raise HTTPException(status_code=404, detail="이전 상담사를 찾을 수 없거나 비활성 상태입니다")
        
        if counselor.status != CounselorStatus.waiting_for_call:
            raise HTTPException(status_code=400, detail="상담사가 현재 상담 가능한 상태가 아닙니다")
        
        # 캐릭터 타입 정보 가져오기
        character_type = previous_consultation.character_type
        
        # 새로운 상담 코드 생성
        consultation_code = generate_consultation_code()
        
        # 상담 세션 생성
        consultation = Consultation(
            consultation_code=consultation_code,
            user_nickname=request.nickname,
            character_type_id=previous_consultation.character_type_id,
            character_name=previous_consultation.character_name,
            counselor_id=previous_consultation.counselor_id,  # 이전 상담의 상담사 ID 사용
            status=ConsultationStatus.waiting
        )
        
        db.add(consultation)
        db.flush()
        
        # 상담 요청 생성 (특정 상담사에게만)
        consultation_request = ConsultationRequest(
            consultation_id=consultation.id,
            counselor_id=previous_consultation.counselor_id,  # 이전 상담의 상담사 ID 사용
            status="pending"
        )
        
        db.add(consultation_request)
        db.commit()
        db.refresh(consultation)
        
        # WebSocket으로 특정 상담사에게만 알림 전송
        from services.consultation.websocket_manager import counselor_manager
        import asyncio
        
        async def send_notification():
            await counselor_manager.send_reconsultation_request(
                counselor_id=previous_consultation.counselor_id,  # 이전 상담의 상담사 ID 사용
                consultation_data={
                    "id": consultation.id,
                    "code": consultation.consultation_code,
                    "user_nickname": consultation.user_nickname,
                    "character_name": consultation.character_name,
                    "request_id": consultation_request.id,
                    "is_reconsultation": True,
                    "previous_consultation_code": request.previous_consultation_code
                }
            )
        
        # 비동기 작업 실행
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(send_notification())
            else:
                loop.run_until_complete(send_notification())
        except Exception as e:
            logger.error(f"재상담 알림 전송 중 오류: {e}")
        
        return ConsultationResponse(
            id=consultation.id,
            consultation_code=consultation.consultation_code,
            user_nickname=consultation.user_nickname,
            character_type_id=consultation.character_type_id,
            character_name=consultation.character_name,
            character_animal=character_type.animal,
            character_group=character_type.group_name,
            status=consultation.status,
            created_at=consultation.created_at,
            completed_at=consultation.completed_at,
            is_card_issued=consultation.is_card_issued
        )