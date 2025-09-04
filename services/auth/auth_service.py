from typing import Optional
from datetime import timedelta

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.user import User
from core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token
)
from core.config import settings
from services.auth.jwt_service import (
    save_refresh_token,
    verify_refresh_token,
    invalidate_user_refresh_tokens
)


def authenticate_user(db: Session, nickname: str, password: str) -> Optional[User]:
    """사용자 인증"""
    user = db.query(User).filter(User.nickname == nickname).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_user(db: Session, nickname: str, password: str) -> User:
    """새 사용자 생성"""
    existing_user = db.query(User).filter(User.nickname == nickname).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 닉네임입니다"
        )
    
    hashed_password = get_password_hash(password)
    user = User(
        nickname=nickname,
        password_hash=hashed_password,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


def check_nickname_availability(db: Session, nickname: str) -> bool:
    """닉네임 사용 가능 여부 확인"""
    existing_user = db.query(User).filter(User.nickname == nickname).first()
    return existing_user is None


def login_user(db: Session, nickname: str, password: str) -> dict:
    """사용자 로그인 처리"""
    user = authenticate_user(db, nickname, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="닉네임 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    save_refresh_token(user.id, refresh_token, db)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


def refresh_access_token(db: Session, refresh_token: str) -> dict:
    """Access Token 갱신"""
    user = verify_refresh_token(refresh_token, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프레시 토큰입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


def logout_user(db: Session, user_id: int) -> None:
    """사용자 로그아웃 처리"""
    invalidate_user_refresh_tokens(user_id, db)