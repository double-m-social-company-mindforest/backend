from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, Request
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import hashlib
import secrets

from database.models import Admin, AdminRefreshToken, AdminRole
from schemas.admin.auth import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminInfo,
    AdminCreateRequest,
    AdminChangePasswordRequest,
    TokenRefreshRequest,
    TokenRefreshResponse
)

logger = logging.getLogger(__name__)

# 비밀번호 암호화 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정 (환경변수로 관리하는 것이 좋음)
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class AdminAuthService:
    """관리자 인증 관련 서비스"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """비밀번호 해시화"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """JWT 액세스 토큰 생성"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access", "user_type": "admin"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> tuple[str, str]:
        """Refresh Token 생성 (토큰, 해시값 반환)"""
        # 고유한 토큰 생성
        token = secrets.token_urlsafe(32)
        
        # 토큰 해시 생성 (DB 저장용)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # JWT 형식으로도 저장
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({
            "exp": expire, 
            "type": "refresh", 
            "user_type": "admin",
            "token_hash": token_hash
        })
        
        jwt_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return jwt_token, token_hash
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """JWT 토큰 검증"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # 관리자 토큰인지 확인
            if payload.get("user_type") != "admin":
                return None
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def check_username_availability(db: Session, username: str) -> bool:
        """관리자 아이디 중복 확인"""
        existing_admin = db.query(Admin).filter(Admin.username == username).first()
        return existing_admin is None
    
    @staticmethod
    def check_email_availability(db: Session, email: str) -> bool:
        """관리자 이메일 중복 확인"""
        existing_admin = db.query(Admin).filter(Admin.email == email).first()
        return existing_admin is None
    
    @staticmethod
    def create_admin(db: Session, admin_data: AdminCreateRequest, created_by_id: Optional[int] = None) -> AdminInfo:
        """관리자 계정 생성"""
        try:
            # 1. 중복 확인
            if not AdminAuthService.check_username_availability(db, admin_data.username):
                raise HTTPException(status_code=400, detail="이미 사용 중인 아이디입니다")
            
            if not AdminAuthService.check_email_availability(db, admin_data.email):
                raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")
            
            # 2. 비밀번호 해시화
            hashed_password = AdminAuthService.hash_password(admin_data.password)
            
            # 3. 새 관리자 생성
            new_admin = Admin(
                username=admin_data.username,
                password_hash=hashed_password,
                name=admin_data.name,
                email=admin_data.email,
                role=admin_data.role,
                created_by=created_by_id,
                is_active=True
            )
            
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)
            
            logger.info(f"새 관리자 생성 완료: {new_admin.username} (역할: {new_admin.role})")
            
            return AdminInfo.from_orm(new_admin)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"관리자 생성 중 오류 발생: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail="관리자 계정 생성 중 오류가 발생했습니다")
    
    @staticmethod
    def authenticate_admin(db: Session, username: str, password: str) -> Optional[Admin]:
        """관리자 인증"""
        admin = db.query(Admin).filter(Admin.username == username).first()
        
        if not admin:
            logger.error(f"관리자를 찾을 수 없음: {username}")
            return None
        
        # 비밀번호 검증
        try:
            is_valid = AdminAuthService.verify_password(password, admin.password_hash)
            logger.info(f"관리자 비밀번호 검증 결과 - 사용자: {username}, 결과: {is_valid}")
            
            if not is_valid:
                return None
        except Exception as e:
            logger.error(f"관리자 비밀번호 검증 중 오류: {e}")
            return None
        
        # 계정 상태 확인
        if not admin.is_active:
            raise HTTPException(status_code=403, detail="비활성화된 관리자 계정입니다")
        
        return admin
    
    @staticmethod
    def save_refresh_token(
        db: Session,
        admin_id: int,
        token_hash: str,
        expires_at: datetime,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """관리자 Refresh Token을 DB에 저장"""
        try:
            refresh_token = AdminRefreshToken(
                admin_id=admin_id,
                token_hash=token_hash,
                expires_at=expires_at,
                user_agent=user_agent,
                ip_address=ip_address,
                is_active=True
            )
            
            db.add(refresh_token)
            db.commit()
        except Exception as e:
            logger.error(f"관리자 Refresh Token 저장 중 오류: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def login(db: Session, login_data: AdminLoginRequest, request: Optional[Request] = None) -> AdminLoginResponse:
        """관리자 로그인"""
        try:
            # 1. 인증
            admin = AdminAuthService.authenticate_admin(db, login_data.username, login_data.password)
            
            if not admin:
                raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다")
            
            # 2. 액세스 토큰 생성
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = AdminAuthService.create_access_token(
                data={"sub": str(admin.id), "username": admin.username, "role": admin.role.value},
                expires_delta=access_token_expires
            )
            
            # 3. Refresh Token 생성
            refresh_token, token_hash = AdminAuthService.create_refresh_token(
                data={"sub": str(admin.id), "username": admin.username, "role": admin.role.value}
            )
            
            # 4. Refresh Token DB 저장
            refresh_expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            user_agent = request.headers.get("User-Agent") if request else None
            ip_address = request.client.host if request else None
            
            AdminAuthService.save_refresh_token(
                db=db,
                admin_id=admin.id,
                token_hash=token_hash,
                expires_at=refresh_expires_at,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            # 5. 마지막 로그인 시간 업데이트
            admin.last_login_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"관리자 로그인 성공: {admin.username} (역할: {admin.role})")
            
            return AdminLoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                admin_info=AdminInfo.from_orm(admin)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"관리자 로그인 처리 중 오류 발생: {e}")
            raise HTTPException(status_code=500, detail="로그인 처리 중 오류가 발생했습니다")
    
    @staticmethod
    def get_current_admin(db: Session, token: str) -> Admin:
        """현재 로그인한 관리자 정보 조회"""
        payload = AdminAuthService.verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")
        
        admin_id = payload.get("sub")
        if not admin_id:
            raise HTTPException(status_code=401, detail="토큰에서 관리자 정보를 찾을 수 없습니다")
        
        admin = db.query(Admin).filter(Admin.id == int(admin_id)).first()
        if not admin:
            raise HTTPException(status_code=404, detail="관리자를 찾을 수 없습니다")
        
        if not admin.is_active:
            raise HTTPException(status_code=403, detail="비활성화된 관리자 계정입니다")
        
        return admin
    
    @staticmethod
    def change_password(db: Session, admin_id: int, password_data: AdminChangePasswordRequest) -> Dict[str, str]:
        """관리자 비밀번호 변경"""
        try:
            admin = db.query(Admin).filter(Admin.id == admin_id).first()
            if not admin:
                raise HTTPException(status_code=404, detail="관리자를 찾을 수 없습니다")
            
            # 현재 비밀번호 확인
            if not AdminAuthService.verify_password(password_data.current_password, admin.password_hash):
                raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다")
            
            # 새 비밀번호 설정
            admin.password_hash = AdminAuthService.hash_password(password_data.new_password)
            db.commit()
            
            logger.info(f"관리자 비밀번호 변경 완료: {admin.username}")
            
            return {"message": "비밀번호가 성공적으로 변경되었습니다"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"관리자 비밀번호 변경 중 오류 발생: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail="비밀번호 변경 중 오류가 발생했습니다")
    
    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> TokenRefreshResponse:
        """Refresh Token으로 새로운 Access Token 발급"""
        try:
            # 1. Refresh Token 검증
            payload = AdminAuthService.verify_token(refresh_token)
            if not payload:
                raise HTTPException(status_code=401, detail="유효하지 않은 Refresh Token입니다")
            
            # 토큰 타입 확인
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="잘못된 토큰 타입입니다")
            
            token_hash = payload.get("token_hash")
            admin_id = int(payload.get("sub"))
            
            # 2. DB에서 토큰 확인
            refresh_token_record = db.query(AdminRefreshToken).filter(
                and_(
                    AdminRefreshToken.token_hash == token_hash,
                    AdminRefreshToken.admin_id == admin_id,
                    AdminRefreshToken.is_active == True
                )
            ).first()
            
            if not refresh_token_record:
                raise HTTPException(status_code=401, detail="Refresh Token을 찾을 수 없습니다")
            
            if refresh_token_record.expires_at < datetime.utcnow():
                raise HTTPException(status_code=401, detail="만료된 Refresh Token입니다")
            
            # 3. 마지막 사용 시간 업데이트
            refresh_token_record.last_used_at = datetime.utcnow()
            db.commit()
            
            # 4. 관리자 정보 조회
            admin = db.query(Admin).filter(Admin.id == admin_id).first()
            if not admin or not admin.is_active:
                raise HTTPException(status_code=403, detail="비활성화된 관리자 계정입니다")
            
            # 5. 새로운 Access Token 생성
            access_token = AdminAuthService.create_access_token(
                data={"sub": str(admin.id), "username": admin.username, "role": admin.role.value}
            )
            
            return TokenRefreshResponse(
                access_token=access_token,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"관리자 토큰 갱신 중 오류 발생: {e}")
            raise HTTPException(status_code=500, detail="토큰 갱신 중 오류가 발생했습니다")
    
    @staticmethod
    def logout(db: Session, admin_id: int, refresh_token: Optional[str] = None) -> Dict[str, str]:
        """관리자 로그아웃 - Refresh Token 무효화"""
        try:
            if refresh_token:
                # 특정 토큰만 무효화
                payload = AdminAuthService.verify_token(refresh_token)
                if payload and payload.get("type") == "refresh":
                    token_hash = payload.get("token_hash")
                    refresh_token_record = db.query(AdminRefreshToken).filter(
                        and_(
                            AdminRefreshToken.token_hash == token_hash,
                            AdminRefreshToken.admin_id == admin_id
                        )
                    ).first()
                    if refresh_token_record:
                        refresh_token_record.is_active = False
            else:
                # 모든 토큰 무효화
                db.query(AdminRefreshToken).filter(
                    and_(
                        AdminRefreshToken.admin_id == admin_id,
                        AdminRefreshToken.is_active == True
                    )
                ).update({"is_active": False})
            
            db.commit()
            
            logger.info(f"관리자 로그아웃: admin_id={admin_id}")
            return {"message": "성공적으로 로그아웃되었습니다"}
            
        except Exception as e:
            logger.error(f"관리자 로그아웃 처리 중 오류: {e}")
            raise HTTPException(status_code=500, detail="로그아웃 처리 중 오류가 발생했습니다")