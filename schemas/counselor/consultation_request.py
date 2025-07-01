from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class RequestStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    expired = "expired"


class ConsultationRequestCreate(BaseModel):
    consultation_id: int
    counselor_id: int


class ConsultationRequestResponse(BaseModel):
    response_message: Optional[str] = Field(None, description="응답 메시지")


class ConsultationRequestDetail(BaseModel):
    id: int
    consultation_id: int
    counselor_id: int
    status: RequestStatus
    requested_at: datetime
    responded_at: Optional[datetime]
    response_message: Optional[str]
    
    # 상담 정보
    consultation_code: str
    user_nickname: str
    character_type_name: str
    
    # 상담사 정보
    counselor_name: str

    class Config:
        from_attributes = True


class PendingRequestsResponse(BaseModel):
    requests: list[ConsultationRequestDetail]
    total_count: int