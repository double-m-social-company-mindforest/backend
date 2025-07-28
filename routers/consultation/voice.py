from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import ConsultationMessage, MessageType, Consultation
from services.consultation.voice_service import VoiceService
from services.consultation.voice_call_service import VoiceCallService
import io
import base64
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])


@router.get("/message/{message_id}/download")
async def download_voice_message(
    message_id: int,
    db: Session = Depends(get_db)
):
    """
    음성 메시지 파일 다운로드
    
    Args:
        message_id: 메시지 ID
        db: 데이터베이스 세션
        
    Returns:
        StreamingResponse: 음성 파일 스트림
    """
    try:
        # 음성 메시지 조회
        message = db.query(ConsultationMessage).filter(
            ConsultationMessage.id == message_id,
            ConsultationMessage.message_type == MessageType.voice
        ).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="음성 메시지를 찾을 수 없습니다")
        
        if not message.voice_file_path:
            raise HTTPException(status_code=404, detail="음성 파일이 존재하지 않습니다")
        
        # 파일 데이터 조회
        file_data = VoiceService.get_voice_file_data(message.voice_file_path)
        if not file_data:
            raise HTTPException(status_code=404, detail="음성 파일을 읽을 수 없습니다")
        
        # base64 디코딩
        audio_bytes = base64.b64decode(file_data['data'])
        audio_stream = io.BytesIO(audio_bytes)
        
        # 파일 확장자에 따른 MIME 타입 결정
        extension = file_data['extension'].lower()
        mime_types = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.m4a': 'audio/mp4',
            '.ogg': 'audio/ogg',
            '.webm': 'audio/webm'
        }
        
        media_type = mime_types.get(extension, 'audio/octet-stream')
        
        # 스트리밍 응답 생성
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={file_data['filename']}",
                "Content-Length": str(file_data['size'])
            }
        )
        
    except Exception as e:
        logger.error(f"음성 메시지 다운로드 실패: {e}")
        raise HTTPException(status_code=500, detail="음성 메시지 다운로드 중 오류가 발생했습니다")


@router.get("/message/{message_id}/info")
async def get_voice_message_info(
    message_id: int,
    db: Session = Depends(get_db)
):
    """
    음성 메시지 정보 조회
    
    Args:
        message_id: 메시지 ID
        db: 데이터베이스 세션
        
    Returns:
        Dict: 음성 메시지 정보
    """
    try:
        # 음성 메시지 조회
        message = db.query(ConsultationMessage).filter(
            ConsultationMessage.id == message_id,
            ConsultationMessage.message_type == MessageType.voice
        ).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="음성 메시지를 찾을 수 없습니다")
        
        return {
            "id": message.id,
            "consultation_id": message.consultation_id,
            "sender_type": message.sender_type.value,
            "message": message.message,
            "timestamp": message.timestamp.isoformat(),
            "voice_duration": message.voice_duration,
            "voice_file_size": message.voice_file_size,
            "has_voice_file": bool(message.voice_file_path)
        }
        
    except Exception as e:
        logger.error(f"음성 메시지 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="음성 메시지 정보 조회 중 오류가 발생했습니다")


@router.get("/consultation/{consultation_code}/call-status")
async def get_voice_call_status(
    consultation_code: str,
    db: Session = Depends(get_db)
):
    """
    상담의 음성 통화 상태 조회
    
    Args:
        consultation_code: 상담 코드
        db: 데이터베이스 세션
        
    Returns:
        Dict: 음성 통화 상태
    """
    try:
        # 상담 존재 여부 확인
        consultation = db.query(Consultation).filter(
            Consultation.consultation_code == consultation_code
        ).first()
        
        if not consultation:
            raise HTTPException(status_code=404, detail="상담을 찾을 수 없습니다")
        
        # 음성 통화 상태 조회
        status = VoiceCallService.get_voice_call_status(db, consultation_code)
        if status is None:
            raise HTTPException(status_code=500, detail="음성 통화 상태 조회에 실패했습니다")
        
        # 음성 통화 가능 여부 추가
        status["available"] = VoiceCallService.is_voice_call_available(db, consultation_code)
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"음성 통화 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="음성 통화 상태 조회 중 오류가 발생했습니다")


@router.get("/consultation/{consultation_code}/messages")
async def get_voice_messages(
    consultation_code: str,
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """
    상담의 음성 메시지 목록 조회
    
    Args:
        consultation_code: 상담 코드
        db: 데이터베이스 세션
        limit: 조회할 메시지 수
        offset: 조회 시작 위치
        
    Returns:
        Dict: 음성 메시지 목록
    """
    try:
        # 상담 존재 여부 확인
        consultation = db.query(Consultation).filter(
            Consultation.consultation_code == consultation_code
        ).first()
        
        if not consultation:
            raise HTTPException(status_code=404, detail="상담을 찾을 수 없습니다")
        
        # 음성 메시지 조회
        voice_messages = db.query(ConsultationMessage).filter(
            ConsultationMessage.consultation_id == consultation.id,
            ConsultationMessage.message_type == MessageType.voice
        ).order_by(
            ConsultationMessage.timestamp.desc()
        ).offset(offset).limit(limit).all()
        
        # 결과 포맷팅
        messages = []
        for msg in voice_messages:
            messages.append({
                "id": msg.id,
                "sender_type": msg.sender_type.value,
                "message": msg.message,
                "timestamp": msg.timestamp.isoformat(),
                "voice_duration": msg.voice_duration,
                "voice_file_size": msg.voice_file_size,
                "download_url": f"/api/consultation/voice/message/{msg.id}/download"
            })
        
        return {
            "consultation_code": consultation_code,
            "messages": messages,
            "total_count": len(messages),
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"음성 메시지 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="음성 메시지 목록 조회 중 오류가 발생했습니다")


@router.delete("/message/{message_id}")
async def delete_voice_message(
    message_id: int,
    db: Session = Depends(get_db)
):
    """
    음성 메시지 삭제 (관리용)
    
    Args:
        message_id: 메시지 ID
        db: 데이터베이스 세션
        
    Returns:
        Dict: 삭제 결과
    """
    try:
        # 음성 메시지 조회
        message = db.query(ConsultationMessage).filter(
            ConsultationMessage.id == message_id,
            ConsultationMessage.message_type == MessageType.voice
        ).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="음성 메시지를 찾을 수 없습니다")
        
        # 파일 삭제
        file_deleted = False
        if message.voice_file_path:
            file_deleted = VoiceService.delete_voice_file(message.voice_file_path)
        
        # 데이터베이스에서 메시지 삭제
        db.delete(message)
        db.commit()
        
        logger.info(f"음성 메시지 삭제 완료: ID={message_id}, 파일삭제={file_deleted}")
        
        return {
            "message": "음성 메시지가 삭제되었습니다",
            "message_id": message_id,
            "file_deleted": file_deleted
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"음성 메시지 삭제 실패: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="음성 메시지 삭제 중 오류가 발생했습니다")