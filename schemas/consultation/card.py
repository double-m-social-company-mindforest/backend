from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import datetime
import json


class ConsultationCardCreate(BaseModel):
    additional_notes: str = ""


class ConsultationCardData(BaseModel):
    user_nickname: str
    character_type: str
    character_name: str
    character_animal: str
    character_group: str
    consultation_code: str
    consultation_date: str  # ISO 문자열로 저장
    hashtags: List[str]
    additional_notes: str


class ConsultationCardResponse(BaseModel):
    id: int
    consultation_id: int
    card_data: ConsultationCardData
    issued_at: datetime

    class Config:
        from_attributes = True