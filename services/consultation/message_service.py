from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from database.models import ConsultationMessage, Consultation, MessageType, SenderType
from datetime import datetime
import pytz
from schemas.consultation import MessageResponse, MessagesHistoryResponse


def convert_utc_to_kst(utc_time):
    """UTC 시간을 한국 시간으로 변환"""
    if utc_time is None:
        return None
    
    if utc_time.tzinfo is None:
        # naive datetime을 UTC로 간주
        utc_time = utc_time.replace(tzinfo=pytz.UTC)
    
    kst = pytz.timezone('Asia/Seoul')
    return utc_time.astimezone(kst)


class MessageService:
    @staticmethod
    def create_message(
        db: Session,
        consultation_id: int,
        sender_type: SenderType,
        message: str,
        message_type: MessageType = MessageType.text
    ) -> ConsultationMessage:
        """
        새 메시지 생성 및 저장
        
        Args:
            db: 데이터베이스 세션
            consultation_id: 상담 ID
            sender_type: 발신자 유형 (user/character)
            message: 메시지 내용
            message_type: 메시지 유형 (text/system/image)
            
        Returns:
            ConsultationMessage: 생성된 메시지
        """
        kst = pytz.timezone('Asia/Seoul')
        new_message = ConsultationMessage(
            consultation_id=consultation_id,
            sender_type=sender_type,
            message=message,
            message_type=message_type,
            timestamp=datetime.now(kst)  # 한국 시간으로 저장
        )
        
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        return new_message
    
    @staticmethod
    def get_messages_history(
        db: Session,
        consultation_code: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> MessagesHistoryResponse:
        """
        상담 메시지 히스토리 조회
        
        Args:
            db: 데이터베이스 세션
            consultation_code: 상담 코드
            limit: 조회할 메시지 수 제한
            offset: 오프셋
            
        Returns:
            MessagesHistoryResponse: 메시지 히스토리
        """
        # 상담 조회
        consultation = db.query(Consultation).filter(
            Consultation.consultation_code == consultation_code
        ).first()
        
        if not consultation:
            return MessagesHistoryResponse(
                consultation_code=consultation_code,
                messages=[],
                total_count=0
            )
        
        # 메시지 쿼리
        query = db.query(ConsultationMessage).filter(
            ConsultationMessage.consultation_id == consultation.id
        ).order_by(ConsultationMessage.timestamp)
        
        # 전체 카운트
        total_count = query.count()
        
        # 페이지네이션 적용
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        messages = query.all()
        
        # 응답 변환
        message_responses = [
            MessageResponse(
                id=msg.id,
                consultation_id=msg.consultation_id,
                sender_type=msg.sender_type,
                message=msg.message,
                timestamp=convert_utc_to_kst(msg.timestamp),
                message_type=msg.message_type
            )
            for msg in messages
        ]
        
        return MessagesHistoryResponse(
            consultation_code=consultation_code,
            messages=message_responses,
            total_count=total_count
        )
    
    @staticmethod
    def create_system_message(
        db: Session,
        consultation_id: int,
        message: str
    ) -> ConsultationMessage:
        """
        시스템 메시지 생성
        
        Args:
            db: 데이터베이스 세션
            consultation_id: 상담 ID
            message: 시스템 메시지 내용
            
        Returns:
            ConsultationMessage: 생성된 시스템 메시지
        """
        return MessageService.create_message(
            db=db,
            consultation_id=consultation_id,
            sender_type=SenderType.counselor,
            message=message,
            message_type=MessageType.system
        )