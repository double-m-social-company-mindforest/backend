"""
상담사 데이터 초기화 스크립트
주의: 이 스크립트는 모든 상담사 데이터를 삭제합니다!
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import Counselor, RefreshToken
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reset_counselor_data():
    """상담사 관련 모든 데이터 삭제"""
    db = SessionLocal()
    
    try:
        # 1. RefreshToken 삭제 (외래 키 제약 때문에 먼저 삭제)
        deleted_tokens = db.query(RefreshToken).delete()
        logger.info(f"리프레시 토큰 {deleted_tokens}개 삭제됨")
        
        # 2. 상담사 데이터 삭제
        deleted_counselors = db.query(Counselor).delete()
        logger.info(f"상담사 {deleted_counselors}명 삭제됨")
        
        # 변경사항 커밋
        db.commit()
        logger.info("모든 상담사 데이터가 성공적으로 초기화되었습니다.")
        
        # 삭제 후 상태 확인
        counselor_count = db.query(Counselor).count()
        token_count = db.query(RefreshToken).count()
        logger.info(f"\n=== 초기화 후 데이터 개수 ===")
        logger.info(f"상담사: {counselor_count}")
        logger.info(f"리프레시 토큰: {token_count}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"데이터 초기화 중 오류 발생: {e}")
        raise
        
    finally:
        db.close()


if __name__ == "__main__":
    response = input("정말로 모든 상담사 데이터를 삭제하시겠습니까? (yes/no): ")
    if response.lower() == "yes":
        reset_counselor_data()
    else:
        logger.info("데이터 초기화가 취소되었습니다.")