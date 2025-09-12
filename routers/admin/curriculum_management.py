from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from database.connection import get_db
from models.curriculum import UserCurriculumSession
from models.user import User
from schemas.admin.curriculum import (
    UserCurriculumSessionResponse,
    UserCurriculumSessionDetail,
    UserProgressSummary,
    SessionSummary
)
from dependencies.admin_auth import get_current_admin

router = APIRouter(prefix="/curriculum-management")


@router.get("/sessions", response_model=List[UserCurriculumSessionResponse])
async def get_all_curriculum_sessions(
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(None, description="특정 사용자의 세션만 조회"),
    session_number: Optional[int] = Query(None, ge=1, le=8, description="특정 세션 번호만 조회"),
    status: Optional[str] = Query(None, description="세션 상태로 필터링 (not_started/in_progress/completed)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100)
):
    """
    모든 사용자의 커리큘럼 세션 데이터를 조회합니다.
    관리자 권한이 필요합니다.
    """
    query = db.query(UserCurriculumSession).options(
        joinedload(UserCurriculumSession.user)
    )
    
    # 필터링
    if user_id:
        query = query.filter(UserCurriculumSession.user_id == user_id)
    if session_number:
        query = query.filter(UserCurriculumSession.session_number == session_number)
    if status:
        query = query.filter(UserCurriculumSession.status == status)
    
    # 정렬 및 페이지네이션
    query = query.order_by(
        UserCurriculumSession.created_at.desc()
    ).offset(skip).limit(limit)
    
    sessions = query.all()
    
    return [
        UserCurriculumSessionResponse(
            id=session.id,
            user_id=session.user_id,
            user_nickname=session.user.nickname,
            session_number=session.session_number,
            status=session.status,
            created_at=session.created_at,
            updated_at=session.updated_at,
            completed_at=session.completed_at
        )
        for session in sessions
    ]


@router.get("/sessions/{session_id}", response_model=UserCurriculumSessionDetail)
async def get_curriculum_session_detail(
    session_id: int,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    특정 커리큘럼 세션의 상세 데이터를 조회합니다.
    session_data 포함.
    """
    session = db.query(UserCurriculumSession).options(
        joinedload(UserCurriculumSession.user)
    ).filter(UserCurriculumSession.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    return UserCurriculumSessionDetail(
        id=session.id,
        user_id=session.user_id,
        user_nickname=session.user.nickname,
        session_number=session.session_number,
        session_data=session.session_data,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
        completed_at=session.completed_at
    )


@router.get("/users/{user_id}/sessions/{session_number}", response_model=UserCurriculumSessionDetail)
async def get_user_session_data(
    user_id: int,
    session_number: int,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    특정 사용자의 특정 세션 데이터를 조회합니다.
    user_id와 session_number를 사용하여 정확한 세션을 찾습니다.
    """
    if session_number < 1 or session_number > 8:
        raise HTTPException(status_code=400, detail="세션 번호는 1~8 사이여야 합니다.")
    
    session = db.query(UserCurriculumSession).options(
        joinedload(UserCurriculumSession.user)
    ).filter(
        UserCurriculumSession.user_id == user_id,
        UserCurriculumSession.session_number == session_number
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404, 
            detail=f"사용자 {user_id}의 세션 {session_number} 데이터를 찾을 수 없습니다."
        )
    
    return UserCurriculumSessionDetail(
        id=session.id,
        user_id=session.user_id,
        user_nickname=session.user.nickname,
        session_number=session.session_number,
        session_data=session.session_data,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
        completed_at=session.completed_at
    )


@router.get("/users/{user_id}/progress", response_model=UserProgressSummary)
async def get_user_progress(
    user_id: int,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    특정 사용자의 커리큘럼 진행 상황을 요약하여 조회합니다.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    sessions = db.query(UserCurriculumSession).filter(
        UserCurriculumSession.user_id == user_id
    ).order_by(UserCurriculumSession.session_number).all()
    
    completed_sessions = [s for s in sessions if s.status == "completed"]
    in_progress_sessions = [s for s in sessions if s.status == "in_progress"]
    
    # 전체 진행률 계산
    progress_percentage = (len(completed_sessions) / 8) * 100
    
    # 가장 최근 활동 시간
    last_activity = None
    if sessions:
        last_activity = max(s.updated_at for s in sessions)
    
    # SessionSummary 형식으로 변환
    session_summaries = [
        SessionSummary(
            id=s.id,
            session_number=s.session_number,
            status=s.status,
            created_at=s.created_at,
            updated_at=s.updated_at,
            completed_at=s.completed_at
        )
        for s in sessions
    ]
    
    return UserProgressSummary(
        user_id=user_id,
        user_nickname=user.nickname,
        total_sessions=8,
        completed_sessions=len(completed_sessions),
        in_progress_sessions=len(in_progress_sessions),
        not_started_sessions=8 - len(sessions),
        progress_percentage=progress_percentage,
        sessions=session_summaries,
        last_activity=last_activity
    )


@router.get("/users/{user_id}/all-sessions")
async def get_user_all_sessions(
    user_id: int,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    특정 사용자의 모든 세션 데이터를 한 번에 조회합니다.
    각 세션의 session_data를 포함하여 반환합니다.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    sessions = db.query(UserCurriculumSession).filter(
        UserCurriculumSession.user_id == user_id
    ).order_by(UserCurriculumSession.session_number).all()
    
    result = {
        "user_id": user_id,
        "user_nickname": user.nickname,
        "sessions": []
    }
    
    for session in sessions:
        result["sessions"].append({
            "session_number": session.session_number,
            "status": session.status,
            "session_data": session.session_data,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "completed_at": session.completed_at
        })
    
    return result


@router.get("/all-users-sessions")
async def get_all_users_sessions(
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
    only_completed: bool = Query(False, description="완료된 세션만 조회")
):
    """
    모든 사용자의 세션 데이터를 조회합니다.
    각 사용자별로 그룹화하여 session_data를 포함한 전체 데이터를 반환합니다.
    """
    query = db.query(UserCurriculumSession).options(
        joinedload(UserCurriculumSession.user)
    )
    
    if only_completed:
        query = query.filter(UserCurriculumSession.status == "completed")
    
    sessions = query.order_by(
        UserCurriculumSession.user_id,
        UserCurriculumSession.session_number
    ).all()
    
    # 사용자별로 그룹화
    users_data = {}
    for session in sessions:
        user_id = session.user_id
        if user_id not in users_data:
            users_data[user_id] = {
                "user_id": user_id,
                "user_nickname": session.user.nickname,
                "sessions": []
            }
        
        users_data[user_id]["sessions"].append({
            "session_number": session.session_number,
            "status": session.status,
            "session_data": session.session_data,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "completed_at": session.completed_at
        })
    
    return list(users_data.values())


@router.get("/statistics")
async def get_curriculum_statistics(
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    전체 커리큘럼 통계를 조회합니다.
    """
    # 총 사용자 수
    total_users = db.query(User).count()
    
    # 커리큘럼 참여 사용자 수
    participating_users = db.query(UserCurriculumSession.user_id).distinct().count()
    
    # 세션별 완료 통계
    session_stats = []
    for session_num in range(1, 9):
        total = db.query(UserCurriculumSession).filter(
            UserCurriculumSession.session_number == session_num
        ).count()
        
        completed = db.query(UserCurriculumSession).filter(
            UserCurriculumSession.session_number == session_num,
            UserCurriculumSession.status == "completed"
        ).count()
        
        session_stats.append({
            "session_number": session_num,
            "total_attempts": total,
            "completed": completed,
            "completion_rate": (completed / total * 100) if total > 0 else 0
        })
    
    # 전체 완료율 - 8개 세션을 모두 완료한 사용자 수
    from sqlalchemy import func
    users_completed_all = db.query(func.count(func.distinct(UserCurriculumSession.user_id))).filter(
        UserCurriculumSession.status == "completed"
    ).group_by(UserCurriculumSession.user_id).having(
        func.count(UserCurriculumSession.session_number) == 8
    ).scalar() or 0
    
    return {
        "total_users": total_users,
        "participating_users": participating_users,
        "participation_rate": (participating_users / total_users * 100) if total_users > 0 else 0,
        "users_completed_all": users_completed_all,
        "overall_completion_rate": (users_completed_all / participating_users * 100) if participating_users > 0 else 0,
        "session_statistics": session_stats
    }