from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum
from database.models import Gender


class CounselorStatus(str, Enum):
    offline = "offline"
    online = "online"
    busy = "busy"
    away = "away"
    waiting_for_call = "waiting_for_call"  # 콜대기 상태


# CounselorCreate 스키마 제거됨 - 상담사 등록은 CounselorRegister 스키마 사용


class CounselorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = None
    specialties: Optional[List[str]] = None
    bio: Optional[str] = None
    license_number: Optional[str] = None
    experience_years: Optional[int] = Field(None, ge=0)
    max_concurrent_sessions: Optional[int] = Field(None, ge=1, le=10)
    is_active: Optional[bool] = None


class CounselorStatusUpdate(BaseModel):
    status: CounselorStatus


class CounselorResponse(BaseModel):
    """상담사 정보 응답 스키마 (기존 API와의 호환성을 위해 유지)"""
    id: int
    name: str
    username: str
    email: Optional[str]
    phone: str
    gender: Gender
    birth_date: str
    counseling_fields: List[int]
    is_approved: bool
    status: CounselorStatus
    max_concurrent_sessions: int
    is_active: bool
    created_at: datetime
    last_active_at: Optional[datetime]
    approved_at: Optional[datetime]

    class Config:
        from_attributes = True


class CounselorListResponse(BaseModel):
    counselors: List[CounselorResponse]
    total_count: int
    online_count: int
    available_count: int  # 상담 가능한 상담사 수


class CounselorStatsResponse(BaseModel):
    counselor_id: int
    total_consultations: int
    active_consultations: int
    avg_session_duration: Optional[float]  # 평균 상담 시간 (분)
    rating: Optional[float]  # 평점 (향후 확장)
    last_consultation_at: Optional[datetime]