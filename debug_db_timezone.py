#!/usr/bin/env python3
import sys
sys.path.append('.')

from datetime import datetime
import pytz
from database.connection import SessionLocal
from database.models import Consultation
from sqlalchemy import text

def debug_db_timezone():
    db = SessionLocal()
    
    print("=== 데이터베이스 시간대 디버깅 ===")
    
    # 1. 데이터베이스 시간대 설정 확인
    db_timezone = db.execute(text("SHOW timezone")).fetchone()[0]
    db_now = db.execute(text("SELECT NOW()")).fetchone()[0]
    
    print(f"데이터베이스 시간대: {db_timezone}")
    print(f"데이터베이스 현재 시간: {db_now}")
    
    # 2. 시스템 시간들
    system_now = datetime.now()
    utc_now = datetime.utcnow()
    kst = pytz.timezone('Asia/Seoul')
    kst_now = datetime.now(kst)
    
    print(f"시스템 현재 시간: {system_now}")
    print(f"UTC 현재 시간: {utc_now}")
    print(f"KST 현재 시간: {kst_now}")
    
    # 3. 가장 최근 상담 확인
    latest_consultation = db.query(Consultation).order_by(Consultation.created_at.desc()).first()
    
    if latest_consultation:
        print(f"\n=== 최근 상담 데이터 ===")
        print(f"상담 코드: {latest_consultation.consultation_code}")
        print(f"DB에 저장된 생성 시간: {latest_consultation.created_at}")
        print(f"DB에 저장된 완료 시간: {latest_consultation.completed_at}")
        
        # 시간대 정보 확인
        if latest_consultation.created_at:
            print(f"생성 시간 tzinfo: {latest_consultation.created_at.tzinfo}")
        if latest_consultation.completed_at:
            print(f"완료 시간 tzinfo: {latest_consultation.completed_at.tzinfo}")
    
    # 4. 테스트: 한국 시간으로 직접 저장해보기
    print(f"\n=== 한국 시간 저장 테스트 ===")
    test_kst_time = datetime.now(kst)
    print(f"저장할 한국 시간: {test_kst_time}")
    
    # SQL로 직접 확인
    result = db.execute(
        text("SELECT :test_time::timestamp with time zone"),
        {"test_time": test_kst_time}
    ).fetchone()[0]
    print(f"DB에서 해석한 시간: {result}")
    
    db.close()

if __name__ == "__main__":
    debug_db_timezone()