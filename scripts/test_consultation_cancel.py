"""
상담 취소 기능 테스트 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_consultation_cancel():
    """상담 취소 시나리오 테스트"""
    
    # 1. 상담 시작
    logger.info("=== 1. 상담 시작 ===")
    start_url = "http://localhost:8000/api/v1/consultations/start"
    start_payload = {
        "nickname": "취소테스트사용자",
        "quick_match": True
    }
    
    response = requests.post(start_url, json=start_payload)
    if response.status_code != 200:
        logger.error(f"상담 시작 실패: {response.text}")
        return
    
    consultation_data = response.json()
    consultation_code = consultation_data["consultation_code"]
    logger.info(f"✅ 상담 생성됨: {consultation_code}")
    logger.info(f"   상태: {consultation_data['status']}")
    
    # 2. 대기 시간 시뮬레이션
    logger.info("\n=== 2. 사용자가 3초 후 취소 결정 ===")
    time.sleep(3)
    
    # 3. 상담 취소
    logger.info("\n=== 3. 상담 취소 요청 ===")
    cancel_url = f"http://localhost:8000/api/v1/consultations/{consultation_code}/cancel"
    
    response = requests.delete(cancel_url)
    if response.status_code == 200:
        cancel_data = response.json()
        logger.info(f"✅ 상담 취소 성공!")
        logger.info(f"   메시지: {cancel_data['message']}")
        logger.info(f"   삭제된 요청 수: {cancel_data['deleted_requests']}")
    else:
        logger.error(f"❌ 상담 취소 실패: {response.text}")
    
    # 4. 취소된 상담 조회 시도
    logger.info("\n=== 4. 취소된 상담 조회 시도 ===")
    get_url = f"http://localhost:8000/api/v1/consultations/{consultation_code}"
    
    response = requests.get(get_url)
    if response.status_code == 404:
        logger.info("✅ 예상대로 상담이 삭제되어 조회되지 않음")
    else:
        logger.error(f"❌ 예상치 않은 응답: {response.status_code} - {response.text}")


def test_cancel_active_consultation():
    """진행 중인 상담 취소 시도 (실패해야 함)"""
    
    logger.info("\n\n=== 진행 중인 상담 취소 테스트 ===")
    
    # 1. 상담 시작
    start_url = "http://localhost:8000/api/v1/consultations/start"
    start_payload = {
        "nickname": "활성상담테스트",
        "quick_match": True
    }
    
    response = requests.post(start_url, json=start_payload)
    if response.status_code != 200:
        logger.error(f"상담 시작 실패: {response.text}")
        return
    
    consultation_data = response.json()
    consultation_code = consultation_data["consultation_code"]
    logger.info(f"✅ 상담 생성됨: {consultation_code}")
    
    # 2. 상담 재연결로 active 상태로 변경
    reconnect_url = f"http://localhost:8000/api/v1/consultations/{consultation_code}/reconnect"
    reconnect_payload = {"nickname": "활성상담테스트"}
    
    response = requests.post(reconnect_url, json=reconnect_payload)
    if response.status_code == 200:
        logger.info("✅ 상담이 active 상태로 변경됨")
    
    # 3. active 상담 취소 시도
    logger.info("\n=== active 상담 취소 시도 ===")
    cancel_url = f"http://localhost:8000/api/v1/consultations/{consultation_code}/cancel"
    
    response = requests.delete(cancel_url)
    if response.status_code == 400:
        logger.info("✅ 예상대로 active 상담은 취소할 수 없음")
        logger.info(f"   에러 메시지: {response.json()['detail']}")
    else:
        logger.error(f"❌ 예상치 않은 응답: {response.status_code}")


if __name__ == "__main__":
    # 정상 취소 테스트
    test_consultation_cancel()
    
    # 진행 중인 상담 취소 시도 테스트
    test_cancel_active_consultation()
    
    logger.info("\n\n=== 테스트 완료 ===")