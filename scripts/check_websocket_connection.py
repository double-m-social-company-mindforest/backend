"""
WebSocket 연결 상태 및 알림 전송 확인 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.connection import SessionLocal
from services.consultation.websocket_manager import counselor_manager
print(f"counselor_manager 인스턴스 ID: {id(counselor_manager)}")
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_websocket_connections():
    """WebSocket 연결 상태 확인"""
    try:
        counselor_id = 13
        
        # 상담사 연결 상태 확인
        is_connected = counselor_manager.is_counselor_connected(counselor_id)
        logger.info(f"상담사 ID {counselor_id} WebSocket 연결 상태: {is_connected}")
        
        # 현재 연결된 상담사들 확인
        connected_counselors = list(counselor_manager.counselor_connections.keys())
        logger.info(f"현재 연결된 상담사들: {connected_counselors}")
        
        # 연결 매핑 정보
        logger.info(f"전체 연결 수: {len(counselor_manager.counselor_connections)}")
        for cid, ws in counselor_manager.counselor_connections.items():
            logger.info(f"  상담사 {cid}: {ws}")
        
        return is_connected
        
    except Exception as e:
        logger.error(f"WebSocket 연결 확인 중 오류: {e}")
        return False


async def test_send_notification():
    """테스트 알림 전송"""
    try:
        counselor_id = 13
        test_data = {
            "id": 999,
            "code": "TEST12345",
            "user_nickname": "테스트사용자",
            "character_name": "테스트캐릭터",
            "request_id": 888
        }
        
        success = await counselor_manager.send_consultation_request(counselor_id, test_data)
        logger.info(f"테스트 알림 전송 결과: {success}")
        
        return success
        
    except Exception as e:
        logger.error(f"테스트 알림 전송 중 오류: {e}")
        return False


if __name__ == "__main__":
    check_websocket_connections()
    
    # 테스트 알림 전송은 비동기 함수이므로 별도로 실행 필요
    import asyncio
    print("\n=== 테스트 알림 전송 ===")
    result = asyncio.run(test_send_notification())