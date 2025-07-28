#!/usr/bin/env python3
import sys
sys.path.append('.')

from datetime import datetime
import pytz
from database.connection import SessionLocal
from database.models import Consultation
from sqlalchemy.sql import func

def test_timezone():
    db = SessionLocal()
    
    print("=== 시간대 테스트 ===")
    
    # 현재 시간들
    now_system = datetime.now()
    now_utc = datetime.utcnow()
    kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(kst)
    
    print(f"시스템 시간: {now_system}")
    print(f"UTC 시간: {now_utc}")
    print(f"한국 시간 (pytz): {now_kst}")
    
    # 데이터베이스의 현재 시간 확인
    from sqlalchemy import text
    db_now = db.execute(text("SELECT NOW()")).fetchone()[0]
    print(f"데이터베이스 시간: {db_now}")
    
    # 가장 최근 상담 데이터 확인
    latest_consultation = db.query(Consultation).order_by(Consultation.created_at.desc()).first()
    
    if latest_consultation:
        print(f"\n=== 최근 상담 데이터 ===")
        print(f"상담 코드: {latest_consultation.consultation_code}")
        print(f"생성 시간: {latest_consultation.created_at}")
        print(f"완료 시간: {latest_consultation.completed_at}")
        
        # 시간대 정보 확인
        if latest_consultation.created_at.tzinfo:
            print(f"생성 시간 시간대: {latest_consultation.created_at.tzinfo}")
        else:
            print("생성 시간에 시간대 정보 없음")
            
        if latest_consultation.completed_at and latest_consultation.completed_at.tzinfo:
            print(f"완료 시간 시간대: {latest_consultation.completed_at.tzinfo}")
        elif latest_consultation.completed_at:
            print("완료 시간에 시간대 정보 없음")
    
    db.close()

if __name__ == "__main__":
    test_timezone()