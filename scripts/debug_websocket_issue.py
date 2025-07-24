"""
WebSocket 문제 디버깅 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.connection import SessionLocal
from services.consultation.websocket_manager import counselor_manager
from database.models import Counselor, CounselorStatus, Consultation, ConsultationRequest
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def debug_websocket_issue():
    """WebSocket 문제 디버깅"""
    db = SessionLocal()
    
    try:
        logger.info("=== WebSocket 문제 디버깅 ===")
        
        # 1. 상담사 상태 확인
        counselors = db.query(Counselor).all()
        logger.info(f"\n상담사 목록:")
        for c in counselors:
            logger.info(f"  ID: {c.id}, 이름: {c.name}, 상태: {c.status}")
        
        # 2. WebSocket 연결 상태
        logger.info(f"\nWebSocket 연결 상태:")
        logger.info(f"  연결된 상담사 수: {len(counselor_manager.counselor_connections)}")
        logger.info(f"  연결된 상담사 ID들: {list(counselor_manager.counselor_connections.keys())}")
        
        # 3. 최근 상담 요청 확인
        recent_requests = db.query(ConsultationRequest).order_by(
            ConsultationRequest.id.desc()
        ).limit(5).all()
        
        logger.info(f"\n최근 상담 요청 5개:")
        for req in recent_requests:
            consultation = db.query(Consultation).filter(
                Consultation.id == req.consultation_id
            ).first()
            logger.info(f"  요청 ID: {req.id}")
            logger.info(f"    상담사 ID: {req.counselor_id}")
            logger.info(f"    상담 코드: {consultation.consultation_code if consultation else 'N/A'}")
            logger.info(f"    상태: {req.status}")
            logger.info(f"    생성시간: {req.requested_at}")
            logger.info("    ---")
        
        # 4. 상담사 연결 상태별 확인
        counselor_13 = db.query(Counselor).filter(Counselor.id == 13).first()
        counselor_14 = db.query(Counselor).filter(Counselor.id == 14).first()
        
        if counselor_13:
            logger.info(f"\n상담사 13 (kimsangdam) 상태: {counselor_13.status}")
            is_connected_13 = counselor_manager.is_counselor_connected(13)
            logger.info(f"  WebSocket 연결: {is_connected_13}")
        
        if counselor_14:
            logger.info(f"\n상담사 14 (최성욱) 상태: {counselor_14.status}")
            is_connected_14 = counselor_manager.is_counselor_connected(14)
            logger.info(f"  WebSocket 연결: {is_connected_14}")
            
    except Exception as e:
        logger.error(f"디버깅 중 오류: {e}")
        raise
        
    finally:
        db.close()


async def test_both_counselors():
    """두 상담사 모두에게 테스트 알림 전송"""
    logger.info("\n=== 두 상담사 모두에게 테스트 알림 전송 ===")
    
    test_data = {
        "id": 999,
        "code": "TEST12345",
        "user_nickname": "테스트사용자",
        "character_name": "테스트캐릭터",
        "request_id": 888
    }
    
    # 상담사 13에게 전송
    success_13 = await counselor_manager.send_consultation_request(13, test_data)
    logger.info(f"상담사 13 알림 전송 결과: {success_13}")
    
    # 상담사 14에게 전송
    success_14 = await counselor_manager.send_consultation_request(14, test_data)
    logger.info(f"상담사 14 알림 전송 결과: {success_14}")


if __name__ == "__main__":
    debug_websocket_issue()
    
    # 비동기 테스트
    asyncio.run(test_both_counselors())