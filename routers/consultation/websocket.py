from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Consultation, ConsultationStatus, SenderType, MessageType
from services.consultation.websocket_manager import manager, counselor_manager
from services.consultation.message_service import MessageService
from services.consultation.character_ai_service import CharacterAIService
from services.consultation.voice_service import VoiceService
from services.consultation.voice_call_service import VoiceCallService
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
                
                elif message_type == "voice_message":
                    # 음성 메시지 처리
                    voice_data = message_content.get("audio_data", "")
                    duration = message_content.get("duration")
                    file_extension = message_content.get("format", ".webm")
                    
                    if voice_data and VoiceService.validate_voice_data(voice_data):
                        try:
                            # 메시지 발신자 유형 결정
                            sender_type = SenderType.user if user_type == "user" else SenderType.counselor
                            
                            # 음성 메시지 저장
                            voice_message = VoiceService.save_voice_message(
                                db=db,
                                consultation_id=consultation.id,
                                sender_type=sender_type,
                                voice_data=voice_data,
                                file_extension=file_extension,
                                duration=duration
                            )
                            
                            # 다른 연결에 음성 메시지 알림 브로드캐스트
                            await manager.send_to_consultation(
                                consultation_code=consultation_code,
                                message=f"음성 메시지 ({duration}초)" if duration else "음성 메시지",
                                sender_type=user_type,
                                message_type="voice",
                                exclude_websocket=websocket,
                                voice_data={
                                    "message_id": voice_message.id,
                                    "duration": duration,
                                    "file_size": voice_message.voice_file_size
                                }
                            )
                            
                            logger.info(f"음성 메시지 처리 완료: 상담={consultation_code}, 길이={duration}초")
                            
                        except Exception as e:
                            logger.error(f"음성 메시지 처리 실패: {e}")
                            await manager.send_system_message(
                                websocket=websocket,
                                message="음성 메시지 처리 중 오류가 발생했습니다.",
                                event="error"
                            )
                    else:
                        await manager.send_system_message(
                            websocket=websocket,
                            message="유효하지 않은 음성 데이터입니다.",
                            event="error"
                        )
                
                elif message_type == "typing":
                    # 타이핑 상태 처리
                    is_typing = message_content.get("is_typing", False)
                    await manager.send_typing_status(
                        websocket=websocket,
                        consultation_code=consultation_code,
                        is_typing=is_typing
                    )
                
                elif message_type == "voice_call_request":
                    # 음성 통화 요청
                    if VoiceCallService.is_voice_call_available(db, consultation_code):
                        await VoiceCallService.notify_voice_call_event(
                            consultation_code=consultation_code,
                            event_type="request",
                            initiator_type=user_type
                        )
                        logger.info(f"음성 통화 요청: 상담={consultation_code}, 요청자={user_type}")
                    else:
                        await manager.send_system_message(
                            websocket=websocket,
                            message="현재 음성 통화를 시작할 수 없습니다.",
                            event="voice_call_unavailable"
                        )
                
                elif message_type == "voice_call_accept":
                    # 음성 통화 수락
                    # 먼저 accept 이벤트를 모든 참가자에게 전송
                    await VoiceCallService.notify_voice_call_event(
                        consultation_code=consultation_code,
                        event_type="accept",
                        initiator_type=user_type
                    )
                    
                    if VoiceCallService.start_voice_call(db, consultation_code, user_type):
                        # WebRTC 세션에 참가자 추가
                        VoiceCallService.add_webrtc_participant(consultation_code, user_type)
                        
                        # 통화 시작 이벤트 전송
                        await VoiceCallService.notify_voice_call_event(
                            consultation_code=consultation_code,
                            event_type="start",
                            initiator_type="system"  # 시스템에서 발생하는 이벤트
                        )
                        logger.info(f"음성 통화 시작: 상담={consultation_code}, 수락자={user_type}")
                    else:
                        await manager.send_system_message(
                            websocket=websocket,
                            message="음성 통화 시작에 실패했습니다.",
                            event="voice_call_start_failed"
                        )
                
                elif message_type == "voice_call_reject":
                    # 음성 통화 거절
                    await VoiceCallService.notify_voice_call_event(
                        consultation_code=consultation_code,
                        event_type="reject",
                        initiator_type=user_type
                    )
                    logger.info(f"음성 통화 거절: 상담={consultation_code}, 거절자={user_type}")
                
                elif message_type == "voice_call_end":
                    # 음성 통화 종료
                    if VoiceCallService.end_voice_call(db, consultation_code, user_type):
                        # WebRTC 세션 정리
                        VoiceCallService.cleanup_webrtc_session(consultation_code)
                        
                        await VoiceCallService.notify_voice_call_event(
                            consultation_code=consultation_code,
                            event_type="end",
                            initiator_type=user_type
                        )
                        logger.info(f"음성 통화 종료: 상담={consultation_code}, 종료자={user_type}")
                    else:
                        await manager.send_system_message(
                            websocket=websocket,
                            message="음성 통화 종료에 실패했습니다.",
                            event="voice_call_end_failed"
                        )
                
                elif message_type == "voice_call_status":
                    # 음성 통화 상태 조회
                    status = VoiceCallService.get_voice_call_status(db, consultation_code)
                    await websocket.send_json({
                        "type": "voice_call_status",
                        "data": status or {"error": "상태 조회 실패"}
                    })
                
                elif message_type == "webrtc_offer":
                    # WebRTC Offer 시그널링
                    offer_data = message_content.get("offer")
                    if offer_data:
                        # WebRTC 세션에 Offer 저장
                        VoiceCallService.store_webrtc_offer(consultation_code, user_type, offer_data)
                        
                        await manager.send_to_consultation(
                            consultation_code=consultation_code,
                            message="WebRTC Offer",
                            sender_type=user_type,
                            message_type="webrtc_offer",
                            exclude_websocket=websocket,
                            voice_data={
                                "offer": offer_data,
                                "sender_type": user_type
                            }
                        )
                        logger.info(f"WebRTC Offer 전달: 상담={consultation_code}, 발신자={user_type}")
                    else:
                        await manager.send_system_message(
                            websocket=websocket,
                            message="유효하지 않은 WebRTC Offer입니다.",
                            event="webrtc_error"
                        )
                
                elif message_type == "webrtc_answer":
                    # WebRTC Answer 시그널링
                    answer_data = message_content.get("answer")
                    if answer_data:
                        # WebRTC 세션에 Answer 저장
                        VoiceCallService.store_webrtc_answer(consultation_code, user_type, answer_data)
                        
                        await manager.send_to_consultation(
                            consultation_code=consultation_code,
                            message="WebRTC Answer",
                            sender_type=user_type,
                            message_type="webrtc_answer",
                            exclude_websocket=websocket,
                            voice_data={
                                "answer": answer_data,
                                "sender_type": user_type
                            }
                        )
                        logger.info(f"WebRTC Answer 전달: 상담={consultation_code}, 발신자={user_type}")
                    else:
                        await manager.send_system_message(
                            websocket=websocket,
                            message="유효하지 않은 WebRTC Answer입니다.",
                            event="webrtc_error"
                        )
                
                elif message_type == "webrtc_ice_candidate":
                    # WebRTC ICE Candidate 시그널링
                    candidate_data = message_content.get("candidate")
                    if candidate_data:
                        # WebRTC 세션에 ICE Candidate 추가
                        VoiceCallService.add_ice_candidate(consultation_code, user_type, candidate_data)
                        
                        await manager.send_to_consultation(
                            consultation_code=consultation_code,
                            message="WebRTC ICE Candidate",
                            sender_type=user_type,
                            message_type="webrtc_ice_candidate",
                            exclude_websocket=websocket,
                            voice_data={
                                "candidate": candidate_data,
                                "sender_type": user_type
                            }
                        )
                        logger.debug(f"WebRTC ICE Candidate 전달: 상담={consultation_code}, 발신자={user_type}")
                    else:
                        logger.warning(f"빈 ICE Candidate 수신: 상담={consultation_code}, 발신자={user_type}")
                
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