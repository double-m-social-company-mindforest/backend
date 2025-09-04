from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from models.curriculum import UserCurriculumSession
from schemas.curriculum import SessionStatus, SESSION_TITLES


class CurriculumService:
    
    @staticmethod
    def get_user_session(db: Session, user_id: int, session_number: int) -> Optional[UserCurriculumSession]:
        """특정 세션 데이터 조회"""
        return db.query(UserCurriculumSession).filter(
            UserCurriculumSession.user_id == user_id,
            UserCurriculumSession.session_number == session_number
        ).first()
    
    @staticmethod
    def get_all_user_sessions(db: Session, user_id: int) -> List[UserCurriculumSession]:
        """사용자의 모든 세션 데이터 조회"""
        return db.query(UserCurriculumSession).filter(
            UserCurriculumSession.user_id == user_id
        ).order_by(UserCurriculumSession.session_number).all()
    
    @staticmethod
    def save_session_data(
        db: Session, 
        user_id: int, 
        session_number: int, 
        session_data: Dict[str, Any],
        mark_completed: bool = True
    ) -> UserCurriculumSession:
        """세션 데이터 저장 또는 업데이트"""
        
        # 세션 번호 검증
        if session_number < 1 or session_number > 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="세션 번호는 1에서 8 사이여야 합니다"
            )
        
        # 기존 세션 데이터 확인
        existing_session = CurriculumService.get_user_session(db, user_id, session_number)
        
        if existing_session:
            # 업데이트
            existing_session.session_data = session_data
            existing_session.updated_at = datetime.utcnow()
            
            if mark_completed:
                existing_session.status = SessionStatus.COMPLETED
                existing_session.completed_at = datetime.utcnow()
            else:
                existing_session.status = SessionStatus.IN_PROGRESS
            
            db.commit()
            db.refresh(existing_session)
            return existing_session
        else:
            # 새로 생성
            new_session = UserCurriculumSession(
                user_id=user_id,
                session_number=session_number,
                session_data=session_data,
                status=SessionStatus.COMPLETED if mark_completed else SessionStatus.IN_PROGRESS,
                completed_at=datetime.utcnow() if mark_completed else None
            )
            
            try:
                db.add(new_session)
                db.commit()
                db.refresh(new_session)
                return new_session
            except IntegrityError:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="세션 데이터 저장 중 오류가 발생했습니다"
                )
    
    @staticmethod
    def delete_session_data(db: Session, user_id: int, session_number: int) -> bool:
        """세션 데이터 삭제"""
        session = CurriculumService.get_user_session(db, user_id, session_number)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"세션 {session_number} 데이터를 찾을 수 없습니다"
            )
        
        db.delete(session)
        db.commit()
        return True
    
    @staticmethod
    def get_user_progress(db: Session, user_id: int) -> Dict[str, Any]:
        """사용자 전체 진행 상황 조회"""
        sessions = CurriculumService.get_all_user_sessions(db, user_id)
        
        completed_count = sum(1 for s in sessions if s.status == SessionStatus.COMPLETED)
        total_sessions = 8
        
        # 세션별 진행 상황
        session_progress = []
        for i in range(1, 9):
            session = next((s for s in sessions if s.session_number == i), None)
            session_progress.append({
                "session_number": i,
                "title": SESSION_TITLES.get(i, f"세션 {i}"),
                "status": session.status if session else SessionStatus.NOT_STARTED,
                "completed_at": session.completed_at if session else None
            })
        
        return {
            "total_sessions": total_sessions,
            "completed_sessions": completed_count,
            "progress_percentage": (completed_count / total_sessions) * 100,
            "sessions": session_progress
        }
    
    @staticmethod
    def mark_session_complete(db: Session, user_id: int, session_number: int) -> UserCurriculumSession:
        """세션 완료 처리"""
        session = CurriculumService.get_user_session(db, user_id, session_number)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"세션 {session_number} 데이터를 찾을 수 없습니다"
            )
        
        session.status = SessionStatus.COMPLETED
        session.completed_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(session)
        return session