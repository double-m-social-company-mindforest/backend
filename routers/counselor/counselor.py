from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from database.connection import get_db
from database.models import Counselor
from schemas.counselor import (
    CounselorUpdate,
    CounselorResponse,
    CounselorListResponse,
    CounselorStatsResponse,
    CounselorStatusUpdate,
    CounselorStatus,
    ConsultationHistoryResponse
)
from services.counselor import CounselorService
from routers.counselor.auth import get_current_counselor

router = APIRouter(
    prefix="/api/v1/counselors",
    tags=["counselors"]
)


# POST 엔드포인트 제거됨 - 상담사 등록은 /api/v1/counselors/auth/register 사용

@router.get("/", response_model=CounselorListResponse)
def get_counselors(
    status: Optional[CounselorStatus] = Query(None, description="상태 필터"),
    specialties: Optional[List[str]] = Query(None, description="전문분야 필터"),
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
    available_only: bool = Query(False, description="상담 가능한 상담사만 조회"),
    db: Session = Depends(get_db)
) -> CounselorListResponse:
    """
    상담사 목록 조회
    
    - **status**: 상태별 필터 (online, offline, busy, away)
    - **specialties**: 전문분야별 필터
    - **is_active**: 활성 상태 필터
    - **available_only**: 현재 상담 가능한 상담사만 조회
    """
    return CounselorService.get_counselors(
        db=db,
        status=status,
        specialties=specialties,
        is_active=is_active,
        available_only=available_only
    )


@router.get("/{counselor_id}", response_model=CounselorResponse)
def get_counselor(
    counselor_id: int,
    db: Session = Depends(get_db)
) -> CounselorResponse:
    """
    특정 상담사 정보 조회
    
    - **counselor_id**: 상담사 ID
    """
    return CounselorService.get_counselor(db, counselor_id)


@router.put("/{counselor_id}", response_model=CounselorResponse)
def update_counselor(
    counselor_id: int,
    counselor_data: CounselorUpdate,
    db: Session = Depends(get_db)
) -> CounselorResponse:
    """
    상담사 정보 업데이트
    
    - **counselor_id**: 상담사 ID
    - 업데이트할 필드만 전송 (부분 업데이트 지원)
    """
    return CounselorService.update_counselor(db, counselor_id, counselor_data)


@router.patch("/{counselor_id}/status", response_model=CounselorResponse)
def update_counselor_status(
    counselor_id: int,
    status_data: CounselorStatusUpdate,
    db: Session = Depends(get_db)
) -> CounselorResponse:
    """
    상담사 상태 업데이트
    
    - **counselor_id**: 상담사 ID
    - **status**: 새로운 상태 (online, offline, busy, away)
    
    상담사가 로그인/로그아웃하거나 상태를 변경할 때 사용
    """
    return CounselorService.update_counselor_status(db, counselor_id, status_data)


@router.get("/{counselor_id}/stats", response_model=CounselorStatsResponse)
def get_counselor_stats(
    counselor_id: int,
    db: Session = Depends(get_db)
) -> CounselorStatsResponse:
    """
    상담사 통계 조회
    
    - **counselor_id**: 상담사 ID
    
    상담 건수, 평균 상담 시간, 현재 활성 상담 수 등의 통계 정보를 제공
    """
    return CounselorService.get_counselor_stats(db, counselor_id)


@router.get("/{counselor_id}/consultations", response_model=ConsultationHistoryResponse)
def get_consultation_history(
    counselor_id: int,
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    status: Optional[str] = Query(None, description="상태 필터 (completed, terminated, active, waiting)"),
    db: Session = Depends(get_db),
    current_counselor: Counselor = Depends(get_current_counselor)
):
    """
    상담사의 상담 이력을 조회합니다.
    
    - 닉네임: 상담을 받은 사용자의 닉네임
    - 유형: 사용자가 선택한 캐릭터 유형
    - 상담 날짜: YYYY-MM-DD 형식
    - 시작 시간: HH:MM 형식
    - 종료 시간: HH:MM 형식 (종료된 경우만)
    - 상태: 완료, 중단, 진행중, 대기중
    """
    # 본인의 상담 이력만 조회 가능
    if current_counselor.id != counselor_id:
        raise HTTPException(status_code=403, detail="다른 상담사의 이력은 조회할 수 없습니다")
    
    return CounselorService.get_consultation_history(
        db=db,
        counselor_id=counselor_id,
        page=page,
        page_size=page_size,
        status_filter=status
    )