from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Consultation, ConsultationStatus, SenderType, MessageType
from services.consultation.websocket_manager import manager, counselor_manager
from services.consultation.message_service import MessageService
from services.consultation.character_ai_service import CharacterAIService
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db_for_websocket():
    """WebSocket용 데이터베이스 세션 생성"""
    from database.connection import SessionLocal
    return SessionLocal()


@router.websocket("/ws/consultation/{consultation_code}")
async def websocket_endpoint(
    websocket: WebSocket,
    consultation_code: str,
    user_type: str = "user"  # "user" 또는 "counselor"
):
    """
    실시간 상담 WebSocket 엔드포인트
    
    Args:
        websocket: WebSocket 연결
        consultation_code: 9자리 상담 코드
    """
    db = get_db_for_websocket()
    
    try:
        # 상담 존재 여부 확인
        consultation = db.query(Consultation).filter(
            Consultation.consultation_code == consultation_code
        ).first()
        
        if not consultation:
            logger.error(f"상담 코드를 찾을 수 없음: {consultation_code}")
            await websocket.close(code=4004, reason="상담 코드를 찾을 수 없습니다")
            return
        
        # 종료된 상담 확인
        if consultation.status == ConsultationStatus.terminated:
            logger.warning(f"종료된 상담 접근 시도: {consultation_code}")
            await websocket.close(code=4003, reason="종료된 상담입니다")
            return
        
        logger.info(f"WebSocket 연결 시도: 상담={consultation_code}, 유형={user_type}, 상태={consultation.status}")
        
        # WebSocket 연결 수락
        await manager.connect(websocket, consultation_code, user_type)
        
        # 상담 상태를 active로 변경 (상담사가 연결될 때만)
        if user_type == "counselor" and consultation.status == ConsultationStatus.waiting:
            consultation.status = ConsultationStatus.active
            db.commit()
            db.refresh(consultation)
            
            # 상담 시작 알림 전송
            await manager.send_to_consultation(
                consultation_code=consultation_code,
                message="상담사가 연결되었습니다. 상담을 시작합니다.",
                sender_type="system",
                message_type="system"
            )
        
        # 상담이 배정되지 않은 경우 (고객이 먼저 연결된 경우)
        if user_type == "user" and not consultation.counselor_id:
            await manager.send_personal_message(
                message="상담사 배정을 기다리고 있습니다. 잠시만 기다려 주세요.",
                websocket=websocket,
                sender_type="system",
                message_type="system"
            )
        
        # 메시지 수신 루프
        while True:
            try:
                # 클라이언트 메시지 수신
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                message_type = message_data.get("type")
                message_content = message_data.get("data", {})
                
                if message_type == "message":
                    # 텍스트 메시지 처리
                    user_message = message_content.get("content", "")
                    
                    if user_message.strip():
                        # 메시지 발신자 유형 결정
                        sender_type = SenderType.user if user_type == "user" else SenderType.counselor
                        
                        # 메시지 저장
                        MessageService.create_message(
                            db=db,
                            consultation_id=consultation.id,
                            sender_type=sender_type,
                            message=user_message,
                            message_type=MessageType.text
                        )
                        
                        # 다른 연결에 메시지 브로드캐스트 (발신자 제외)
                        await manager.send_to_consultation(
                            consultation_code=consultation_code,
                            message=user_message,
                            sender_type=user_type,
                            message_type="text",
                            exclude_websocket=websocket
                        )
                
                elif message_type == "typing":
                    # 타이핑 상태 처리
                    is_typing = message_content.get("is_typing", False)
                    await manager.send_typing_status(
                        websocket=websocket,
                        consultation_code=consultation_code,
                        is_typing=is_typing
                    )
                
                elif message_type == "ping":
                    # 연결 상태 확인 (heartbeat)
                    await websocket.send_json({"type": "pong", "data": {}})
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await manager.send_system_message(
                    websocket=websocket,
                    message="잘못된 메시지 형식입니다.",
                    event="error"
                )
            except Exception as e:
                logger.error(f"WebSocket 메시지 처리 중 오류: {e}")
                await manager.send_system_message(
                    websocket=websocket,
                    message="메시지 처리 중 오류가 발생했습니다.",
                    event="error"
                )
    
    except Exception as e:
        logger.error(f"WebSocket 연결 중 오류: {e}")
    
    finally:
        # 연결 정리
        await manager.disconnect(websocket)
        db.close()


@router.websocket("/ws/counselor/{counselor_id}/notifications")
async def counselor_notification_websocket(
    websocket: WebSocket,
    counselor_id: int
):
    """
    상담사 알림 WebSocket 엔드포인트
    
    상담사가 콜대기 중일 때 실시간으로 상담 요청을 받기 위한 WebSocket
    """
    try:
        # WebSocket 연결
        await counselor_manager.connect(websocket, counselor_id)
        logger.info(f"상담사 알림 WebSocket 연결: counselor_id={counselor_id}")
        
        # 메시지 수신 루프
        while True:
            try:
                # 클라이언트 메시지 수신
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                message_type = message_data.get("type")
                
                if message_type == "heartbeat":
                    # Heartbeat 응답
                    await websocket.send_json({
                        "type": "heartbeat_ack",
                        "data": {"status": "alive"}
                    })
                elif message_type == "status_update":
                    # 상태 업데이트 처리 (필요시)
                    status = message_data.get("data", {}).get("status")
                    logger.info(f"상담사 상태 업데이트: counselor_id={counselor_id}, status={status}")
                
            except WebSocketDisconnect:
                logger.info(f"상담사 알림 WebSocket 연결 종료: counselor_id={counselor_id}")
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "잘못된 메시지 형식입니다."}
                })
            except Exception as e:
                logger.error(f"상담사 알림 WebSocket 오류: {e}")
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "메시지 처리 중 오류가 발생했습니다."}
                })
    
    except Exception as e:
        logger.error(f"상담사 알림 WebSocket 연결 중 오류: {e}")
    
    finally:
        # 연결 정리
        await counselor_manager.disconnect(websocket)


# AI 자동 응답 기능 제거 - 실제 상담사가 직접 응답