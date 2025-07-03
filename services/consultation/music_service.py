import httpx
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException
from database.models import Consultation, ConsultationMessage
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class MusicService:
    
    @staticmethod
    async def get_music_recommendations(
        db: Session,
        consultation_code: str,
        take: int = 3
    ) -> Dict[str, Any]:
        """
        상담 중 최근 대화 기반 음원 추천
        
        Args:
            db: Database session
            consultation_code: 9자리 상담 코드
            take: 추천받을 음원 수 (1-10)
            
        Returns:
            음원 추천 결과
        """
        # 1. 상담 존재 여부 및 상태 확인
        consultation = db.query(Consultation).filter(
            Consultation.consultation_code == consultation_code
        ).first()
        
        if not consultation:
            raise HTTPException(status_code=404, detail="상담을 찾을 수 없습니다")
        
        if consultation.status not in ["active", "waiting"]:
            raise HTTPException(
                status_code=400,
                detail="진행 중인 상담만 음원 추천이 가능합니다"
            )
        
        # 2. 최근 메시지 추출 (1000자 이하)
        recent_text = MusicService._extract_recent_messages(db, consultation.id)
        
        if len(recent_text) < 10:
            raise HTTPException(
                status_code=400,
                detail="충분한 대화 내용이 없습니다. 대화를 더 진행해주세요."
            )
        
        # 3. Link Music API 호출
        try:
            music_data = await MusicService._call_link_music_api(recent_text, take)
        except httpx.HTTPStatusError as e:
            logger.error(f"Link Music API error: {e}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"음원 추천 API 오류: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Unexpected error calling Link Music API: {e}")
            raise HTTPException(
                status_code=500,
                detail="음원 추천 서비스에 연결할 수 없습니다"
            )
        
        # 4. 응답 포맷팅
        return {
            "consultation_code": consultation_code,
            "analyzed_text_length": len(recent_text),
            "recommendations": music_data.get("musics", []),
            "total_recommendations": len(music_data.get("musics", []))
        }
    
    @staticmethod
    def _extract_recent_messages(db: Session, consultation_id: int) -> str:
        """
        최근 메시지에서 1000자 이하 텍스트 추출
        
        Args:
            db: Database session
            consultation_id: 상담 ID
            
        Returns:
            최근 메시지 텍스트 (최대 1000자)
        """
        # 최신 메시지부터 역순으로 조회
        messages = db.query(ConsultationMessage)\
            .filter(ConsultationMessage.consultation_id == consultation_id)\
            .order_by(desc(ConsultationMessage.timestamp))\
            .all()
        
        combined_text = ""
        
        for message in messages:
            # 시스템 메시지 제외, 텍스트 메시지만 포함
            if message.message_type == "text" and message.message:
                # 새 메시지를 앞에 추가 (최신 메시지가 앞에 오도록)
                new_text = message.message + " " + combined_text
                
                # 1000자 초과 시 중단
                if len(new_text) > 1000:
                    # 정확히 1000자로 자르기
                    remaining_chars = 1000 - len(combined_text) - 1  # 공백 고려
                    if remaining_chars > 0:
                        combined_text = message.message[:remaining_chars] + " " + combined_text
                    break
                
                combined_text = new_text
        
        # 최종적으로 1000자 초과 시 자르기
        final_text = combined_text.strip()
        if len(final_text) > 1000:
            final_text = final_text[:1000]
        
        return final_text
    
    @staticmethod
    async def _call_link_music_api(text_input: str, take: int) -> Dict[str, Any]:
        """
        Link Music API 호출
        
        Args:
            text_input: 분석할 텍스트
            take: 추천받을 음원 수
            
        Returns:
            API 응답 데이터
        """
        headers = {
            "Authorization": f"Bearer {settings.API_KEY}",
            "Content-Type": "application/x-www-form-urlencoded",
            "accept": "*/*"
        }
        
        data = {
            "message": text_input,  # API expects 'message' field, not 'text_input'
            "take": str(take)  # API expects string
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api-prod.linkmusic.io/v2/analyze/text",
                headers=headers,
                data=data
            )
            
            response.raise_for_status()
            return response.json()