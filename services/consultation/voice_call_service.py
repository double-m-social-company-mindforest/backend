from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
import pytz
from database.models import Consultation, ConsultationStatus
from services.consultation.websocket_manager import manager
import logging
import json

logger = logging.getLogger(__name__)

class VoiceCallService:
    """음성 통화 관리 서비스 (WebRTC 지원)"""
    
    # WebRTC 연결 상태 저장 (메모리 기반 - 실제 운영에서는 Redis 권장)
    _webrtc_sessions: Dict[str, Dict[str, Any]] = {}
    
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
            kst = pytz.timezone('Asia/Seoul')
            consultation.voice_call_started_at = datetime.now(kst)
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
            kst = pytz.timezone('Asia/Seoul')
            consultation.voice_call_ended_at = datetime.now(kst)
            
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
                    kst = pytz.timezone('Asia/Seoul')
                    now = datetime.now(kst)
                    start_time = consultation.voice_call_started_at
                    if start_time.tzinfo is None:
                        start_time = start_time.replace(tzinfo=kst)
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
    
    @staticmethod
    def create_webrtc_session(consultation_code: str) -> Dict[str, Any]:
        """
        WebRTC 세션 생성
        
        Args:
            consultation_code: 상담 코드
            
        Returns:
            Dict: WebRTC 세션 정보
        """
        session_data = {
            "consultation_code": consultation_code,
            "created_at": datetime.utcnow().isoformat(),
            "participants": {},  # user_type -> 연결 상태
            "ice_candidates": {
                "user": [],
                "counselor": []
            },
            "offers": {},
            "answers": {},
            "status": "initializing"  # initializing, connecting, connected, disconnected
        }
        
        VoiceCallService._webrtc_sessions[consultation_code] = session_data
        logger.info(f"WebRTC 세션 생성: {consultation_code}")
        
        return session_data
    
    @staticmethod
    def get_webrtc_session(consultation_code: str) -> Optional[Dict[str, Any]]:
        """
        WebRTC 세션 조회
        
        Args:
            consultation_code: 상담 코드
            
        Returns:
            Dict: WebRTC 세션 정보
        """
        return VoiceCallService._webrtc_sessions.get(consultation_code)
    
    @staticmethod
    def add_webrtc_participant(consultation_code: str, user_type: str) -> bool:
        """
        WebRTC 세션에 참가자 추가
        
        Args:
            consultation_code: 상담 코드
            user_type: 사용자 타입
            
        Returns:
            bool: 추가 성공 여부
        """
        try:
            session = VoiceCallService.get_webrtc_session(consultation_code)
            if not session:
                session = VoiceCallService.create_webrtc_session(consultation_code)
            
            session["participants"][user_type] = {
                "joined_at": datetime.utcnow().isoformat(),
                "status": "joined"
            }
            
            logger.info(f"WebRTC 참가자 추가: {consultation_code}, {user_type}")
            return True
            
        except Exception as e:
            logger.error(f"WebRTC 참가자 추가 실패: {e}")
            return False
    
    @staticmethod
    def store_webrtc_offer(consultation_code: str, user_type: str, offer: Dict) -> bool:
        """
        WebRTC Offer 저장
        
        Args:
            consultation_code: 상담 코드
            user_type: 발신자 타입
            offer: WebRTC Offer 데이터
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            session = VoiceCallService.get_webrtc_session(consultation_code)
            if not session:
                session = VoiceCallService.create_webrtc_session(consultation_code)
            
            session["offers"][user_type] = {
                "offer": offer,
                "created_at": datetime.utcnow().isoformat()
            }
            session["status"] = "offer_created"
            
            logger.info(f"WebRTC Offer 저장: {consultation_code}, 발신자={user_type}")
            return True
            
        except Exception as e:
            logger.error(f"WebRTC Offer 저장 실패: {e}")
            return False
    
    @staticmethod
    def store_webrtc_answer(consultation_code: str, user_type: str, answer: Dict) -> bool:
        """
        WebRTC Answer 저장
        
        Args:
            consultation_code: 상담 코드
            user_type: 응답자 타입
            answer: WebRTC Answer 데이터
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            session = VoiceCallService.get_webrtc_session(consultation_code)
            if not session:
                logger.error(f"WebRTC 세션을 찾을 수 없음: {consultation_code}")
                return False
            
            session["answers"][user_type] = {
                "answer": answer,
                "created_at": datetime.utcnow().isoformat()
            }
            session["status"] = "answer_created"
            
            logger.info(f"WebRTC Answer 저장: {consultation_code}, 응답자={user_type}")
            return True
            
        except Exception as e:
            logger.error(f"WebRTC Answer 저장 실패: {e}")
            return False
    
    @staticmethod
    def add_ice_candidate(consultation_code: str, user_type: str, candidate: Dict) -> bool:
        """
        ICE Candidate 추가
        
        Args:
            consultation_code: 상담 코드
            user_type: 발신자 타입
            candidate: ICE Candidate 데이터
            
        Returns:
            bool: 추가 성공 여부
        """
        try:
            session = VoiceCallService.get_webrtc_session(consultation_code)
            if not session:
                session = VoiceCallService.create_webrtc_session(consultation_code)
            
            if user_type not in session["ice_candidates"]:
                session["ice_candidates"][user_type] = []
            
            session["ice_candidates"][user_type].append({
                "candidate": candidate,
                "created_at": datetime.utcnow().isoformat()
            })
            
            logger.debug(f"ICE Candidate 추가: {consultation_code}, {user_type}")
            return True
            
        except Exception as e:
            logger.error(f"ICE Candidate 추가 실패: {e}")
            return False
    
    @staticmethod
    def update_webrtc_status(consultation_code: str, status: str) -> bool:
        """
        WebRTC 연결 상태 업데이트
        
        Args:
            consultation_code: 상담 코드
            status: 연결 상태
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            session = VoiceCallService.get_webrtc_session(consultation_code)
            if not session:
                logger.error(f"WebRTC 세션을 찾을 수 없음: {consultation_code}")
                return False
            
            session["status"] = status
            session["updated_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"WebRTC 상태 업데이트: {consultation_code}, 상태={status}")
            return True
            
        except Exception as e:
            logger.error(f"WebRTC 상태 업데이트 실패: {e}")
            return False
    
    @staticmethod
    def cleanup_webrtc_session(consultation_code: str) -> bool:
        """
        WebRTC 세션 정리
        
        Args:
            consultation_code: 상담 코드
            
        Returns:
            bool: 정리 성공 여부
        """
        try:
            if consultation_code in VoiceCallService._webrtc_sessions:
                del VoiceCallService._webrtc_sessions[consultation_code]
                logger.info(f"WebRTC 세션 정리 완료: {consultation_code}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"WebRTC 세션 정리 실패: {e}")
            return False