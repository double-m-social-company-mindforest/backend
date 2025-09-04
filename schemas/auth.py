from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class SignupRequest(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=50, description="사용자 닉네임")
    password: str = Field(..., min_length=1, description="비밀번호")
    password_confirm: str = Field(..., min_length=1, description="비밀번호 확인")

    @validator('password_confirm')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('비밀번호가 일치하지 않습니다')
        return v


class SignupResponse(BaseModel):
    status: str = "success"
    message: str = "회원가입이 완료되었습니다"
    data: dict

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "회원가입이 완료되었습니다",
                "data": {
                    "user_id": 1,
                    "nickname": "testuser"
                }
            }
        }


class LoginRequest(BaseModel):
    nickname: str = Field(..., description="사용자 닉네임")
    password: str = Field(..., description="비밀번호")


class LoginResponse(BaseModel):
    status: str = "success"
    message: str = "로그인 성공"
    data: dict

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "로그인 성공",
                "data": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "Bearer",
                    "expires_in": 900
                }
            }
        }


class CheckNicknameRequest(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=50, description="확인할 닉네임")


class CheckNicknameResponse(BaseModel):
    status: str = "success"
    data: dict

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "data": {
                    "available": True
                }
            }
        }


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="리프레시 토큰")


class RefreshTokenResponse(BaseModel):
    status: str = "success"
    data: dict

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "data": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "Bearer",
                    "expires_in": 900
                }
            }
        }


class LogoutResponse(BaseModel):
    status: str = "success"
    message: str = "로그아웃 되었습니다"


class UserInfo(BaseModel):
    id: int
    nickname: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True