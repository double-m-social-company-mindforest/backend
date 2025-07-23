from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from database.connection import get_db
from database.models import Admin
from schemas.admin.counselor_management import (
    CounselorPendingApproval,
    CounselorApprovalRequest,
    CounselorApprovalResponse,
    CounselorListRequest,
    CounselorListResponse,
    CounselorDetailResponse,
    CounselorStatusUpdateRequest,
    CounselorStatsResponse
)
from services.admin.counselor_management_service import CounselorManagementService
from dependencies.admin_auth import (
    require_admin_or_above,
    require_moderator_or_above,
    AdminPermissions
)

router = APIRouter(prefix="/counselors", tags=["관리자 상담사 관리"])


@router.get("/pending", response_model=List[CounselorPendingApproval], summary="승인 대기 상담사 목록")
async def get_pending_approvals(
    current_admin: Admin = Depends(require_moderator_or_above),
    db: Session = Depends(get_db)
):
    """
    승인 대기 중인 상담사 목록 조회
    
    **권한**: 모더레이터 이상
    """
    return CounselorManagementService.get_pending_approvals(db)


@router.post("/approve", response_model=CounselorApprovalResponse, summary="상담사 승인/거절")
async def approve_counselor(
    approval_data: CounselorApprovalRequest,
    current_admin: Admin = Depends(require_admin_or_above),
    db: Session = Depends(get_db)
):
    """
    상담사 승인 또는 거절 처리
    
    **권한**: 관리자 이상
    
    - **counselor_id**: 상담사 ID
    - **action**: 처리 방법 ("approve" 또는 "reject")
    - **rejection_reason**: 거절 사유 (거절 시에만)
    """
    # 권한 확인
    if not AdminPermissions.can_approve_counselor(current_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="상담사 승인 권한이 없습니다"
        )
    
    return CounselorManagementService.approve_counselor(
        db=db,
        counselor_id=approval_data.counselor_id,
        admin_id=current_admin.id,
        action=approval_data.action,
        rejection_reason=approval_data.rejection_reason
    )


@router.post("/bulk-approve", summary="상담사 일괄 승인")
async def bulk_approve_counselors(
    counselor_ids: List[int],
    current_admin: Admin = Depends(require_admin_or_above),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    상담사 일괄 승인
    
    **권한**: 관리자 이상
    
    - **counselor_ids**: 승인할 상담사 ID 목록
    """
    # 권한 확인
    if not AdminPermissions.can_approve_counselor(current_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="상담사 승인 권한이 없습니다"
        )
    
    return CounselorManagementService.bulk_approve_counselors(
        db=db,
        counselor_ids=counselor_ids,
        admin_id=current_admin.id
    )


@router.get("/list", response_model=CounselorListResponse, summary="상담사 목록 조회")
async def get_counselor_list(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    status_filter: str = Query(None, pattern="^(pending|approved|rejected|all)$", description="상태 필터"),
    search: str = Query(None, max_length=100, description="검색어"),
    current_admin: Admin = Depends(require_moderator_or_above),
    db: Session = Depends(get_db)
):
    """
    상담사 목록 조회 (필터링, 검색, 페이징 지원)
    
    **권한**: 모더레이터 이상
    
    - **page**: 페이지 번호 (기본값: 1)
    - **size**: 페이지 크기 (기본값: 20, 최대: 100)
    - **status_filter**: 상태 필터 (pending/approved/rejected/all)
    - **search**: 검색어 (이름, 아이디, 휴대폰, 이메일)
    """
    request = CounselorListRequest(
        page=page,
        size=size,
        status_filter=status_filter,
        search=search
    )
    
    return CounselorManagementService.get_counselor_list(db, request)


@router.get("/{counselor_id}", response_model=CounselorDetailResponse, summary="상담사 상세 정보")
async def get_counselor_detail(
    counselor_id: int,
    current_admin: Admin = Depends(require_moderator_or_above),
    db: Session = Depends(get_db)
):
    """
    상담사 상세 정보 조회
    
    **권한**: 모더레이터 이상
    
    - **counselor_id**: 상담사 ID
    """
    return CounselorManagementService.get_counselor_detail(db, counselor_id)


@router.put("/status", summary="상담사 활성화 상태 변경")
async def update_counselor_status(
    status_data: CounselorStatusUpdateRequest,
    current_admin: Admin = Depends(require_admin_or_above),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    상담사 활성화/비활성화 상태 변경
    
    **권한**: 관리자 이상
    
    - **counselor_id**: 상담사 ID
    - **is_active**: 활성화 상태 (true/false)
    """
    # 권한 확인
    if not AdminPermissions.can_manage_counselor(current_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="상담사 관리 권한이 없습니다"
        )
    
    return CounselorManagementService.update_counselor_status(
        db=db,
        request=status_data,
        admin_id=current_admin.id
    )


@router.get("/stats/overview", response_model=CounselorStatsResponse, summary="상담사 통계")
async def get_counselor_stats(
    current_admin: Admin = Depends(require_moderator_or_above),
    db: Session = Depends(get_db)
):
    """
    상담사 통계 정보 조회
    
    **권한**: 모더레이터 이상
    
    반환 정보:
    - 전체 상담사 수
    - 승인 대기 중인 상담사 수
    - 승인된 상담사 수
    - 활성화된 상담사 수
    - 온라인 상담사 수
    """
    return CounselorManagementService.get_counselor_stats(db)