"""
새로운 상담 요청 조회 로직 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import Counselor, CounselorStatus
from services.counselor.request_service import RequestService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_request_logic():
    """새로운 요청 조회 로직 테스트"""
    db = SessionLocal()
    
    try:
        # 상담사 조회
        counselor = db.query(Counselor).filter(Counselor.username == "kimsangdam").first()
        
        if not counselor:
            logger.error("kimsangdam 상담사를 찾을 수 없습니다")
            return
        
        logger.info(f"상담사 정보: ID={counselor.id}, 상태={counselor.status}")
        
        # 상담 요청 조회 테스트
        try:
            response = RequestService.get_pending_requests(db, counselor.id)
            logger.info(f"조회된 요청 수: {response.total_count}")
            
            for req in response.requests:
                logger.info(f"요청 ID: {req.id}")
                logger.info(f"  상담 코드: {req.consultation_code}")
                logger.info(f"  사용자: {req.user_nickname}")
                logger.info(f"  배정된 상담사: {req.counselor_name} (ID: {req.counselor_id})")
                logger.info(f"  현재 조회자와 동일: {req.counselor_id == counselor.id}")
                logger.info("---")
                
        except Exception as e:
            logger.error(f"요청 조회 중 오류: {e}")
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        raise
        
    finally:
        db.close()


if __name__ == "__main__":
    test_request_logic()