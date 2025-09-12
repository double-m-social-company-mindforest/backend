from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class UserCurriculumSessionResponse(BaseModel):
    """커리큘럼 세션 목록 응답"""
    id: int
    user_id: int
    user_nickname: str
    session_number: int
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCurriculumSessionDetail(BaseModel):
    """커리큘럼 세션 상세 응답"""
    id: int
    user_id: int
    user_nickname: str
    session_number: int
    session_data: dict
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionSummary(BaseModel):
    """세션 요약 정보"""
    id: int
    session_number: int
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProgressSummary(BaseModel):
    """사용자별 커리큘럼 진행 상황 요약"""
    user_id: int
    user_nickname: str
    total_sessions: int
    completed_sessions: int
    in_progress_sessions: int
    not_started_sessions: int
    progress_percentage: float
    sessions: List[SessionSummary]
    last_activity: Optional[datetime] = None

    class Config:
        from_attributes = True