from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from database.connection import get_db
from schemas.counselor import (
    CounselorUpdate,
    CounselorResponse,
    CounselorListResponse,
    CounselorStatsResponse,
    CounselorStatusUpdate,
    CounselorStatus
)
from services.counselor import CounselorService

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