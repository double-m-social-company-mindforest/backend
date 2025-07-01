from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


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

    class Config:
        from_attributes = True


class ConsultationReconnectRequest(BaseModel):
    nickname: Optional[str] = Field(None, description="재연결 시 닉네임 변경")


class ConsultationEndResponse(BaseModel):
    consultation_code: str
    status: ConsultationStatus
    completed_at: datetime
    message: str