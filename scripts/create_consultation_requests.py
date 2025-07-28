"""
대기 중인 상담에 대해 상담 요청 생성하는 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import Counselor, Consultation, ConsultationRequest, ConsultationStatus, CounselorStatus
from datetime import datetime
import pytz
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_requests_for_waiting_consultations():
    """대기 중인 상담에 대해 상담 요청 생성"""
    db = SessionLocal()
    
    try:
        # 대기 중인 상담 조회
        waiting_consultations = db.query(Consultation).filter(
            Consultation.status == ConsultationStatus.waiting,
            Consultation.counselor_id.is_(None)
        ).all()
        
        logger.info(f"대기 중인 상담 {len(waiting_consultations)}개 발견")
        
        # 사용 가능한 상담사 확인
        available_counselor = db.query(Counselor).filter(
            Counselor.is_active == True,
            Counselor.is_approved == True,
            Counselor.status == CounselorStatus.waiting_for_call
        ).first()
        
        if not available_counselor:
            logger.error("사용 가능한 상담사가 없습니다")
            return
        
        logger.info(f"사용 가능한 상담사: {available_counselor.name} (ID: {available_counselor.id})")
        
        # 각 대기 중인 상담에 대해 요청 생성
        for consultation in waiting_consultations:
            # 이미 요청이 있는지 확인
            existing_request = db.query(ConsultationRequest).filter(
                ConsultationRequest.consultation_id == consultation.id
            ).first()
            
            if existing_request:
                logger.info(f"상담 {consultation.consultation_code}에 이미 요청이 존재함")
                continue
            
            # 새 요청 생성
            kst = pytz.timezone('Asia/Seoul')
            new_request = ConsultationRequest(
                consultation_id=consultation.id,
                counselor_id=available_counselor.id,
                status="pending",
                requested_at=datetime.now(kst)  # 한국 시간으로 명시적 설정
            )
            
            db.add(new_request)
            logger.info(f"상담 {consultation.consultation_code}에 대한 요청 생성")
        
        db.commit()
        logger.info("모든 요청 생성 완료")
        
    except Exception as e:
        db.rollback()
        logger.error(f"요청 생성 중 오류 발생: {e}")
        raise
        
    finally:
        db.close()


if __name__ == "__main__":
    response = input("대기 중인 상담에 대해 상담 요청을 생성하시겠습니까? (yes/no): ")
    if response.lower() == "yes":
        create_requests_for_waiting_consultations()
    else:
        logger.info("작업이 취소되었습니다.")