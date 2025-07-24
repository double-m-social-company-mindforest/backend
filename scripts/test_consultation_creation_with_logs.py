"""
상담 생성 시 알림 전송 과정을 자세히 로깅하는 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.connection import SessionLocal
from schemas.consultation import ConsultationStartRequest
from services.consultation.consultation_service import ConsultationService
from services.consultation.websocket_manager import counselor_manager
import logging
import asyncio

# 상세 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 매칭 서비스 로거도 DEBUG로 설정
matching_logger = logging.getLogger('services.counselor.matching_service')
matching_logger.setLevel(logging.DEBUG)


def test_consultation_creation():
    """상담 생성 테스트 with 자세한 로깅"""
    db = SessionLocal()
    
    try:
        logger.info("=== 상담 생성 테스트 시작 ===")
        
        # 1. WebSocket 연결 상태 확인
        connected_counselors = list(counselor_manager.counselor_connections.keys())
        logger.info(f"현재 연결된 상담사들: {connected_counselors}")
        
        if not connected_counselors:
            logger.warning("⚠️ 연결된 상담사가 없습니다!")
        
        # 2. 상담 요청 생성
        request = ConsultationStartRequest(
            nickname="테스트유저",
            character_type_preference=None,
            quick_match=True
        )
        
        logger.info("상담 시작 요청 생성...")
        
        # 3. 상담 서비스 호출
        response = ConsultationService.start_consultation(db, request)
        
        logger.info(f"✅ 상담 생성 완료:")
        logger.info(f"  - 상담 코드: {response.consultation_code}")
        logger.info(f"  - 상담 ID: {response.id}")
        logger.info(f"  - 상태: {response.status}")
        
        # 4. 생성된 상담에 대한 요청 확인
        from database.models import ConsultationRequest
        consultation_requests = db.query(ConsultationRequest).filter(
            ConsultationRequest.consultation_id == response.id
        ).all()
        
        logger.info(f"생성된 상담 요청 수: {len(consultation_requests)}")
        for req in consultation_requests:
            logger.info(f"  - 요청 ID: {req.id}, 상담사 ID: {req.counselor_id}, 상태: {req.status}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ 상담 생성 중 오류: {e}")
        raise
        
    finally:
        db.close()


async def test_manual_notification():
    """수동 알림 전송 테스트"""
    logger.info("\n=== 수동 알림 전송 테스트 ===")
    
    counselor_id = 13
    test_data = {
        "id": 999,
        "code": "MANUAL123",
        "user_nickname": "수동테스트",
        "character_name": "테스트캐릭터",
        "request_id": 777
    }
    
    success = await counselor_manager.send_consultation_request(counselor_id, test_data)
    logger.info(f"수동 알림 전송 결과: {success}")
    
    return success


if __name__ == "__main__":
    # 1. 상담 생성 테스트
    consultation = test_consultation_creation()
    
    # 2. 수동 알림 테스트
    print("\n" + "="*50)
    result = asyncio.run(test_manual_notification())