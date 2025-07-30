from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum
import pytz


class ConsultationStatus(str, Enum):
    waiting = "waiting"
    active = "active"
    completed = "completed"
    terminated = "terminated"


class ConsultationStartRequest(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=100, description="사용자 닉네임")
    character_type_preference: Optional[int] = Field(None, description="선호하는 캐릭터 유형 ID")
    quick_match: bool = Field(True, description="빠른 매칭 여부")


class ConsultationResponse(BaseModel):
    id: int
    consultation_code: str
    user_nickname: str
    character_type_id: int
    character_name: str
    character_animal: Optional[str]
    character_group: Optional[str]
    status: ConsultationStatus
    created_at: datetime
    completed_at: Optional[datetime]
    is_card_issued: bool

    @field_validator('created_at', 'completed_at')
    @classmethod
    def convert_to_kst(cls, v):
        """UTC 시간을 한국 시간으로 변환"""
        if v is None:
            return v
        
        # UTC로 간주하고 KST로 변환
        if v.tzinfo is None:
            v = v.replace(tzinfo=pytz.UTC)
        elif v.tzinfo != pytz.UTC:
            v = v.astimezone(pytz.UTC)
        
        kst = pytz.timezone('Asia/Seoul')
        return v.astimezone(kst)

    class Config:
        from_attributes = True


class ConsultationReconnectRequest(BaseModel):
    nickname: Optional[str] = Field(None, description="재연결 시 닉네임 변경")


class ReconsultationRequest(BaseModel):
    """재상담 요청"""
    previous_consultation_code: str = Field(..., description="이전 상담 코드")


class ConsultationEndResponse(BaseModel):
    consultation_code: str
    status: ConsultationStatus
    completed_at: datetime
    message: str

    @field_validator('completed_at')
    @classmethod
    def convert_to_kst(cls, v):
        """UTC 시간을 한국 시간으로 변환"""
        if v is None:
            return v
        
        # UTC로 간주하고 KST로 변환
        if v.tzinfo is None:
            v = v.replace(tzinfo=pytz.UTC)
        elif v.tzinfo != pytz.UTC:
            v = v.astimezone(pytz.UTC)
        
        kst = pytz.timezone('Asia/Seoul')
        return v.astimezone(kst)