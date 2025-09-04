from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from database.connection import get_db
from models.user import User, UserRefreshToken
from core.config import settings
from core.security import verify_token, hash_token


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """현재 인증된 사용자 가져오기"""
    token = credentials.credentials
    
    try:
        payload = verify_token(token)
        
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token이 아닙니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰이 유효하지 않습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 유효하지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """활성 사용자만 허용"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다"
        )
    return current_user


def verify_refresh_token(token: str, db: Session) -> Optional[User]:
    """Refresh Token 검증"""
    try:
        payload = verify_token(token)
        
        if payload.get("type") != "refresh":
            return None
        
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        
        token_hash = hash_token(token)
        
        refresh_token = db.query(UserRefreshToken).filter(
            UserRefreshToken.token_hash == token_hash,
            UserRefreshToken.user_id == user_id,
            UserRefreshToken.is_active == True,
            UserRefreshToken.expires_at > datetime.utcnow()
        ).first()
        
        if not refresh_token:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        return user if user and user.is_active else None
        
    except JWTError:
        return None


def invalidate_user_refresh_tokens(user_id: int, db: Session) -> None:
    """사용자의 모든 Refresh Token 무효화"""
    db.query(UserRefreshToken).filter(
        UserRefreshToken.user_id == user_id
    ).update({"is_active": False})
    db.commit()


def save_refresh_token(user_id: int, token: str, db: Session) -> None:
    """Refresh Token DB에 저장"""
    token_hash = hash_token(token)
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    refresh_token = UserRefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        is_active=True
    )
    
    db.add(refresh_token)
    db.commit()