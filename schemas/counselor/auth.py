from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from database.models import Gender


class CounselorRegister(BaseModel):
    """상담사 회원가입 요청 스키마"""
    
    # 기본 정보
    username: str = Field(..., min_length=4, max_length=50, description="아이디")
    password: str = Field(..., min_length=8, description="비밀번호")
    password_confirm: str = Field(..., description="비밀번호 확인")
    name: str = Field(..., min_length=2, max_length=100, description="실명")
    gender: Gender = Field(..., description="성별")
    birth_date: str = Field(..., description="생년월일 (YYYY-MM-DD)")
    phone: str = Field(..., description="휴대폰 번호")
    email: Optional[EmailStr] = Field(None, description="이메일 (선택)")
    
    # 상담 관련
    counseling_fields: List[int] = Field(..., min_items=1, max_items=9, description="상담 분야 ID 목록")
    
    @validator('password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('비밀번호가 일치하지 않습니다')
        return v
    
    @validator('birth_date')
    def validate_birth_date(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('생년월일 형식이 올바르지 않습니다 (YYYY-MM-DD)')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        import re
        phone_pattern = r'^010-\d{4}-\d{4}$|^010\d{8}$'
        if not re.match(phone_pattern, v):
            raise ValueError('휴대폰 번호 형식이 올바르지 않습니다 (010-0000-0000 또는 01000000000)')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('아이디는 영문, 숫자, 언더스코어(_)만 사용 가능합니다')
        return v


class CounselorLogin(BaseModel):
    """상담사 로그인 요청 스키마"""
    username: str = Field(..., description="아이디")
    password: str = Field(..., description="비밀번호")


class CounselorResponse(BaseModel):
    """상담사 정보 응답 스키마"""
    id: int
    username: str
    name: str
    gender: Gender
    birth_date: str
    phone: str
    email: Optional[str]
    counseling_fields: List[int]
    is_approved: bool
    approved_at: Optional[datetime]
    status: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """토큰 응답 스키마"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30분
    refresh_expires_in: int = 604800  # 7일


class PasswordChangeRequest(BaseModel):
    """비밀번호 변경 요청 스키마"""
    current_password: str = Field(..., description="현재 비밀번호")
    new_password: str = Field(..., min_length=8, description="새 비밀번호")
    new_password_confirm: str = Field(..., description="새 비밀번호 확인")
    
    @validator('new_password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('새 비밀번호가 일치하지 않습니다')
        return v


class CounselingFieldResponse(BaseModel):
    """상담 분야 응답 스키마"""
    id: int
    code: str
    name: str
    description: Optional[str]
    is_active: bool
    display_order: int
    
    class Config:
        from_attributes = True


class CounselingFieldsListResponse(BaseModel):
    """상담 분야 목록 응답 스키마"""
    fields: List[CounselingFieldResponse]
    total: int


class UsernameCheckRequest(BaseModel):
    """아이디 중복 확인 요청 스키마"""
    username: str = Field(..., min_length=4, max_length=50)


class PhoneCheckRequest(BaseModel):
    """휴대폰 번호 중복 확인 요청 스키마"""
    phone: str = Field(...)


class EmailCheckRequest(BaseModel):
    """이메일 중복 확인 요청 스키마"""
    email: EmailStr = Field(...)


class CheckResponse(BaseModel):
    """중복 확인 응답 스키마"""
    is_available: bool
    message: str


class RefreshTokenRequest(BaseModel):
    """토큰 갱신 요청 스키마"""
    refresh_token: str = Field(..., description="Refresh Token")


class RefreshTokenResponse(BaseModel):
    """토큰 갱신 응답 스키마"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30분