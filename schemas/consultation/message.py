from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    text = "text"
    system = "system"
    image = "image"


class SenderType(str, Enum):
    user = "user"
    counselor = "counselor"


class MessageCreate(BaseModel):
    content: str = Field(..., description="메시지 내용")
    message_type: MessageType = Field(MessageType.text, description="메시지 유형")


class MessageResponse(BaseModel):
    id: int
    consultation_id: int
    sender_type: SenderType
    message: str
    timestamp: datetime
    message_type: MessageType

    class Config:
        from_attributes = True


class MessagesHistoryResponse(BaseModel):
    consultation_code: str
    messages: List[MessageResponse]
    total_count: int


class WebSocketMessage(BaseModel):
    type: str = Field(..., description="메시지 타입 (message, typing, system)")
    data: dict = Field(..., description="메시지 데이터")


class WebSocketMessageData(BaseModel):
    content: Optional[str] = None
    message_type: Optional[MessageType] = None
    sender_type: Optional[SenderType] = None
    timestamp: Optional[datetime] = None
    is_typing: Optional[bool] = None
    event: Optional[str] = None