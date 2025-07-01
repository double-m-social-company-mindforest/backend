from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from fastapi import HTTPException
from database.models import Consultation, ConsultationStatus, FinalType
from schemas.consultation import ConsultationStartRequest, ConsultationResponse
from .code_generator import generate_consultation_code
import random


class ConsultationService:
    @staticmethod
    def start_consultation(
        db: Session,
        request: ConsultationStartRequest
    ) -> ConsultationResponse:
        """
        새로운 상담 세션 시작 (실제 상담사 매칭)
        
        Args:
            db: 데이터베이스 세션
            request: 상담 시작 요청 정보
            
        Returns:
            ConsultationResponse: 생성된 상담 정보
        """
        # 실제 상담사 매칭 서비스 사용
        from services.counselor.matching_service import MatchingService
        return MatchingService.find_and_assign_counselor(db, request)
    
    @staticmethod
    def get_consultation(db: Session, consultation_code: str) -> ConsultationResponse:
        """
        상담 세션 정보 조회
        
        Args:
            db: 데이터베이스 세션
            consultation_code: 상담 코드
            
        Returns:
            ConsultationResponse: 상담 정보
        """
        consultation = db.query(Consultation).filter(
            Consultation.consultation_code == consultation_code
        ).first()
        
        if not consultation:
            raise HTTPException(status_code=404, detail="상담 세션을 찾을 수 없습니다")
        
        character_type = consultation.character_type
        
        return ConsultationResponse(
            id=consultation.id,
            consultation_code=consultation.consultation_code,
            user_nickname=consultation.user_nickname,
            character_type_id=consultation.character_type_id,
            character_name=consultation.character_name,
            character_animal=character_type.animal,
            character_group=character_type.group_name,
            status=consultation.status,
            created_at=consultation.created_at,
            completed_at=consultation.completed_at,
            is_card_issued=consultation.is_card_issued
        )
    
    @staticmethod
    def reconnect_consultation(
        db: Session,
        consultation_code: str,
        nickname: Optional[str] = None
    ) -> ConsultationResponse:
        """
        기존 상담 세션 재연결
        
        Args:
            db: 데이터베이스 세션
            consultation_code: 상담 코드
            nickname: 변경할 닉네임 (선택사항)
            
        Returns:
            ConsultationResponse: 상담 정보
        """
        consultation = db.query(Consultation).filter(
            Consultation.consultation_code == consultation_code
        ).first()
        
        if not consultation:
            raise HTTPException(status_code=404, detail="상담 세션을 찾을 수 없습니다")
        
        # 종료된 상담은 재연결 불가
        if consultation.status == ConsultationStatus.terminated:
            raise HTTPException(status_code=400, detail="종료된 상담은 재연결할 수 없습니다")
        
        # 닉네임 변경 (선택사항)
        if nickname:
            consultation.user_nickname = nickname
        
        # 상태를 active로 변경
        if consultation.status == ConsultationStatus.waiting:
            consultation.status = ConsultationStatus.active
        
        db.commit()
        db.refresh(consultation)
        
        return ConsultationService.get_consultation(db, consultation_code)
    
    @staticmethod
    def end_consultation(
        db: Session,
        consultation_code: str
    ) -> dict:
        """
        상담 종료
        
        Args:
            db: 데이터베이스 세션
            consultation_code: 상담 코드
            
        Returns:
            dict: 종료 결과
        """
        consultation = db.query(Consultation).filter(
            Consultation.consultation_code == consultation_code
        ).first()
        
        if not consultation:
            raise HTTPException(status_code=404, detail="상담 세션을 찾을 수 없습니다")
        
        if consultation.status in [ConsultationStatus.completed, ConsultationStatus.terminated]:
            raise HTTPException(status_code=400, detail="이미 종료된 상담입니다")
        
        # 상담 종료 처리
        consultation.status = ConsultationStatus.completed
        consultation.completed_at = func.now()
        
        db.commit()
        db.refresh(consultation)
        
        return {
            "consultation_code": consultation.consultation_code,
            "status": consultation.status,
            "completed_at": consultation.completed_at,
            "message": "상담이 정상적으로 종료되었습니다"
        }