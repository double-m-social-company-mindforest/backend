"""
상담 전체 플로우 테스트 및 문제점 진단 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import Counselor, Consultation, ConsultationRequest, CounselorStatus, ConsultationStatus
from services.counselor.matching_service import MatchingService
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def diagnose_matching_issue():
    """매칭 문제 진단"""
    db = SessionLocal()
    
    try:
        logger.info("=== 상담 매칭 문제 진단 시작 ===")
        
        # 1. 상담사 상태 확인
        logger.info("\n1. 상담사 상태 확인")
        counselors = db.query(Counselor).all()
        for c in counselors:
            logger.info(f"  - {c.username} (ID: {c.id})")
            logger.info(f"    is_active: {c.is_active}")
            logger.info(f"    is_approved: {c.is_approved}")
            logger.info(f"    status: {c.status}")
            logger.info(f"    max_concurrent_sessions: {c.max_concurrent_sessions}")
            
            # 현재 활성 상담 수 확인
            active_consultations = db.query(Consultation).filter(
                Consultation.counselor_id == c.id,
                Consultation.status.in_([ConsultationStatus.waiting, ConsultationStatus.active])
            ).count()
            logger.info(f"    현재 활성 상담 수: {active_consultations}")
        
        # 2. _find_available_counselor 테스트
        logger.info("\n2. _find_available_counselor 메서드 테스트")
        available = MatchingService._find_available_counselor(db)
        if available:
            logger.info(f"  사용 가능한 상담사 찾음: {available.name} (ID: {available.id})")
        else:
            logger.info("  사용 가능한 상담사 없음!")
            
            # 상세 진단
            logger.info("\n  상세 진단:")
            
            # 활성화된 상담사
            active_counselors = db.query(Counselor).filter(
                Counselor.is_active == True
            ).all()
            logger.info(f"  - 활성화된 상담사: {len(active_counselors)}명")
            
            # 승인된 상담사
            approved_counselors = db.query(Counselor).filter(
                Counselor.is_active == True,
                Counselor.is_approved == True
            ).all()
            logger.info(f"  - 활성화되고 승인된 상담사: {len(approved_counselors)}명")
            
            # 콜대기 상태 상담사
            waiting_counselors = db.query(Counselor).filter(
                Counselor.is_active == True,
                Counselor.is_approved == True,
                Counselor.status == CounselorStatus.waiting_for_call
            ).all()
            logger.info(f"  - 콜대기 상태 상담사: {len(waiting_counselors)}명")
        
        # 3. 대기 중인 상담 확인
        logger.info("\n3. 대기 중인 상담 확인")
        waiting_consultations = db.query(Consultation).filter(
            Consultation.status == ConsultationStatus.waiting
        ).all()
        
        logger.info(f"  대기 중인 상담: {len(waiting_consultations)}개")
        for con in waiting_consultations:
            logger.info(f"  - 상담 {con.consultation_code}")
            
            # 관련 요청 확인
            requests = db.query(ConsultationRequest).filter(
                ConsultationRequest.consultation_id == con.id
            ).all()
            
            if requests:
                logger.info(f"    요청 {len(requests)}개 있음")
                for req in requests:
                    logger.info(f"    - 요청 ID: {req.id}, 상담사: {req.counselor_id}, 상태: {req.status}")
            else:
                logger.info("    요청 없음 ❌")
        
        # 4. 상담 종료 후 상담사 상태 확인
        logger.info("\n4. 완료된 상담의 상담사 상태 확인")
        completed_consultations = db.query(Consultation).filter(
            Consultation.status == ConsultationStatus.completed,
            Consultation.counselor_id.isnot(None)
        ).all()
        
        for con in completed_consultations:
            counselor = db.query(Counselor).filter(Counselor.id == con.counselor_id).first()
            if counselor:
                logger.info(f"  - 상담 {con.consultation_code} 완료 후 상담사 {counselor.username} 상태: {counselor.status}")
        
        logger.info("\n=== 진단 완료 ===")
        
    except Exception as e:
        logger.error(f"진단 중 오류 발생: {e}")
        raise
        
    finally:
        db.close()


if __name__ == "__main__":
    diagnose_matching_issue()