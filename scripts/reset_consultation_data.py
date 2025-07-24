"""
상담 관련 데이터 초기화 스크립트
주의: 이 스크립트는 모든 상담 관련 데이터를 삭제합니다!
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import (
    Consultation,
    ConsultationMessage,
    ConsultationCard,
    ConsultationRequest
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reset_consultation_data():
    """상담 관련 모든 데이터 삭제"""
    db = SessionLocal()
    
    try:
        # 삭제 순서: 외래 키 제약 조건을 고려하여 자식 테이블부터 삭제
        
        # 1. 상담 카드 삭제
        deleted_cards = db.query(ConsultationCard).delete()
        logger.info(f"상담 카드 {deleted_cards}개 삭제됨")
        
        # 2. 상담 메시지 삭제
        deleted_messages = db.query(ConsultationMessage).delete()
        logger.info(f"상담 메시지 {deleted_messages}개 삭제됨")
        
        # 3. 상담 요청 삭제
        deleted_requests = db.query(ConsultationRequest).delete()
        logger.info(f"상담 요청 {deleted_requests}개 삭제됨")
        
        # 4. 상담 삭제
        deleted_consultations = db.query(Consultation).delete()
        logger.info(f"상담 {deleted_consultations}개 삭제됨")
        
        # 변경사항 커밋
        db.commit()
        logger.info("모든 상담 관련 데이터가 성공적으로 초기화되었습니다.")
        
        # 삭제 후 상태 확인
        consultation_count = db.query(Consultation).count()
        message_count = db.query(ConsultationMessage).count()
        card_count = db.query(ConsultationCard).count()
        request_count = db.query(ConsultationRequest).count()
        
        logger.info(f"\n=== 초기화 후 데이터 개수 ===")
        logger.info(f"상담: {consultation_count}")
        logger.info(f"메시지: {message_count}")
        logger.info(f"카드: {card_count}")
        logger.info(f"요청: {request_count}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"데이터 초기화 중 오류 발생: {e}")
        raise
        
    finally:
        db.close()


if __name__ == "__main__":
    response = input("정말로 모든 상담 데이터를 삭제하시겠습니까? (yes/no): ")
    if response.lower() == "yes":
        reset_consultation_data()
    else:
        logger.info("데이터 초기화가 취소되었습니다.")