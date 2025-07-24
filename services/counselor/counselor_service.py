from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql import func
from sqlalchemy import and_, or_
from fastapi import HTTPException
from database.models import Counselor, CounselorStatus, Consultation, ConsultationStatus, FinalType
from schemas.counselor import (
    CounselorUpdate, 
    CounselorResponse, 
    CounselorListResponse,
    CounselorStatsResponse,
    CounselorStatusUpdate,
    ConsultationHistoryItem,
    ConsultationHistoryResponse
)
from datetime import datetime, timedelta
import math


class CounselorService:
    # create_counselor 메서드 제거됨 - 상담사 등록은 CounselorAuthService.register_counselor 사용
    
    @staticmethod
    def get_counselor(db: Session, counselor_id: int) -> CounselorResponse:
        """
        상담사 정보 조회
        
        Args:
            db: 데이터베이스 세션
            counselor_id: 상담사 ID
            
        Returns:
            CounselorResponse: 상담사 정보
        """
        counselor = db.query(Counselor).filter(Counselor.id == counselor_id).first()
        if not counselor:
            raise HTTPException(status_code=404, detail="상담사를 찾을 수 없습니다")
        
        return CounselorResponse.from_orm(counselor)
    
    @staticmethod
    def update_counselor(
        db: Session, 
        counselor_id: int, 
        counselor_data: CounselorUpdate
    ) -> CounselorResponse:
        """
        상담사 정보 업데이트
        
        Args:
            db: 데이터베이스 세션
            counselor_id: 상담사 ID
            counselor_data: 업데이트할 정보
            
        Returns:
            CounselorResponse: 업데이트된 상담사 정보
        """
        counselor = db.query(Counselor).filter(Counselor.id == counselor_id).first()
        if not counselor:
            raise HTTPException(status_code=404, detail="상담사를 찾을 수 없습니다")
        
        update_data = counselor_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(counselor, field, value)
        
        db.commit()
        db.refresh(counselor)
        
        return CounselorResponse.from_orm(counselor)
    
    @staticmethod
    def update_counselor_status(
        db: Session, 
        counselor_id: int, 
        status_data: CounselorStatusUpdate
    ) -> CounselorResponse:
        """
        상담사 상태 업데이트
        
        Args:
            db: 데이터베이스 세션
            counselor_id: 상담사 ID
            status_data: 상태 정보
            
        Returns:
            CounselorResponse: 업데이트된 상담사 정보
        """
        counselor = db.query(Counselor).filter(Counselor.id == counselor_id).first()
        if not counselor:
            raise HTTPException(status_code=404, detail="상담사를 찾을 수 없습니다")
        
        counselor.status = status_data.status
        counselor.last_active_at = func.now()
        
        db.commit()
        db.refresh(counselor)
        
        return CounselorResponse.from_orm(counselor)
    
    @staticmethod
    def get_counselors(
        db: Session,
        status: Optional[CounselorStatus] = None,
        specialties: Optional[List[str]] = None,
        is_active: Optional[bool] = None,
        available_only: bool = False
    ) -> CounselorListResponse:
        """
        상담사 목록 조회
        
        Args:
            db: 데이터베이스 세션
            status: 상태 필터
            specialties: 전문분야 필터
            is_active: 활성 상태 필터
            available_only: 상담 가능한 상담사만 조회
            
        Returns:
            CounselorListResponse: 상담사 목록과 통계
        """
        query = db.query(Counselor)
        
        # 필터 적용
        if status:
            query = query.filter(Counselor.status == status)
        
        if is_active is not None:
            query = query.filter(Counselor.is_active == is_active)
        
        if specialties:
            # JSON 배열에서 전문분야 검색
            conditions = [Counselor.specialties.contains([specialty]) for specialty in specialties]
            query = query.filter(or_(*conditions))
        
        if available_only:
            # 온라인이고 현재 상담 수가 최대치보다 적은 상담사
            subquery = db.query(
                Consultation.counselor_id,
                func.count(Consultation.id).label('active_count')
            ).filter(
                Consultation.status.in_([ConsultationStatus.waiting, ConsultationStatus.active])
            ).group_by(Consultation.counselor_id).subquery()
            
            query = query.outerjoin(subquery, Counselor.id == subquery.c.counselor_id).filter(
                and_(
                    Counselor.status.in_([CounselorStatus.online, CounselorStatus.waiting_for_call]),
                    or_(
                        subquery.c.active_count < Counselor.max_concurrent_sessions,
                        subquery.c.active_count.is_(None)
                    )
                )
            )
        
        counselors = query.all()
        
        # 통계 계산
        total_count = len(counselors)
        online_count = len([c for c in counselors if c.status == CounselorStatus.online])
        
        # 실제로 상담 가능한 상담사 수 계산
        available_counselors = CounselorService._get_available_counselors(db)
        available_count = len(available_counselors)
        
        counselor_responses = [CounselorResponse.from_orm(c) for c in counselors]
        
        return CounselorListResponse(
            counselors=counselor_responses,
            total_count=total_count,
            online_count=online_count,
            available_count=available_count
        )
    
    @staticmethod
    def _get_available_counselors(db: Session) -> List[Counselor]:
        """
        현재 상담 가능한 상담사 목록 반환
        
        Args:
            db: 데이터베이스 세션
            
        Returns:
            List[Counselor]: 상담 가능한 상담사 목록
        """
        # 현재 활성 상담 수 계산
        subquery = db.query(
            Consultation.counselor_id,
            func.count(Consultation.id).label('active_count')
        ).filter(
            Consultation.status.in_([ConsultationStatus.waiting, ConsultationStatus.active])
        ).group_by(Consultation.counselor_id).subquery()
        
        # 온라인이고 상담 여유가 있는 상담사
        available_counselors = db.query(Counselor).outerjoin(
            subquery, Counselor.id == subquery.c.counselor_id
        ).filter(
            and_(
                Counselor.is_active == True,
                Counselor.status == CounselorStatus.online,
                or_(
                    subquery.c.active_count < Counselor.max_concurrent_sessions,
                    subquery.c.active_count.is_(None)
                )
            )
        ).all()
        
        return available_counselors
    
    @staticmethod
    def get_counselor_stats(db: Session, counselor_id: int) -> CounselorStatsResponse:
        """
        상담사 통계 조회
        
        Args:
            db: 데이터베이스 세션
            counselor_id: 상담사 ID
            
        Returns:
            CounselorStatsResponse: 상담사 통계
        """
        counselor = db.query(Counselor).filter(Counselor.id == counselor_id).first()
        if not counselor:
            raise HTTPException(status_code=404, detail="상담사를 찾을 수 없습니다")
        
        # 총 상담 수
        total_consultations = db.query(Consultation).filter(
            Consultation.counselor_id == counselor_id
        ).count()
        
        # 현재 활성 상담 수
        active_consultations = db.query(Consultation).filter(
            and_(
                Consultation.counselor_id == counselor_id,
                Consultation.status.in_([ConsultationStatus.waiting, ConsultationStatus.active])
            )
        ).count()
        
        # 완료된 상담의 평균 시간 계산
        completed_consultations = db.query(Consultation).filter(
            and_(
                Consultation.counselor_id == counselor_id,
                Consultation.status == ConsultationStatus.completed,
                Consultation.completed_at.is_not(None)
            )
        ).all()
        
        avg_duration = None
        if completed_consultations:
            durations = []
            for consultation in completed_consultations:
                if consultation.completed_at and consultation.created_at:
                    duration = (consultation.completed_at - consultation.created_at).total_seconds() / 60
                    durations.append(duration)
            
            if durations:
                avg_duration = sum(durations) / len(durations)
        
        # 마지막 상담 시간
        last_consultation = db.query(Consultation).filter(
            Consultation.counselor_id == counselor_id
        ).order_by(Consultation.created_at.desc()).first()
        
        last_consultation_at = last_consultation.created_at if last_consultation else None
        
        return CounselorStatsResponse(
            counselor_id=counselor_id,
            total_consultations=total_consultations,
            active_consultations=active_consultations,
            avg_session_duration=avg_duration,
            rating=None,  # 향후 구현
            last_consultation_at=last_consultation_at
        )
    
    @staticmethod
    def get_consultation_history(
        db: Session, 
        counselor_id: int,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None
    ) -> ConsultationHistoryResponse:
        """
        상담사의 상담 이력 조회
        
        Args:
            db: 데이터베이스 세션
            counselor_id: 상담사 ID
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지 크기
            status_filter: 상태 필터 (optional)
            
        Returns:
            ConsultationHistoryResponse: 상담 이력 목록
        """
        # 상담사 확인
        counselor = db.query(Counselor).filter(Counselor.id == counselor_id).first()
        if not counselor:
            raise HTTPException(status_code=404, detail="상담사를 찾을 수 없습니다")
        
        # 기본 쿼리
        query = db.query(Consultation).options(
            joinedload(Consultation.character_type)
        ).filter(
            Consultation.counselor_id == counselor_id
        )
        
        # 상태 필터 적용
        if status_filter:
            query = query.filter(Consultation.status == status_filter)
        
        # 전체 개수
        total_count = query.count()
        
        # 페이지네이션
        offset = (page - 1) * page_size
        consultations = query.order_by(
            Consultation.created_at.desc()
        ).offset(offset).limit(page_size).all()
        
        # 상태 한글 매핑
        status_display_map = {
            ConsultationStatus.completed: "완료",
            ConsultationStatus.terminated: "중단",
            ConsultationStatus.active: "진행중",
            ConsultationStatus.waiting: "대기중"
        }
        
        # 응답 데이터 구성
        consultation_items = []
        for consultation in consultations:
            # 상담 시간 계산
            duration_minutes = None
            end_time = None
            
            if consultation.completed_at:
                duration_minutes = int((consultation.completed_at - consultation.created_at).total_seconds() / 60)
                end_time = consultation.completed_at.strftime("%H:%M")
            
            consultation_items.append(ConsultationHistoryItem(
                consultation_id=consultation.id,
                consultation_code=consultation.consultation_code,
                user_nickname=consultation.user_nickname,
                character_type=consultation.character_type.name if consultation.character_type else "알 수 없음",
                consultation_date=consultation.created_at.strftime("%Y-%m-%d"),
                start_time=consultation.created_at.strftime("%H:%M"),
                end_time=end_time,
                duration_minutes=duration_minutes,
                status=consultation.status,
                status_display=status_display_map.get(consultation.status, consultation.status)
            ))
        
        # 전체 페이지 수 계산
        total_pages = math.ceil(total_count / page_size)
        
        return ConsultationHistoryResponse(
            consultations=consultation_items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )