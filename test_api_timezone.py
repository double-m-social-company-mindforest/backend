#!/usr/bin/env python3
import sys
sys.path.append('.')

import requests
import json
from datetime import datetime
import pytz

def test_api_timezone():
    base_url = "http://localhost:8000"
    
    # 현재 한국 시간
    kst = pytz.timezone('Asia/Seoul')
    current_kst = datetime.now(kst)
    print(f"현재 한국 시간: {current_kst}")
    
    # 1. 상담 시작
    print("\n=== 상담 시작 테스트 ===")
    start_data = {
        "nickname": "시간테스트",
        "character_type_preference": 1,
        "quick_match": True
    }
    
    try:
        start_response = requests.post(f"{base_url}/api/v1/consultations/start", json=start_data)
        if start_response.status_code == 200:
            start_result = start_response.json()
            consultation_code = start_result["consultation_code"]
            print(f"상담 코드: {consultation_code}")
            print(f"생성 시간: {start_result['created_at']}")
            
            # created_at 파싱 및 시간 차이 계산
            created_str = start_result['created_at'].replace('Z', '+00:00')
            if '+09:00' in created_str:
                # 이미 KST
                created_time = datetime.fromisoformat(created_str)
                time_diff = (current_kst.replace(tzinfo=None) - created_time.replace(tzinfo=None)).total_seconds()
            else:
                # UTC로 간주
                created_time = datetime.fromisoformat(created_str)
                time_diff = (current_kst.replace(tzinfo=None) - created_time.replace(tzinfo=None)).total_seconds()
            
            print(f"시간 차이: {time_diff/3600:.1f}시간")
            
            # 2. 상담 종료
            print(f"\n=== 상담 종료 테스트 ({consultation_code}) ===")
            end_response = requests.post(f"{base_url}/api/v1/consultations/{consultation_code}/end")
            
            if end_response.status_code == 200:
                end_result = end_response.json()
                print(f"종료 시간: {end_result['completed_at']}")
                
                # completed_at 파싱 및 시간 차이 계산
                completed_str = end_result['completed_at'].replace('Z', '+00:00')
                if '+09:00' in completed_str:
                    # 이미 KST
                    completed_time = datetime.fromisoformat(completed_str)
                    time_diff = (current_kst.replace(tzinfo=None) - completed_time.replace(tzinfo=None)).total_seconds()
                else:
                    # UTC로 간주
                    completed_time = datetime.fromisoformat(completed_str)
                    time_diff = (current_kst.replace(tzinfo=None) - completed_time.replace(tzinfo=None)).total_seconds()
                
                print(f"시간 차이: {time_diff/3600:.1f}시간")
            else:
                print(f"종료 실패: {end_response.status_code}")
                print(end_response.text)
        else:
            print(f"시작 실패: {start_response.status_code}")
            print(start_response.text)
            
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    test_api_timezone()