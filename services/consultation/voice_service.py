import os
import base64
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from database.models import ConsultationMessage, MessageType, SenderType
import logging

logger = logging.getLogger(__name__)

class VoiceService:
    """음성 메시지 처리 서비스"""
    
    # 음성 파일 저장 디렉토리
    VOICE_FILES_DIR = Path("voice_files")
    
    # 지원되는 음성 포맷
    SUPPORTED_FORMATS = ['.wav', '.mp3', '.m4a', '.ogg', '.webm']
    
    # 최대 파일 크기 (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    @classmethod
    def initialize_storage(cls):
        """음성 파일 저장 디렉토리 초기화"""
        cls.VOICE_FILES_DIR.mkdir(exist_ok=True)
        logger.info(f"음성 파일 저장 디렉토리 초기화: {cls.VOICE_FILES_DIR}")
    
    @staticmethod
    def save_voice_message(
        db: Session,
        consultation_id: int,
        sender_type: SenderType,
        voice_data: str,  # base64 encoded audio data
        file_extension: str = '.webm',
        duration: Optional[int] = None
    ) -> ConsultationMessage:
        """
        음성 메시지 저장
        
        Args:
            db: 데이터베이스 세션
            consultation_id: 상담 ID
            sender_type: 발신자 타입
            voice_data: base64 인코딩된 음성 데이터
            file_extension: 파일 확장자
            duration: 음성 길이 (초)
            
        Returns:
            ConsultationMessage: 저장된 메시지
        """
        try:
            # 저장 디렉토리 확인
            VoiceService.initialize_storage()
            
            # base64 디코딩
            audio_bytes = base64.b64decode(voice_data)
            file_size = len(audio_bytes)
            
            # 파일 크기 검증
            if file_size > VoiceService.MAX_FILE_SIZE:
                raise ValueError(f"파일 크기가 너무 큽니다: {file_size} bytes")
            
            # 고유 파일명 생성
            file_id = str(uuid.uuid4())
            filename = f"{file_id}{file_extension}"
            file_path = VoiceService.VOICE_FILES_DIR / filename
            
            # 파일 저장
            with open(file_path, 'wb') as f:
                f.write(audio_bytes)
            
            # 데이터베이스에 메시지 저장
            message = ConsultationMessage(
                consultation_id=consultation_id,
                sender_type=sender_type,
                message=f"음성 메시지 ({duration}초)" if duration else "음성 메시지",
                message_type=MessageType.voice,
                voice_file_path=str(file_path),
                voice_duration=duration,
                voice_file_size=file_size
            )
            
            db.add(message)
            db.commit()
            db.refresh(message)
            
            logger.info(f"음성 메시지 저장 완료: {filename}, 크기: {file_size} bytes")
            return message
            
        except Exception as e:
            logger.error(f"음성 메시지 저장 실패: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_voice_file_data(file_path: str) -> Optional[Dict[str, Any]]:
        """
        음성 파일 데이터 조회
        
        Args:
            file_path: 파일 경로
            
        Returns:
            Dict: 파일 정보와 base64 데이터
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"음성 파일을 찾을 수 없음: {file_path}")
                return None
            
            with open(path, 'rb') as f:
                audio_bytes = f.read()
            
            # base64 인코딩
            audio_data = base64.b64encode(audio_bytes).decode('utf-8')
            
            return {
                'data': audio_data,
                'size': len(audio_bytes),
                'filename': path.name,
                'extension': path.suffix
            }
            
        except Exception as e:
            logger.error(f"음성 파일 읽기 실패: {e}")
            return None
    
    @staticmethod
    def delete_voice_file(file_path: str) -> bool:
        """
        음성 파일 삭제
        
        Args:
            file_path: 파일 경로
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"음성 파일 삭제 완료: {file_path}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"음성 파일 삭제 실패: {e}")
            return False
    
    @staticmethod
    def validate_voice_data(voice_data: str, max_size: int = None) -> bool:
        """
        음성 데이터 유효성 검증
        
        Args:
            voice_data: base64 인코딩된 음성 데이터
            max_size: 최대 파일 크기
            
        Returns:
            bool: 유효성 검증 결과
        """
        try:
            # base64 디코딩 테스트
            audio_bytes = base64.b64decode(voice_data)
            file_size = len(audio_bytes)
            
            # 크기 검증
            max_allowed = max_size or VoiceService.MAX_FILE_SIZE
            if file_size > max_allowed:
                logger.warning(f"파일 크기 초과: {file_size} > {max_allowed}")
                return False
            
            # 최소 크기 검증 (100 bytes)
            if file_size < 100:
                logger.warning(f"파일 크기가 너무 작음: {file_size}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"음성 데이터 검증 실패: {e}")
            return False

# 초기화
VoiceService.initialize_storage()