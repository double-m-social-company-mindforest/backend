from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from database.models import Gender, CounselorStatus


class CounselorPendingApproval(BaseModel):
    """승인 대기 중인 상담사 정보"""
    id: int
    username: str
    name: str
    gender: Gender
    birth_date: str
    phone: str
    email: Optional[str]
    counseling_fields: List[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class CounselorApprovalRequest(BaseModel):
    """상담사 승인 요청"""
    counselor_id: int = Field(..., description="상담사 ID")
    action: str = Field(..., pattern="^(approve|reject)$", description="승인 액션 (approve/reject)")
    rejection_reason: Optional[str] = Field(None, description="거절 사유")


class CounselorApprovalResponse(BaseModel):
    """상담사 승인 응답"""
    counselor_id: int
    action: str
    success: bool
    message: str


class CounselorListItem(BaseModel):
    """상담사 목록 항목"""
    id: int
    username: str
    name: str
    gender: Gender
    phone: str
    email: Optional[str]
    status: CounselorStatus
    is_approved: bool
    is_active: bool
    approved_at: Optional[datetime]
    created_at: datetime
    last_active_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class CounselorListRequest(BaseModel):
    """상담사 목록 조회 요청"""
    page: int = Field(default=1, ge=1, description="페이지 번호")
    size: int = Field(default=20, ge=1, le=100, description="페이지 크기")
    status_filter: Optional[str] = Field(None, pattern="^(pending|approved|rejected|all)$", description="상태 필터")
    search: Optional[str] = Field(None, max_length=100, description="검색어 (이름, 아이디)")


class CounselorListResponse(BaseModel):
    """상담사 목록 조회 응답"""
    counselors: List[CounselorListItem]
    total: int
    page: int
    size: int
    total_pages: int


class CounselorDetailResponse(BaseModel):
    """상담사 상세 정보 응답"""
    id: int
    username: str
    name: str
    gender: Gender
    birth_date: str
    phone: str
    email: Optional[str]
    counseling_fields: List[int]
    status: CounselorStatus
    is_approved: bool
    is_active: bool
    approved_at: Optional[datetime]
    approved_by: Optional[int]
    created_at: datetime
    last_active_at: Optional[datetime]
    max_concurrent_sessions: int
    
    class Config:
        from_attributes = True


class CounselorStatusUpdateRequest(BaseModel):
    """상담사 상태 업데이트 요청"""
    counselor_id: int = Field(..., description="상담사 ID")
    is_active: bool = Field(..., description="활성화 상태")


class CounselorStatsResponse(BaseModel):
    """상담사 통계 응답"""
    total_counselors: int
    pending_approval: int
    approved_counselors: int
    active_counselors: int
    online_counselors: int