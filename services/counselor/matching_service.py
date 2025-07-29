from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import and_, or_
from fastapi import HTTPException
from datetime import datetime
import pytz
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
        kst = pytz.timezone('Asia/Seoul')
        consultation = Consultation(
            consultation_code=consultation_code,
            user_nickname=request.nickname,
            character_type_id=character_type.id,
            character_name=character_type.name,
            status=ConsultationStatus.waiting,
            counselor_id=None,  # 아직 배정되지 않음
            created_at=datetime.now(kst)  # 한국 시간으로 저장
        )
        
        db.add(consultation)
        db.commit()
        db.refresh(consultation)
        
        # 모든 사용 가능한 상담사 찾기 (브로드캐스트 방식)
        available_counselors = MatchingService._find_all_available_counselors(db)
        
        if available_counselors:
            logger.info(f"사용 가능한 상담사 {len(available_counselors)}명 찾음")
            
            # 모든 상담사에게 브로드캐스트 요청 생성 및 알림 전송
            broadcast_success = MatchingService._broadcast_consultation_request(
                db, consultation.id, consultation_code, consultation.user_nickname,
                consultation.character_name, available_counselors
            )
            
            if broadcast_success:
                logger.info(f"브로드캐스트 알림 전송 완료: {len(available_counselors)}명에게 전송")
            else:
                logger.warning("브로드캐스트 알림 전송 중 일부 실패")
        else:
            logger.warning(f"사용 가능한 상담사가 없음: 상담={consultation_code}")
            # 사용 가능한 상담사 조건 디버깅
            all_counselors = db.query(Counselor).all()
            for c in all_counselors:
                logger.info(f"상담사 {c.username}: is_active={c.is_active}, is_approved={c.is_approved}, status={c.status}")
        
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
        # 콜대기 상태인 상담사 조회 (동시 상담 수 제한 없음)
        logger.info("사용 가능한 상담사 검색 시작...")
        available_counselors = db.query(Counselor).filter(
            and_(
                Counselor.is_active == True,
                Counselor.is_approved == True,  # 승인된 상담사만
                Counselor.status == CounselorStatus.waiting_for_call  # 콜대기 상태만
            )
        ).all()
        
        logger.info(f"사용 가능한 상담사 수: {len(available_counselors)}")
        
        if not available_counselors:
            return None
        
        # 랜덤하게 상담사 선택 (동시 상담 수 제한 없으므로)
        import random
        return random.choice(available_counselors)
    
    @staticmethod
    def _find_all_available_counselors(db: Session) -> List[Counselor]:
        """
        모든 사용 가능한 상담사 찾기 (브로드캐스트용)
        
        Args:
            db: 데이터베이스 세션
            
        Returns:
            List[Counselor]: 사용 가능한 모든 상담사 목록
        """
        # 콜대기 상태인 모든 상담사 조회 (동시 상담 수 제한 없음)
        available_counselors = db.query(Counselor).filter(
            and_(
                Counselor.is_active == True,
                Counselor.is_approved == True,
                Counselor.status == CounselorStatus.waiting_for_call
            )
        ).all()
        
        logger.info(f"브로드캐스트 대상 상담사 수: {len(available_counselors)}")
        for counselor in available_counselors:
            logger.info(f"  - {counselor.name} (ID: {counselor.id})")
        
        return available_counselors
    
    @staticmethod
    def _broadcast_consultation_request(
        db: Session,
        consultation_id: int,
        consultation_code: str,
        user_nickname: str,
        character_name: str,
        counselors: List[Counselor]
    ) -> bool:
        """
        모든 상담사에게 브로드캐스트 요청 생성 및 알림 전송
        
        Args:
            db: 데이터베이스 세션
            consultation_id: 상담 ID
            consultation_code: 상담 코드
            user_nickname: 사용자 닉네임
            character_name: 캐릭터 이름
            counselors: 대상 상담사 목록
            
        Returns:
            bool: 전체 브로드캐스트 성공 여부
        """
        success_count = 0
        
        for counselor in counselors:
            try:
                # 각 상담사에게 요청 생성
                request = MatchingService._create_consultation_request(
                    db, consultation_id, counselor.id
                )
                logger.info(f"브로드캐스트 요청 생성: 상담사={counselor.name}, 요청ID={request.id}")
                
                # WebSocket 알림 전송
                MatchingService._send_websocket_notification(
                    counselor.id, {
                        "id": consultation_id,
                        "code": consultation_code,
                        "user_nickname": user_nickname,
                        "character_name": character_name,
                        "request_id": request.id
                    }
                )
                success_count += 1
                
            except Exception as e:
                logger.error(f"상담사 {counselor.name}에게 브로드캐스트 실패: {e}")
        
        logger.info(f"브로드캐스트 결과: {success_count}/{len(counselors)} 성공")
        return success_count > 0
    
    @staticmethod
    def _send_websocket_notification(counselor_id: int, notification_data: dict):
        """
        WebSocket 알림 전송 헬퍼 메서드
        
        Args:
            counselor_id: 상담사 ID
            notification_data: 알림 데이터
        """
        try:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                loop.create_task(
                    counselor_manager.send_consultation_request(counselor_id, notification_data)
                )
            else:
                loop.run_until_complete(
                    counselor_manager.send_consultation_request(counselor_id, notification_data)
                )
            logger.info(f"WebSocket 알림 전송 완료: 상담사={counselor_id}")
            
        except Exception as e:
            logger.error(f"WebSocket 알림 전송 실패 (상담사 {counselor_id}): {e}")
    
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
        kst = pytz.timezone('Asia/Seoul')
        request = ConsultationRequest(
            consultation_id=consultation_id,
            counselor_id=counselor_id,
            status="pending",
            requested_at=datetime.now(kst)  # 한국 시간으로 저장
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