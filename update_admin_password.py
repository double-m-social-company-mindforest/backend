#!/usr/bin/env python
"""관리자 비밀번호 업데이트 스크립트"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from database.connection import SessionLocal
from database.models import Admin
from core.security import get_password_hash

load_dotenv()


def update_admin_password():
    """admin 계정의 비밀번호를 admin123!로 업데이트"""
    db = SessionLocal()
    try:
        # admin 계정 조회
        admin = db.query(Admin).filter(Admin.username == "admin").first()
        
        if not admin:
            print("관리자 계정 'admin'을 찾을 수 없습니다.")
            print("새로운 관리자 계정을 생성합니다...")
            
            # 새 관리자 계정 생성
            new_admin = Admin(
                username="admin",
                password_hash=get_password_hash("admin123!"),
                name="시스템 관리자",
                email="admin@mindforest.com",
                role="super_admin",
                is_active=True
            )
            db.add(new_admin)
            db.commit()
            print("✅ 관리자 계정이 생성되었습니다.")
            print("   - 아이디: admin")
            print("   - 비밀번호: admin123!")
        else:
            # 비밀번호 업데이트
            admin.password_hash = get_password_hash("admin123!")
            db.commit()
            print("✅ 관리자 비밀번호가 업데이트되었습니다.")
            print("   - 아이디: admin")
            print("   - 비밀번호: admin123!")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    update_admin_password()