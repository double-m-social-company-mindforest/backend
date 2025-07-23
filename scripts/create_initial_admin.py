#!/usr/bin/env python3
"""
초기 관리자 계정 생성 스크립트

사용법:
    python scripts/create_initial_admin.py

환경 변수:
    ADMIN_USERNAME: 관리자 아이디 (기본값: admin)
    ADMIN_PASSWORD: 관리자 비밀번호 (기본값: admin123!)
    ADMIN_NAME: 관리자 이름 (기본값: 시스템 관리자)
    ADMIN_EMAIL: 관리자 이메일 (기본값: admin@mindforest.com)
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from database.models import Admin, AdminRole
from services.admin.auth_service import AdminAuthService

# 환경 변수 로드
load_dotenv()

def get_database_url():
    """데이터베이스 URL 생성"""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # 개별 환경 변수로부터 데이터베이스 URL 구성
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "mindforest")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "password")
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def create_initial_admin():
    """초기 관리자 계정 생성"""
    # 데이터베이스 연결
    database_url = get_database_url()
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # 환경 변수에서 관리자 정보 가져오기
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123!")
        admin_name = os.getenv("ADMIN_NAME", "시스템 관리자")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@mindforest.com")
        
        print(f"초기 관리자 계정 생성을 시작합니다...")
        print(f"아이디: {admin_username}")
        print(f"이름: {admin_name}")
        print(f"이메일: {admin_email}")
        
        # 기존 관리자 계정 확인
        existing_admin = db.query(Admin).filter(
            (Admin.username == admin_username) | (Admin.email == admin_email)
        ).first()
        
        if existing_admin:
            print(f"⚠️  이미 존재하는 관리자 계정입니다.")
            if existing_admin.username == admin_username:
                print(f"   동일한 아이디: {admin_username}")
            if existing_admin.email == admin_email:
                print(f"   동일한 이메일: {admin_email}")
            return False
        
        # 비밀번호 해시화
        password_hash = AdminAuthService.hash_password(admin_password)
        
        # 새 관리자 계정 생성
        new_admin = Admin(
            username=admin_username,
            password_hash=password_hash,
            name=admin_name,
            email=admin_email,
            role=AdminRole.super_admin,  # 최고 관리자 권한
            is_active=True
        )
        
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        
        print(f"✅ 초기 관리자 계정이 성공적으로 생성되었습니다!")
        print(f"   ID: {new_admin.id}")
        print(f"   아이디: {new_admin.username}")
        print(f"   역할: {new_admin.role.value}")
        print(f"   생성일: {new_admin.created_at}")
        print()
        print(f"🔐 로그인 정보:")
        print(f"   아이디: {admin_username}")
        print(f"   비밀번호: {admin_password}")
        print()
        print(f"⚠️  보안을 위해 최초 로그인 후 비밀번호를 변경하세요!")
        
        return True
        
    except Exception as e:
        print(f"❌ 관리자 계정 생성 중 오류가 발생했습니다: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

def main():
    """메인 함수"""
    print("=" * 50)
    print("🌲 MindForest 초기 관리자 계정 생성")
    print("=" * 50)
    
    try:
        success = create_initial_admin()
        if success:
            print("\n관리자 승인 시스템이 준비되었습니다!")
            print("이제 다음 API 엔드포인트를 사용할 수 있습니다:")
            print("- POST /api/v1/admin/auth/login - 관리자 로그인")
            print("- GET /api/v1/admin/counselors/pending - 승인 대기 상담사 목록")
            print("- POST /api/v1/admin/counselors/approve - 상담사 승인/거절")
            print("- GET /api/v1/admin/counselors/list - 상담사 목록 조회")
        else:
            print("\n❌ 초기 관리자 계정 생성에 실패했습니다.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n작업이 취소되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()