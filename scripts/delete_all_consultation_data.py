"""
모든 상담 관련 데이터 삭제 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import Consultation, ConsultationRequest, Counselor, CounselorStatus
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def delete_all_consultation_data():
    """모든 상담 관련 데이터 삭제"""
    db = SessionLocal()
    
    try:
        # 1. 모든 상담 요청 삭제
        request_count = db.query(ConsultationRequest).count()
        db.query(ConsultationRequest).delete()
        logger.info(f"✅ 상담 요청 {request_count}개 삭제됨")
        
        # 2. 모든 상담 삭제
        consultation_count = db.query(Consultation).count()
        db.query(Consultation).delete()
        logger.info(f"✅ 상담 {consultation_count}개 삭제됨")
        
        # 3. 상담사 상태 확인 (이제 busy 상태가 없으므로 확인만)
        all_counselors = db.query(Counselor).all()
        logger.info(f"✅ {len(all_counselors)}명의 상담사가 있습니다 (busy 상태 로직 제거됨)")
        
        # 변경사항 커밋
        db.commit()
        
        logger.info("\n🔥 모든 상담 관련 데이터가 삭제되었습니다!")
        
        # 현재 상태 확인
        logger.info("\n=== 현재 데이터베이스 상태 ===")
        logger.info(f"남은 상담 수: {db.query(Consultation).count()}")
        logger.info(f"남은 상담 요청 수: {db.query(ConsultationRequest).count()}")
        
        counselors = db.query(Counselor).all()
        logger.info(f"\n상담사 상태:")
        for counselor in counselors:
            logger.info(f"  - {counselor.name}: {counselor.status}")
        
    except Exception as e:
        logger.error(f"데이터 삭제 중 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("=== 모든 상담 데이터 삭제 시작 ===\n")
    delete_all_consultation_data()