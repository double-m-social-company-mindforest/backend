from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, Request
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging
import hashlib
import secrets

from database.models import Counselor, RefreshToken, CounselingField, Gender
from schemas.counselor.auth import (
    CounselorRegister, 
    CounselorLogin, 
    CounselorResponse,
    TokenResponse,
    PasswordChangeRequest
)

logger = logging.getLogger(__name__)

# 비밀번호 암호화 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정 (환경변수로 관리하는 것이 좋음)
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class CounselorAuthService:
    """상담사 인증 관련 서비스"""
    
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
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> tuple[str, str]:
        """Refresh Token 생성 (토큰, 해시값 반환)"""
        # 고유한 토큰 생성
        token = secrets.token_urlsafe(32)
        
        # 토큰 해시 생성 (DB 저장용)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # JWT 형식으로도 저장 (선택사항)
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh", "token_hash": token_hash})
        
        jwt_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return jwt_token, token_hash
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """JWT 토큰 검증"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def check_username_availability(db: Session, username: str) -> bool:
        """아이디 중복 확인"""
        existing_counselor = db.query(Counselor).filter(
            Counselor.username == username
        ).first()
        return existing_counselor is None
    
    @staticmethod
    def check_phone_availability(db: Session, phone: str) -> bool:
        """휴대폰 번호 중복 확인"""
        existing_counselor = db.query(Counselor).filter(
            Counselor.phone == phone
        ).first()
        return existing_counselor is None
    
    @staticmethod
    def check_email_availability(db: Session, email: str) -> bool:
        """이메일 중복 확인"""
        if not email:
            return True  # 이메일은 선택사항
        
        existing_counselor = db.query(Counselor).filter(
            Counselor.email == email
        ).first()
        return existing_counselor is None
    
    @staticmethod
    def validate_counseling_fields(db: Session, field_ids: List[int]) -> bool:
        """상담 분야 ID 유효성 검사"""
        # counseling_fields 테이블에서 유효한 ID인지 확인
        valid_fields = db.query(CounselingField).filter(
            CounselingField.id.in_(field_ids),
            CounselingField.is_active == True
        ).all()
        return len(valid_fields) == len(field_ids)
    
    @staticmethod
    def register_counselor(db: Session, counselor_data: CounselorRegister) -> CounselorResponse:
        """상담사 회원가입"""
        try:
            # 1. 중복 확인
            if not CounselorAuthService.check_username_availability(db, counselor_data.username):
                raise HTTPException(status_code=400, detail="이미 사용 중인 아이디입니다")
            
            if not CounselorAuthService.check_phone_availability(db, counselor_data.phone):
                raise HTTPException(status_code=400, detail="이미 등록된 휴대폰 번호입니다")
            
            if counselor_data.email and not CounselorAuthService.check_email_availability(db, counselor_data.email):
                raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")
            
            # 2. 상담 분야 유효성 검사
            if not CounselorAuthService.validate_counseling_fields(db, counselor_data.counseling_fields):
                raise HTTPException(status_code=400, detail="유효하지 않은 상담 분야가 포함되어 있습니다")
            
            # 3. 비밀번호 해시화
            hashed_password = CounselorAuthService.hash_password(counselor_data.password)
            
            # 4. 새 상담사 생성
            new_counselor = Counselor(
                username=counselor_data.username,
                password_hash=hashed_password,
                name=counselor_data.name,
                gender=counselor_data.gender,
                birth_date=counselor_data.birth_date,
                phone=counselor_data.phone,
                email=counselor_data.email,
                counseling_fields=counselor_data.counseling_fields,
                is_approved=False,  # 관리자 승인 대기
                is_active=True
            )
            
            db.add(new_counselor)
            db.commit()
            db.refresh(new_counselor)
            
            logger.info(f"새 상담사 등록 완료: {new_counselor.username}")
            
            return CounselorResponse.from_orm(new_counselor)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"상담사 등록 중 오류 발생: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail="회원가입 처리 중 오류가 발생했습니다")
    
    @staticmethod
    def authenticate_counselor(db: Session, username: str, password: str) -> Optional[Counselor]:
        """상담사 인증"""
        counselor = db.query(Counselor).filter(
            Counselor.username == username
        ).first()
        
        if not counselor:
            logger.error(f"사용자를 찾을 수 없음: {username}")
            return None
        
        # 비밀번호 검증 로깅 추가
        try:
            is_valid = CounselorAuthService.verify_password(password, counselor.password_hash)
            logger.info(f"비밀번호 검증 결과 - 사용자: {username}, 결과: {is_valid}")
            
            if not is_valid:
                return None
        except Exception as e:
            logger.error(f"비밀번호 검증 중 오류: {e}")
            return None
        
        # 계정 상태 확인
        if not counselor.is_active:
            raise HTTPException(status_code=403, detail="비활성화된 계정입니다")
        
        if not counselor.is_approved:
            raise HTTPException(status_code=403, detail="관리자 승인이 필요한 계정입니다")
        
        return counselor
    
    @staticmethod
    def save_refresh_token(
        db: Session, 
        counselor_id: int, 
        token_hash: str, 
        expires_at: datetime,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """Refresh Token을 DB에 저장"""
        try:
            # 새 토큰 저장
            refresh_token = RefreshToken(
                counselor_id=counselor_id,
                token_hash=token_hash,
                expires_at=expires_at,
                user_agent=user_agent,
                ip_address=ip_address,
                is_active=True
            )
            
            db.add(refresh_token)
            db.commit()
        except Exception as e:
            logger.error(f"Refresh Token 저장 중 오류: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def login(db: Session, login_data: CounselorLogin, request: Optional[Request] = None) -> TokenResponse:
        """상담사 로그인"""
        try:
            # 1. 인증
            counselor = CounselorAuthService.authenticate_counselor(
                db, login_data.username, login_data.password
            )
            
            if not counselor:
                raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다")
            
            # 2. 액세스 토큰 생성
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = CounselorAuthService.create_access_token(
                data={"sub": str(counselor.id), "username": counselor.username},
                expires_delta=access_token_expires
            )
            
            # 3. Refresh Token 생성
            refresh_token, token_hash = CounselorAuthService.create_refresh_token(
                data={"sub": str(counselor.id), "username": counselor.username}
            )
            
            # 4. Refresh Token DB 저장
            refresh_expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            user_agent = request.headers.get("User-Agent") if request else None
            ip_address = request.client.host if request else None
            
            CounselorAuthService.save_refresh_token(
                db=db,
                counselor_id=counselor.id,
                token_hash=token_hash,
                expires_at=refresh_expires_at,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            # 5. 마지막 로그인 시간 업데이트
            counselor.last_active_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"상담사 로그인 성공: {counselor.username}")
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                refresh_expires_in=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"로그인 처리 중 오류 발생: {e}")
            raise HTTPException(status_code=500, detail="로그인 처리 중 오류가 발생했습니다")
    
    @staticmethod
    def get_current_counselor(db: Session, token: str) -> Counselor:
        """현재 로그인한 상담사 정보 조회"""
        payload = CounselorAuthService.verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")
        
        counselor_id = payload.get("sub")
        if not counselor_id:
            raise HTTPException(status_code=401, detail="토큰에서 사용자 정보를 찾을 수 없습니다")
        
        counselor = db.query(Counselor).filter(Counselor.id == int(counselor_id)).first()
        if not counselor:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        if not counselor.is_active:
            raise HTTPException(status_code=403, detail="비활성화된 계정입니다")
        
        return counselor
    
    @staticmethod
    def change_password(db: Session, counselor_id: int, password_data: PasswordChangeRequest) -> Dict[str, str]:
        """비밀번호 변경"""
        try:
            counselor = db.query(Counselor).filter(Counselor.id == counselor_id).first()
            if not counselor:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
            
            # 현재 비밀번호 확인
            if not CounselorAuthService.verify_password(password_data.current_password, counselor.password_hash):
                raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다")
            
            # 새 비밀번호 설정
            counselor.password_hash = CounselorAuthService.hash_password(password_data.new_password)
            db.commit()
            
            logger.info(f"비밀번호 변경 완료: {counselor.username}")
            
            return {"message": "비밀번호가 성공적으로 변경되었습니다"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"비밀번호 변경 중 오류 발생: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail="비밀번호 변경 중 오류가 발생했습니다")
    
    @staticmethod
    def get_counseling_fields(db: Session) -> List[Dict[str, Any]]:
        """상담 분야 목록 조회"""
        fields = db.query(CounselingField).filter(
            CounselingField.is_active == True
        ).order_by(CounselingField.display_order).all()
        
        return [
            {
                "id": field.id,
                "code": field.code,
                "name": field.name,
                "description": field.description,
                "is_active": field.is_active,
                "display_order": field.display_order
            }
            for field in fields
        ]
    
    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Dict[str, Any]:
        """Refresh Token으로 새로운 Access Token 발급"""
        try:
            # 1. Refresh Token 검증
            payload = CounselorAuthService.verify_token(refresh_token)
            if not payload:
                raise HTTPException(status_code=401, detail="유효하지 않은 Refresh Token입니다")
            
            # 토큰 타입 확인
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="잘못된 토큰 타입입니다")
            
            token_hash = payload.get("token_hash")
            counselor_id = int(payload.get("sub"))
            
            # 2. DB에서 토큰 확인
            refresh_token_record = db.query(RefreshToken).filter(
                and_(
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.counselor_id == counselor_id,
                    RefreshToken.is_active == True
                )
            ).first()
            
            if not refresh_token_record:
                raise HTTPException(status_code=401, detail="Refresh Token을 찾을 수 없습니다")
            
            if refresh_token_record.expires_at < datetime.utcnow():
                raise HTTPException(status_code=401, detail="만료된 Refresh Token입니다")
            
            # 3. 마지막 사용 시간 업데이트
            refresh_token_record.last_used_at = datetime.utcnow()
            db.commit()
            
            # 4. 상담사 정보 조회
            counselor = db.query(Counselor).filter(Counselor.id == counselor_id).first()
            if not counselor or not counselor.is_active:
                raise HTTPException(status_code=403, detail="비활성화된 계정입니다")
            
            # 5. 새로운 Access Token 생성
            access_token = CounselorAuthService.create_access_token(
                data={"sub": str(counselor.id), "username": counselor.username}
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"토큰 갱신 중 오류 발생: {e}")
            raise HTTPException(status_code=500, detail="토큰 갱신 중 오류가 발생했습니다")
    
    @staticmethod
    def logout(db: Session, counselor_id: int, refresh_token: Optional[str] = None) -> Dict[str, str]:
        """로그아웃 - Refresh Token 무효화"""
        try:
            if refresh_token:
                # 특정 토큰만 무효화
                payload = CounselorAuthService.verify_token(refresh_token)
                if payload and payload.get("type") == "refresh":
                    token_hash = payload.get("token_hash")
                    refresh_token_record = db.query(RefreshToken).filter(
                        and_(
                            RefreshToken.token_hash == token_hash,
                            RefreshToken.counselor_id == counselor_id
                        )
                    ).first()
                    if refresh_token_record:
                        refresh_token_record.is_active = False
            else:
                # 모든 토큰 무효화
                db.query(RefreshToken).filter(
                    and_(
                        RefreshToken.counselor_id == counselor_id,
                        RefreshToken.is_active == True
                    )
                ).update({"is_active": False})
            
            db.commit()
            
            logger.info(f"상담사 로그아웃: counselor_id={counselor_id}")
            return {"message": "성공적으로 로그아웃되었습니다"}
            
        except Exception as e:
            logger.error(f"로그아웃 처리 중 오류: {e}")
            raise HTTPException(status_code=500, detail="로그아웃 처리 중 오류가 발생했습니다")