from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from database.models import AdminRole


class AdminLoginRequest(BaseModel):
    """관리자 로그인 요청"""
    username: str = Field(..., min_length=4, max_length=50, description="관리자 아이디")
    password: str = Field(..., min_length=8, description="비밀번호")


class AdminLoginResponse(BaseModel):
    """관리자 로그인 응답"""
    access_token: str = Field(..., description="액세스 토큰")
    refresh_token: str = Field(..., description="리프레시 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")
    expires_in: int = Field(..., description="액세스 토큰 만료 시간(초)")
    admin_info: "AdminInfo"


class AdminInfo(BaseModel):
    """관리자 정보"""
    id: int
    username: str
    name: str
    email: str
    role: AdminRole
    is_active: bool
    last_login_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AdminCreateRequest(BaseModel):
    """관리자 계정 생성 요청"""
    username: str = Field(..., min_length=4, max_length=50, description="관리자 아이디")
    password: str = Field(..., min_length=8, description="비밀번호")
    password_confirm: str = Field(..., description="비밀번호 확인")
    name: str = Field(..., min_length=2, max_length=100, description="이름")
    email: EmailStr = Field(..., description="이메일")
    role: AdminRole = Field(default=AdminRole.admin, description="관리자 역할")

    @validator('username')
    def username_must_be_alphanumeric(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('아이디는 영문, 숫자, 언더스코어만 사용 가능합니다')
        return v

    @validator('password_confirm')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('비밀번호가 일치하지 않습니다')
        return v


class AdminChangePasswordRequest(BaseModel):
    """관리자 비밀번호 변경 요청"""
    current_password: str = Field(..., description="현재 비밀번호")
    new_password: str = Field(..., min_length=8, description="새 비밀번호")
    new_password_confirm: str = Field(..., description="새 비밀번호 확인")

    @validator('new_password_confirm')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('새 비밀번호가 일치하지 않습니다')
        return v


class TokenRefreshRequest(BaseModel):
    """토큰 갱신 요청"""
    refresh_token: str = Field(..., description="리프레시 토큰")


class TokenRefreshResponse(BaseModel):
    """토큰 갱신 응답"""
    access_token: str = Field(..., description="새 액세스 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")
    expires_in: int = Field(..., description="액세스 토큰 만료 시간(초)")


# Forward reference 해결
AdminLoginResponse.model_rebuild()