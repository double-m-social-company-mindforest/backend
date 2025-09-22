from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from database.connection import get_db
from models.user import User
from schemas.curriculum import (
    Session1Request,
    Session2Request,
    Session3Request,
    Session4Request,
    Session5Request,
    Session6Request,
    SessionSaveResponse,
    SessionDataResponse,
    UserProgressResponse,
    SessionStatus,
    SESSION_TITLES
)
from services.auth.jwt_service import get_current_active_user
from services.curriculum.curriculum_service import CurriculumService


router = APIRouter(
    prefix="/api/curriculum",
    tags=["curriculum"],
    responses={404: {"description": "Not found"}},
)


@router.get("/sessions", response_model=UserProgressResponse)
async def get_all_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    전체 커리큘럼 세션 목록 및 진행 상황 조회
    
    Authorization Header에 Bearer Token 필요
    """
    progress_data = CurriculumService.get_user_progress(db, current_user.id)
    
    return UserProgressResponse(
        status="success",
        data=progress_data
    )


@router.get("/sessions/{session_number}", response_model=SessionDataResponse)
async def get_session_data(
    session_number: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    특정 세션 데이터 조회
    
    - session_number: 1~8 세션 번호
    """
    session = CurriculumService.get_user_session(db, current_user.id, session_number)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"세션 {session_number} 데이터를 찾을 수 없습니다"
        )
    
    return SessionDataResponse.from_orm(session)


@router.post("/sessions/1", response_model=SessionSaveResponse)
async def save_session1_data(
    request: Session1Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    세션 1 (삶의 목표 설정) 데이터 저장
    
    - future_vision: 5년 후 나의 모습 (2개 답변)
    - goals: 3개의 목표와 각각의 첫 걸음
    """
    session_data = request.dict()
    
    session = CurriculumService.save_session_data(
        db=db,
        user_id=current_user.id,
        session_number=1,
        session_data=session_data,
        mark_completed=True
    )
    
    return SessionSaveResponse(
        status="success",
        message="세션 1 데이터가 저장되었습니다",
        data={
            "session_number": session.session_number,
            "status": session.status,
            "updated_at": session.updated_at.isoformat()
        }
    )


@router.post("/sessions/2", response_model=SessionSaveResponse)
async def save_session2_data(
    request: Session2Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    세션 2 (자기초월) 데이터 저장
    
    - helping_experience: 도움을 준 경험과 의미 (2개 답변)
    - reluctant_help: 내키지 않았지만 도운 경험과 변화 (2개 답변)
    - received_help: 도움받은 경험과 영향 (2개 답변)
    - kindness_when_lacking: 부족함을 느낄 때 받은 친절과 영감 (2개 답변)
    """
    session_data = request.dict()
    
    session = CurriculumService.save_session_data(
        db=db,
        user_id=current_user.id,
        session_number=2,
        session_data=session_data,
        mark_completed=True
    )
    
    return SessionSaveResponse(
        status="success",
        message="세션 2 데이터가 저장되었습니다",
        data={
            "session_number": session.session_number,
            "status": session.status,
            "updated_at": session.updated_at.isoformat()
        }
    )


@router.post("/sessions/3", response_model=SessionSaveResponse)
async def save_session3_data(
    request: Session3Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    세션 3 (가치관 탐색) 데이터 저장

    - answer1: 나의 삶에서 가장 큰 영향을 준 사람과 배운 가치
    - answer2: 가장 가깝게 느낀 사람과 그 이유
    - answer3: 관계의 지속성과 이어가게 한 이유 (배열 2개)
    - answer4: 관계의 지속성이 삶의 의미에 미치는 영향
    """
    session_data = request.dict()
    
    session = CurriculumService.save_session_data(
        db=db,
        user_id=current_user.id,
        session_number=3,
        session_data=session_data,
        mark_completed=True
    )
    
    return SessionSaveResponse(
        status="success",
        message="세션 3 데이터가 저장되었습니다",
        data={
            "session_number": session.session_number,
            "status": session.status,
            "updated_at": session.updated_at.isoformat()
        }
    )


@router.post("/sessions/4", response_model=SessionSaveResponse)
async def save_session4_data(
    request: Session4Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    세션 4 (감정 표현 활동) 데이터 저장 - 총 7개 필드 (14개 답변)

    - answer1: 감정 표현 활동 (배열 2개)
    - answer2: 창조적 가치 - 단어 (문자열 1개)
    - answer3: 창조적 가치 - 연결 (문자열 1개)
    - answer4: 창조적 가치 - 활동 (문자열 1개)
    - answer5: 자아정체감 - 표현 문장 (배열 3개)
    - answer6: 자아정체감 - 되고 싶은 나 (배열 3개)
    - answer7: 자아정체감 - 바라는 것 (배열 3개)
    """
    session_data = request.dict()
    
    session = CurriculumService.save_session_data(
        db=db,
        user_id=current_user.id,
        session_number=4,
        session_data=session_data,
        mark_completed=True
    )
    
    return SessionSaveResponse(
        status="success",
        message="세션 4 데이터가 저장되었습니다",
        data={
            "session_number": session.session_number,
            "status": session.status,
            "updated_at": session.updated_at.isoformat()
        }
    )


@router.post("/sessions/5", response_model=SessionSaveResponse)
async def save_session5_data(
    request: Session5Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    세션 5 (감정 관리) 데이터 저장

    - unchangeable_situation: 바꿀 수 없는 상황 설명
    - response_to_situation: 상황 대응 방식
    - person_or_media: 사람 또는 매체 소개
    - overcoming_method: 극복 방법 설명
    - my_tree_thought: 나의 나무에 대한 생각
    """
    session_data = request.dict()

    session = CurriculumService.save_session_data(
        db=db,
        user_id=current_user.id,
        session_number=5,
        session_data=session_data,
        mark_completed=True
    )

    return SessionSaveResponse(
        status="success",
        message="세션 5 데이터가 저장되었습니다",
        data={
            "session_number": session.session_number,
            "status": session.status,
            "updated_at": session.updated_at.isoformat()
        }
    )


@router.post("/sessions/6", response_model=SessionSaveResponse)
async def save_session6_data(
    request: Session6Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    세션 6 (스트레스 대처) 데이터 저장

    - unique_situation: 당신은 어떤 가정에서 태어났나요? 관련 답변
    - unique_life_path: 지금까지의 삶의 목적/의미 관련 답변
    - fill_blank_1~5: 괄호 채우기 답변 (5개)
    - life_meaning: 이 문장이 보여주는 가치
    """
    session_data = request.dict()

    session = CurriculumService.save_session_data(
        db=db,
        user_id=current_user.id,
        session_number=6,
        session_data=session_data,
        mark_completed=True
    )

    return SessionSaveResponse(
        status="success",
        message="세션 6 데이터가 저장되었습니다",
        data={
            "session_number": session.session_number,
            "status": session.status,
            "updated_at": session.updated_at.isoformat()
        }
    )


@router.post("/sessions/{session_number}", response_model=SessionSaveResponse)
async def save_generic_session_data(
    session_number: int,
    session_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    세션 7~8 데이터 저장 (제네릭 엔드포인트)

    - session_number: 7~8 세션 번호
    - session_data: 세션별 데이터 (JSON)
    """
    if session_number in [1, 2, 3, 4, 5, 6]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"세션 {session_number}는 /sessions/{session_number} 전용 엔드포인트를 사용하세요"
        )
    
    session = CurriculumService.save_session_data(
        db=db,
        user_id=current_user.id,
        session_number=session_number,
        session_data=session_data,
        mark_completed=True
    )
    
    session_title = SESSION_TITLES.get(session_number, f"세션 {session_number}")
    
    return SessionSaveResponse(
        status="success",
        message=f"{session_title} 데이터가 저장되었습니다",
        data={
            "session_number": session.session_number,
            "status": session.status,
            "updated_at": session.updated_at.isoformat()
        }
    )


@router.put("/sessions/{session_number}/complete", response_model=SessionSaveResponse)
async def complete_session(
    session_number: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    세션 완료 처리
    
    - session_number: 1~8 세션 번호
    """
    session = CurriculumService.mark_session_complete(
        db=db,
        user_id=current_user.id,
        session_number=session_number
    )
    
    session_title = SESSION_TITLES.get(session_number, f"세션 {session_number}")
    
    return SessionSaveResponse(
        status="success",
        message=f"{session_title}이(가) 완료되었습니다",
        data={
            "session_number": session.session_number,
            "status": session.status,
            "completed_at": session.completed_at.isoformat()
        }
    )


@router.delete("/sessions/{session_number}")
async def delete_session_data(
    session_number: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    세션 데이터 삭제
    
    - session_number: 1~8 세션 번호
    """
    CurriculumService.delete_session_data(
        db=db,
        user_id=current_user.id,
        session_number=session_number
    )
    
    return {
        "status": "success",
        "message": f"세션 {session_number} 데이터가 삭제되었습니다"
    }


@router.get("/progress", response_model=UserProgressResponse)
async def get_user_progress(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    사용자 전체 커리큘럼 진행 상황 조회
    
    Authorization Header에 Bearer Token 필요
    """
    progress_data = CurriculumService.get_user_progress(db, current_user.id)
    
    return UserProgressResponse(
        status="success",
        data=progress_data
    )