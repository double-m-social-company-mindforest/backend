#!/usr/bin/env python3
import sys
sys.path.append('.')

from datetime import datetime
import pytz
from database.connection import SessionLocal
from database.models import Consultation
from sqlalchemy import text

def check_consultations_table():
    db = SessionLocal()
    
    print("=== consultations 테이블 최근 데이터 ===")
    
    # 최근 5개 상담 데이터 조회
    recent_consultations = db.query(Consultation).order_by(Consultation.created_at.desc()).limit(5).all()
    
    print(f"총 {len(recent_consultations)}개의 최근 상담 데이터:")
    print("-" * 80)
    
    for i, consultation in enumerate(recent_consultations, 1):
        print(f"{i}. 상담 코드: {consultation.consultation_code}")
        print(f"   상태: {consultation.status}")
        print(f"   생성 시간 (DB): {consultation.created_at}")
        print(f"   완료 시간 (DB): {consultation.completed_at}")
        
        # 시간대 정보
        if consultation.created_at:
            print(f"   생성 시간 tzinfo: {consultation.created_at.tzinfo}")
        if consultation.completed_at:
            print(f"   완료 시간 tzinfo: {consultation.completed_at.tzinfo}")
        
        print("-" * 40)
    
    # 현재 시간들과 비교
    print(f"\n=== 현재 시간 정보 ===")
    system_now = datetime.now()
    utc_now = datetime.utcnow()
    kst = pytz.timezone('Asia/Seoul')
    kst_now = datetime.now(kst)
    
    print(f"시스템 현재 시간: {system_now}")
    print(f"UTC 현재 시간: {utc_now}")
    print(f"KST 현재 시간: {kst_now}")
    
    # 데이터베이스 현재 시간
    db_now = db.execute(text("SELECT NOW()")).fetchone()[0]
    print(f"데이터베이스 현재 시간: {db_now}")
    
    db.close()

if __name__ == "__main__":
    check_consultations_table()