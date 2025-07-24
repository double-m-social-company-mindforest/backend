"""
포스트맨 연결 상태에서 직접 알림 전송 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_consultation_and_check():
    """상담 생성하고 포스트맨에서 알림 확인"""
    
    logger.info("=== 상담 생성 테스트 ===")
    
    # 상담 생성 API 호출
    url = "http://localhost:8000/api/v1/consultations/start"
    
    payload = {
        "nickname": "포스트맨테스트",
        "character_type_preference": None,
        "quick_match": True
    }
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ 상담 생성 성공!")
            logger.info(f"  상담 코드: {data['consultation_code']}")
            logger.info(f"  상담 ID: {data['id']}")
            logger.info(f"  상태: {data['status']}")
            logger.info("\n📱 포스트맨에서 WebSocket 알림을 확인하세요!")
            logger.info("예상 알림 형태:")
            logger.info("""{
  "type": "consultation_request",
  "data": {
    "consultation_id": %d,
    "consultation_code": "%s",
    "user_nickname": "포스트맨테스트",
    "character_name": "...",
    "request_id": ...,
    "timestamp": "...",
    "timeout": 30
  }
}""" % (data['id'], data['consultation_code']))
            
        else:
            logger.error(f"❌ 상담 생성 실패: {response.status_code}")
            logger.error(f"응답: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ 요청 중 오류: {e}")


def check_recent_requests():
    """최근 상담 요청 확인"""
    logger.info("\n=== 최근 상담 요청 확인 ===")
    
    # 상담사 대시보드 API 호출 (임시로 인증 없이)
    url = "http://localhost:8000/api/v1/counselors/13/dashboard/requests"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"대기 중인 요청 수: {data['total_count']}")
            
            for req in data['requests'][:3]:  # 최근 3개만 표시
                logger.info(f"  요청 ID: {req['id']}")
                logger.info(f"    상담 코드: {req['consultation_code']}")
                logger.info(f"    사용자: {req['user_nickname']}")
                logger.info(f"    배정 상담사: {req['counselor_name']}")
                logger.info("    ---")
        else:
            logger.error(f"요청 조회 실패: {response.status_code}")
            
    except Exception as e:
        logger.error(f"요청 조회 중 오류: {e}")


if __name__ == "__main__":
    # 1. 기존 요청 확인
    check_recent_requests()
    
    # 2. 새 상담 생성
    create_consultation_and_check()
    
    logger.info("\n🔍 확인 사항:")
    logger.info("1. 포스트맨에서 WebSocket 연결이 유지되고 있는가?")
    logger.info("2. 상담 생성 후 포스트맨에 알림이 표시되는가?")
    logger.info("3. 알림이 안 오면 서버 로그에 오류 메시지가 있는가?")