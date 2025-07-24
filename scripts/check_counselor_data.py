"""
상담사 및 상담 요청 데이터 확인 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import Counselor, Consultation, ConsultationRequest, CounselorStatus
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_counselor_data():
    """상담사 및 관련 데이터 확인"""
    db = SessionLocal()
    
    try:
        # kimsangdam 상담사 정보 확인
        counselor = db.query(Counselor).filter(
            Counselor.username == "kimsangdam"
        ).first()
        
        if counselor:
            logger.info(f"\n=== 상담사 정보 ===")
            logger.info(f"ID: {counselor.id}")
            logger.info(f"이름: {counselor.name}")
            logger.info(f"Username: {counselor.username}")
            logger.info(f"상태: {counselor.status}")
            logger.info(f"활성화: {counselor.is_active}")
            logger.info(f"승인됨: {counselor.is_approved}")
            logger.info(f"최대 동시 상담 수: {counselor.max_concurrent_sessions}")
            
            # 해당 상담사의 상담 요청 확인
            requests = db.query(ConsultationRequest).filter(
                ConsultationRequest.counselor_id == counselor.id
            ).all()
            
            logger.info(f"\n=== 상담 요청 ({len(requests)}개) ===")
            for req in requests:
                consultation = db.query(Consultation).filter(
                    Consultation.id == req.consultation_id
                ).first()
                logger.info(f"요청 ID: {req.id}, 상태: {req.status}, 상담 코드: {consultation.consultation_code if consultation else 'N/A'}")
            
            # 대기 중인 상담 요청만 확인
            pending_requests = db.query(ConsultationRequest).filter(
                ConsultationRequest.counselor_id == counselor.id,
                ConsultationRequest.status == "pending"
            ).all()
            
            logger.info(f"\n=== 대기 중인 요청 ({len(pending_requests)}개) ===")
            for req in pending_requests:
                consultation = db.query(Consultation).filter(
                    Consultation.id == req.consultation_id
                ).first()
                if consultation:
                    logger.info(f"요청 ID: {req.id}")
                    logger.info(f"상담 ID: {consultation.id}")
                    logger.info(f"상담 코드: {consultation.consultation_code}")
                    logger.info(f"사용자: {consultation.user_nickname}")
                    logger.info(f"요청 시간: {req.requested_at}")
                    logger.info("---")
        else:
            logger.error("kimsangdam 상담사를 찾을 수 없습니다.")
        
        # 전체 상담사 상태 확인
        all_counselors = db.query(Counselor).all()
        logger.info(f"\n=== 전체 상담사 현황 ===")
        for c in all_counselors:
            logger.info(f"{c.username}: 상태={c.status}, 활성화={c.is_active}, 승인={c.is_approved}")
        
        # 전체 상담 현황
        all_consultations = db.query(Consultation).all()
        logger.info(f"\n=== 전체 상담 현황 ({len(all_consultations)}개) ===")
        for con in all_consultations:
            logger.info(f"상담 ID: {con.id}, 코드: {con.consultation_code}, 상태: {con.status}, 상담사 ID: {con.counselor_id}")
        
        # waiting 상태인 상담만 따로 확인
        waiting_consultations = db.query(Consultation).filter(
            Consultation.status == "waiting"
        ).all()
        logger.info(f"\n=== Waiting 상태 상담 ({len(waiting_consultations)}개) ===")
        for con in waiting_consultations:
            logger.info(f"상담 ID: {con.id}, 코드: {con.consultation_code}, 생성시간: {con.created_at}")
            # 이 상담에 대한 요청이 있는지 확인
            related_requests = db.query(ConsultationRequest).filter(
                ConsultationRequest.consultation_id == con.id
            ).all()
            if related_requests:
                for req in related_requests:
                    logger.info(f"  -> 요청 ID: {req.id}, 상담사 ID: {req.counselor_id}, 상태: {req.status}")
            else:
                logger.info(f"  -> 이 상담에 대한 요청이 없습니다!")
        
        # 전체 상담 요청 현황
        all_requests = db.query(ConsultationRequest).all()
        logger.info(f"\n=== 전체 상담 요청 현황 ({len(all_requests)}개) ===")
        for req in all_requests:
            logger.info(f"요청 ID: {req.id}, 상담 ID: {req.consultation_id}, 상담사 ID: {req.counselor_id}, 상태: {req.status}")
            
    except Exception as e:
        logger.error(f"데이터 확인 중 오류 발생: {e}")
        raise
        
    finally:
        db.close()


if __name__ == "__main__":
    check_counselor_data()