from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models import Consultation, ConsultationStatus
from services.consultation.websocket_manager import manager
import logging

logger = logging.getLogger(__name__)

class VoiceCallService:
    """음성 통화 관리 서비스"""
    
    @staticmethod
    def start_voice_call(
        db: Session,
        consultation_code: str,
        initiator_type: str  # "user" 또는 "counselor"
    ) -> bool:
        """
        음성 통화 시작
        
        Args:
            db: 데이터베이스 세션
            consultation_code: 상담 코드
            initiator_type: 통화 시작 요청자 타입
            
        Returns:
            bool: 통화 시작 성공 여부
        """
        try:
            consultation = db.query(Consultation).filter(
                Consultation.consultation_code == consultation_code
            ).first()
            
            if not consultation:
                logger.error(f"상담을 찾을 수 없음: {consultation_code}")
                return False
            
            # 상담 상태 검증
            if consultation.status != ConsultationStatus.active:
                logger.error(f"활성 상담이 아님: {consultation_code}, 상태: {consultation.status}")
                return False
            
            # 이미 음성 통화 중인지 확인
            if consultation.voice_call_active:
                logger.warning(f"이미 음성 통화 중: {consultation_code}")
                return False
            
            # 음성 통화 시작
            consultation.voice_call_active = True
            consultation.voice_call_started_at = func.now()
            consultation.voice_call_ended_at = None
            
            db.commit()
            db.refresh(consultation)
            
            logger.info(f"음성 통화 시작: 상담={consultation_code}, 시작자={initiator_type}")
            return True
            
        except Exception as e:
            logger.error(f"음성 통화 시작 실패: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def end_voice_call(
        db: Session,
        consultation_code: str,
        terminator_type: str  # "user" 또는 "counselor"
    ) -> bool:
        """
        음성 통화 종료
        
        Args:
            db: 데이터베이스 세션
            consultation_code: 상담 코드
            terminator_type: 통화 종료 요청자 타입
            
        Returns:
            bool: 통화 종료 성공 여부
        """
        try:
            consultation = db.query(Consultation).filter(
                Consultation.consultation_code == consultation_code
            ).first()
            
            if not consultation:
                logger.error(f"상담을 찾을 수 없음: {consultation_code}")
                return False
            
            # 음성 통화 중인지 확인
            if not consultation.voice_call_active:
                logger.warning(f"음성 통화 중이 아님: {consultation_code}")
                return False
            
            # 음성 통화 종료
            consultation.voice_call_active = False
            consultation.voice_call_ended_at = func.now()
            
            db.commit()
            db.refresh(consultation)
            
            # 통화 시간 계산
            if consultation.voice_call_started_at:
                call_duration = consultation.voice_call_ended_at - consultation.voice_call_started_at
                logger.info(f"음성 통화 종료: 상담={consultation_code}, 종료자={terminator_type}, 통화시간={call_duration}")
            else:
                logger.info(f"음성 통화 종료: 상담={consultation_code}, 종료자={terminator_type}")
            
            return True
            
        except Exception as e:
            logger.error(f"음성 통화 종료 실패: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def get_voice_call_status(
        db: Session,
        consultation_code: str
    ) -> Optional[Dict[str, Any]]:
        """
        음성 통화 상태 조회
        
        Args:
            db: 데이터베이스 세션
            consultation_code: 상담 코드
            
        Returns:
            Dict: 음성 통화 상태 정보
        """
        try:
            consultation = db.query(Consultation).filter(
                Consultation.consultation_code == consultation_code
            ).first()
            
            if not consultation:
                return None
            
            status = {
                "active": consultation.voice_call_active,
                "started_at": consultation.voice_call_started_at.isoformat() if consultation.voice_call_started_at else None,
                "ended_at": consultation.voice_call_ended_at.isoformat() if consultation.voice_call_ended_at else None,
                "duration": None
            }
            
            # 통화 시간 계산
            if consultation.voice_call_started_at:
                if consultation.voice_call_active:
                    # 현재 진행 중인 통화
                    now = datetime.now(timezone.utc)
                    start_time = consultation.voice_call_started_at
                    if start_time.tzinfo is None:
                        start_time = start_time.replace(tzinfo=timezone.utc)
                    duration = now - start_time
                    status["duration"] = int(duration.total_seconds())
                elif consultation.voice_call_ended_at:
                    # 종료된 통화
                    start_time = consultation.voice_call_started_at
                    end_time = consultation.voice_call_ended_at
                    if start_time.tzinfo is None:
                        start_time = start_time.replace(tzinfo=timezone.utc)
                    if end_time.tzinfo is None:
                        end_time = end_time.replace(tzinfo=timezone.utc)
                    duration = end_time - start_time
                    status["duration"] = int(duration.total_seconds())
            
            return status
            
        except Exception as e:
            logger.error(f"음성 통화 상태 조회 실패: {e}")
            return None
    
    @staticmethod
    async def notify_voice_call_event(
        consultation_code: str,
        event_type: str,  # "start", "end", "request", "accept", "reject"
        initiator_type: str,
        additional_data: Optional[Dict] = None
    ):
        """
        음성 통화 이벤트 알림
        
        Args:
            consultation_code: 상담 코드
            event_type: 이벤트 타입
            initiator_type: 이벤트 발생자 타입
            additional_data: 추가 데이터
        """
        try:
            message_map = {
                "start": "음성 통화가 시작되었습니다.",
                "end": "음성 통화가 종료되었습니다.",
                "request": "음성 통화를 요청했습니다.",
                "accept": "음성 통화 요청을 수락했습니다.",
                "reject": "음성 통화 요청을 거절했습니다."
            }
            
            message = message_map.get(event_type, f"음성 통화 이벤트: {event_type}")
            
            # 이벤트 데이터 구성
            event_data = {
                "event_type": event_type,
                "initiator_type": initiator_type,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            if additional_data:
                event_data.update(additional_data)
            
            # WebSocket을 통해 알림 전송
            await manager.send_to_consultation(
                consultation_code=consultation_code,
                message=message,
                sender_type="system",
                message_type="voice_call_event",
                voice_data={"event": event_data}
            )
            
            logger.info(f"음성 통화 이벤트 알림 전송: 상담={consultation_code}, 이벤트={event_type}")
            
        except Exception as e:
            logger.error(f"음성 통화 이벤트 알림 실패: {e}")
    
    @staticmethod
    def is_voice_call_available(
        db: Session,
        consultation_code: str
    ) -> bool:
        """
        음성 통화 가능 여부 확인
        
        Args:
            db: 데이터베이스 세션
            consultation_code: 상담 코드
            
        Returns:
            bool: 음성 통화 가능 여부
        """
        try:
            consultation = db.query(Consultation).filter(
                Consultation.consultation_code == consultation_code
            ).first()
            
            if not consultation:
                return False
            
            # 상담이 활성 상태이고, 상담사가 배정되어 있으며, 음성 통화 중이 아닌 경우
            return (
                consultation.status == ConsultationStatus.active and
                consultation.counselor_id is not None and
                not consultation.voice_call_active
            )
            
        except Exception as e:
            logger.error(f"음성 통화 가능 여부 확인 실패: {e}")
            return False