from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from fastapi import HTTPException
from database.models import Consultation, ConsultationCard, ConsultationStatus
from schemas.consultation import ConsultationCardCreate, ConsultationCardResponse, ConsultationCardData


class CardService:
    @staticmethod
    def create_consultation_card(
        db: Session,
        consultation_code: str,
        additional_notes: str = ""
    ) -> ConsultationCardResponse:
        """
        상담 카드 생성
        
        Args:
            db: 데이터베이스 세션
            consultation_code: 상담 코드
            additional_notes: 추가 메모
            
        Returns:
            ConsultationCardResponse: 생성된 상담 카드
        """
        # 상담 세션 조회
        consultation = db.query(Consultation).filter(
            Consultation.consultation_code == consultation_code
        ).first()
        
        if not consultation:
            raise HTTPException(status_code=404, detail="상담 세션을 찾을 수 없습니다")
        
        # 완료되지 않은 상담은 카드 발급 불가
        if consultation.status != ConsultationStatus.completed:
            raise HTTPException(status_code=400, detail="완료된 상담만 카드를 발급할 수 있습니다")
        
        # 이미 카드가 발급된 경우 확인
        existing_card = db.query(ConsultationCard).filter(
            ConsultationCard.consultation_id == consultation.id
        ).first()
        
        if existing_card:
            raise HTTPException(status_code=400, detail="이미 상담 카드가 발급되었습니다")
        
        # 캐릭터 정보 가져오기
        character_type = consultation.character_type
        
        # 카드 데이터 생성
        card_data = ConsultationCardData(
            user_nickname=consultation.user_nickname,
            character_type=character_type.name,
            character_name=consultation.character_name,
            character_animal=character_type.animal or "알 수 없음",
            character_group=character_type.group_name or "일반형",
            consultation_code=consultation.consultation_code,
            consultation_date=consultation.created_at.isoformat(),
            hashtags=character_type.hashtags or [],
            additional_notes=additional_notes
        )
        
        # 상담 카드 생성
        consultation_card = ConsultationCard(
            consultation_id=consultation.id,
            card_data=card_data.dict()
        )
        
        db.add(consultation_card)
        
        # 상담에 카드 발급 플래그 설정
        consultation.is_card_issued = True
        
        db.commit()
        db.refresh(consultation_card)
        
        return ConsultationCardResponse(
            id=consultation_card.id,
            consultation_id=consultation_card.consultation_id,
            card_data=card_data,
            issued_at=consultation_card.issued_at
        )
    
    @staticmethod
    def get_consultation_card(
        db: Session,
        consultation_code: str
    ) -> Optional[ConsultationCardResponse]:
        """
        상담 카드 조회
        
        Args:
            db: 데이터베이스 세션
            consultation_code: 상담 코드
            
        Returns:
            ConsultationCardResponse: 상담 카드 (없으면 None)
        """
        # 상담 세션 조회
        consultation = db.query(Consultation).filter(
            Consultation.consultation_code == consultation_code
        ).first()
        
        if not consultation:
            raise HTTPException(status_code=404, detail="상담 세션을 찾을 수 없습니다")
        
        # 상담 카드 조회
        consultation_card = db.query(ConsultationCard).filter(
            ConsultationCard.consultation_id == consultation.id
        ).first()
        
        if not consultation_card:
            return None
        
        # 카드 데이터 파싱
        card_data = ConsultationCardData(**consultation_card.card_data)
        
        return ConsultationCardResponse(
            id=consultation_card.id,
            consultation_id=consultation_card.consultation_id,
            card_data=card_data,
            issued_at=consultation_card.issued_at
        )
    
    @staticmethod
    def update_consultation_card(
        db: Session,
        consultation_code: str,
        additional_notes: str
    ) -> ConsultationCardResponse:
        """
        상담 카드 업데이트 (추가 메모)
        
        Args:
            db: 데이터베이스 세션
            consultation_code: 상담 코드
            additional_notes: 업데이트할 추가 메모
            
        Returns:
            ConsultationCardResponse: 업데이트된 상담 카드
        """
        existing_card = CardService.get_consultation_card(db, consultation_code)
        
        if not existing_card:
            raise HTTPException(status_code=404, detail="상담 카드를 찾을 수 없습니다")
        
        # 카드 데이터 업데이트
        consultation_card = db.query(ConsultationCard).filter(
            ConsultationCard.consultation_id == existing_card.consultation_id
        ).first()
        
        # 카드 데이터에서 추가 메모만 업데이트
        card_data = consultation_card.card_data.copy()
        card_data["additional_notes"] = additional_notes
        consultation_card.card_data = card_data
        
        db.commit()
        db.refresh(consultation_card)
        
        # 업데이트된 카드 데이터 파싱
        updated_card_data = ConsultationCardData(**consultation_card.card_data)
        
        return ConsultationCardResponse(
            id=consultation_card.id,
            consultation_id=consultation_card.consultation_id,
            card_data=updated_card_data,
            issued_at=consultation_card.issued_at
        )