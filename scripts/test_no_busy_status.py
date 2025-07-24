"""
busy 상태 제거 후 동작 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_multiple_consultations():
    """여러 상담을 연속으로 생성하여 상담사 상태가 busy로 변경되지 않는지 확인"""
    
    logger.info("=== 연속 상담 생성 테스트 ===")
    
    consultations = []
    
    # 여러 상담을 연속으로 생성
    for i in range(3):
        logger.info(f"\n--- {i+1}번째 상담 생성 ---")
        
        start_url = "http://localhost:8000/api/v1/consultations/start"
        start_payload = {
            "nickname": f"테스트사용자{i+1}",
            "quick_match": True
        }
        
        response = requests.post(start_url, json=start_payload)
        if response.status_code == 200:
            consultation_data = response.json()
            consultations.append(consultation_data["consultation_code"])
            logger.info(f"✅ 상담 생성됨: {consultation_data['consultation_code']}")
        else:
            logger.error(f"❌ 상담 생성 실패: {response.text}")
        
        time.sleep(1)  # 1초 간격
    
    # 상담사 요청 목록 확인
    logger.info(f"\n=== 상담사 요청 목록 확인 ===")
    requests_url = "http://localhost:8000/api/v1/counselors/1/dashboard/requests"
    
    response = requests.get(requests_url)
    if response.status_code == 200:
        data = response.json()
        logger.info(f"✅ 대기 중인 요청 수: {data['total_count']}")
        
        for req in data['requests']:
            logger.info(f"  - 요청 ID: {req['id']}, 상담코드: {req['consultation_code']}")
    
    # 첫 번째 상담 요청 수락
    if consultations:
        logger.info(f"\n=== 첫 번째 상담 수락 테스트 ===")
        
        # 첫 번째 요청 수락
        if response.status_code == 200 and data['requests']:
            first_request = data['requests'][0]
            accept_url = f"http://localhost:8000/api/v1/counselors/1/dashboard/requests/{first_request['id']}/accept"
            accept_payload = {"response_message": "수락합니다"}
            
            response = requests.post(accept_url, json=accept_payload)
            if response.status_code == 200:
                logger.info("✅ 첫 번째 상담 수락됨")
                
                # 수락 후 다시 요청 목록 확인
                response = requests.get(requests_url)
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ 수락 후 남은 요청 수: {data['total_count']}")
            else:
                logger.error(f"❌ 상담 수락 실패: {response.text}")
    
    logger.info(f"\n생성된 상담들: {consultations}")
    return consultations


if __name__ == "__main__":
    test_multiple_consultations()