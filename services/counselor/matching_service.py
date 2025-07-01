from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import and_, or_
from fastapi import HTTPException
from database.models import (
    Counselor, 
    CounselorStatus, 
    Consultation, 
    ConsultationStatus,
    ConsultationRequest,
    FinalType
)
from services.consultation.code_generator import generate_consultation_code
from services.consultation.websocket_manager import counselor_manager
from schemas.consultation import ConsultationStartRequest, ConsultationResponse
import random
import logging
import asyncio

logger = logging.getLogger(__name__)


class MatchingService:
    @staticmethod
    def find_and_assign_counselor(
        db: Session,
        request: ConsultationStartRequest
    ) -> ConsultationResponse:
        """
        상담사를 찾아서 상담 세션을 생성하고 매칭 요청을 보냄
        
        Args:
            db: 데이터베이스 세션
            request: 상담 시작 요청
            
        Returns:
            ConsultationResponse: 생성된 상담 정보
        """
        # 캐릭터 타입 결정 (기존 로직 유지)
        if request.quick_match or not request.character_type_preference:
            character_types = db.query(FinalType).all()
            if not character_types:
                raise HTTPException(status_code=404, detail="사용 가능한 캐릭터가 없습니다")
            character_type = random.choice(character_types)
        else:
            character_type = db.query(FinalType).filter(
                FinalType.id == request.character_type_preference
            ).first()
            if not character_type:
                raise HTTPException(status_code=404, detail="선택한 캐릭터를 찾을 수 없습니다")
        
        # 상담 코드 생성
        consultation_code = generate_consultation_code(db)
        
        # 상담 세션 생성 (상담사 없이)
        consultation = Consultation(
            consultation_code=consultation_code,
            user_nickname=request.nickname,
            character_type_id=character_type.id,
            character_name=character_type.name,
            status=ConsultationStatus.waiting,
            counselor_id=None  # 아직 배정되지 않음
        )
        
        db.add(consultation)
        db.commit()
        db.refresh(consultation)
        
        # 사용 가능한 상담사 찾기
        available_counselor = MatchingService._find_available_counselor(db)
        
        if available_counselor:
            # 상담사에게 매칭 요청 생성
            request = MatchingService._create_consultation_request(
                db, consultation.id, available_counselor.id
            )
            logger.info(f"상담 요청 생성: 상담={consultation_code}, 상담사={available_counselor.name}")
            
            # 상담사에게 실시간 알림 전송 (백그라운드 태스크로 처리)
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(
                    counselor_manager.send_consultation_request(
                        available_counselor.id,
                        {
                            "id": consultation.id,
                            "code": consultation_code,
                            "user_nickname": consultation.user_nickname,
                            "character_name": consultation.character_name,
                            "request_id": request.id
                        }
                    )
                )
            except RuntimeError:
                # 이벤트 루프가 없는 경우 무시 (테스트 환경 등)
                logger.warning("이벤트 루프가 없어 WebSocket 알림을 보낼 수 없습니다")
        else:
            logger.warning(f"사용 가능한 상담사가 없음: 상담={consultation_code}")
        
        # 응답 생성
        response = ConsultationResponse(
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
        
        return response
    
    @staticmethod
    def _find_available_counselor(db: Session) -> Optional[Counselor]:
        """
        사용 가능한 상담사 찾기
        
        Args:
            db: 데이터베이스 세션
            
        Returns:
            Optional[Counselor]: 사용 가능한 상담사 (없으면 None)
        """
        # 현재 활성 상담 수 계산
        subquery = db.query(
            Consultation.counselor_id,
            func.count(Consultation.id).label('active_count')
        ).filter(
            Consultation.status.in_([ConsultationStatus.waiting, ConsultationStatus.active])
        ).group_by(Consultation.counselor_id).subquery()
        
        # 콜대기 상태이고 상담 여유가 있는 상담사 조회
        available_counselors = db.query(Counselor).outerjoin(
            subquery, Counselor.id == subquery.c.counselor_id
        ).filter(
            and_(
                Counselor.is_active == True,
                Counselor.is_approved == True,  # 승인된 상담사만
                Counselor.status == CounselorStatus.waiting_for_call,  # 콜대기 상태만
                or_(
                    subquery.c.active_count < Counselor.max_concurrent_sessions,
                    subquery.c.active_count.is_(None)
                )
            )
        ).all()
        
        if not available_counselors:
            return None
        
        # 상담 수가 적은 상담사 우선 선택 (로드 밸런싱)
        counselor_loads = []
        for counselor in available_counselors:
            active_count = db.query(Consultation).filter(
                and_(
                    Consultation.counselor_id == counselor.id,
                    Consultation.status.in_([ConsultationStatus.waiting, ConsultationStatus.active])
                )
            ).count()
            counselor_loads.append((counselor, active_count))
        
        # 상담 수가 가장 적은 상담사 선택
        counselor_loads.sort(key=lambda x: x[1])
        return counselor_loads[0][0]
    
    @staticmethod
    def _create_consultation_request(
        db: Session, 
        consultation_id: int, 
        counselor_id: int
    ) -> ConsultationRequest:
        """
        상담 요청 생성
        
        Args:
            db: 데이터베이스 세션
            consultation_id: 상담 ID
            counselor_id: 상담사 ID
            
        Returns:
            ConsultationRequest: 생성된 상담 요청
        """
        request = ConsultationRequest(
            consultation_id=consultation_id,
            counselor_id=counselor_id,
            status="pending"
        )
        
        db.add(request)
        db.commit()
        db.refresh(request)
        
        return request
    
    @staticmethod
    def assign_counselor_to_consultation(
        db: Session,
        consultation_id: int,
        counselor_id: int
    ) -> Consultation:
        """
        상담에 상담사 배정
        
        Args:
            db: 데이터베이스 세션
            consultation_id: 상담 ID
            counselor_id: 상담사 ID
            
        Returns:
            Consultation: 업데이트된 상담
        """
        consultation = db.query(Consultation).filter(
            Consultation.id == consultation_id
        ).first()
        
        if not consultation:
            raise HTTPException(status_code=404, detail="상담을 찾을 수 없습니다")
        
        counselor = db.query(Counselor).filter(
            Counselor.id == counselor_id
        ).first()
        
        if not counselor:
            raise HTTPException(status_code=404, detail="상담사를 찾을 수 없습니다")
        
        # 상담사 배정
        consultation.counselor_id = counselor_id
        consultation.status = ConsultationStatus.active
        
        db.commit()
        db.refresh(consultation)
        
        logger.info(f"상담사 배정 완료: 상담={consultation.consultation_code}, 상담사={counselor.name}")
        
        return consultation
    
    @staticmethod
    def reassign_consultation(
        db: Session,
        consultation_code: str
    ) -> Optional[ConsultationResponse]:
        """
        상담을 다른 상담사에게 재배정
        
        Args:
            db: 데이터베이스 세션
            consultation_code: 상담 코드
            
        Returns:
            Optional[ConsultationResponse]: 재배정된 상담 정보
        """
        consultation = db.query(Consultation).filter(
            Consultation.consultation_code == consultation_code
        ).first()
        
        if not consultation:
            raise HTTPException(status_code=404, detail="상담을 찾을 수 없습니다")
        
        # 현재 상담사와 다른 사용 가능한 상담사 찾기
        current_counselor_id = consultation.counselor_id
        available_counselor = MatchingService._find_available_counselor(db)
        
        if available_counselor and available_counselor.id != current_counselor_id:
            # 새로운 상담사에게 요청 생성
            MatchingService._create_consultation_request(
                db, consultation.id, available_counselor.id
            )
            
            logger.info(f"상담 재배정 요청: 상담={consultation_code}, 새 상담사={available_counselor.name}")
            
            # 응답 생성
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
        
        return None