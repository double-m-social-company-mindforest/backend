from typing import Dict, List, Optional
from fastapi import WebSocket
import json
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 연결 관리자 (상담사-고객 간 실시간 채팅)"""
    
    def __init__(self):
        # consultation_code -> {'user': List[WebSocket], 'counselor': List[WebSocket]} 매핑
        self.active_connections: Dict[str, Dict[str, List[WebSocket]]] = {}
        # WebSocket -> (consultation_code, user_type) 매핑 (역방향 조회용)
        self.connection_map: Dict[WebSocket, tuple] = {}
        
    async def connect(self, websocket: WebSocket, consultation_code: str, user_type: str = "user"):
        """
        WebSocket 연결 수락 및 관리
        
        Args:
            websocket: WebSocket 인스턴스
            consultation_code: 상담 코드
            user_type: 사용자 유형 ("user" 또는 "counselor")
        """
        await websocket.accept()
        
        # 연결 추가
        if consultation_code not in self.active_connections:
            self.active_connections[consultation_code] = {"user": [], "counselor": []}
        
        self.active_connections[consultation_code][user_type].append(websocket)
        self.connection_map[websocket] = (consultation_code, user_type)
        
        logger.info(f"WebSocket 연결됨: 상담 코드={consultation_code}, 사용자 유형={user_type}")
        
        # 연결 성공 메시지 전송
        await self.send_system_message(
            websocket,
            f"상담이 연결되었습니다. ({user_type})",
            event="connection_established"
        )
    
    async def disconnect(self, websocket: WebSocket):
        """
        WebSocket 연결 해제
        
        Args:
            websocket: WebSocket 인스턴스
        """
        connection_info = self.connection_map.get(websocket)
        
        if connection_info:
            consultation_code, user_type = connection_info
            
            # 연결 제거
            if consultation_code in self.active_connections:
                if user_type in self.active_connections[consultation_code]:
                    self.active_connections[consultation_code][user_type].remove(websocket)
                
                # 빈 리스트 정리
                if (not self.active_connections[consultation_code]["user"] and 
                    not self.active_connections[consultation_code]["counselor"]):
                    del self.active_connections[consultation_code]
            
            # 역방향 매핑 제거
            del self.connection_map[websocket]
            
            logger.info(f"WebSocket 연결 해제: 상담 코드={consultation_code}, 사용자 유형={user_type}")
    
    async def send_personal_message(
        self,
        message: str,
        websocket: WebSocket,
        sender_type: str = "character",
        message_type: str = "text"
    ):
        """
        특정 연결에 메시지 전송
        
        Args:
            message: 메시지 내용
            websocket: WebSocket 인스턴스
            sender_type: 발신자 유형
            message_type: 메시지 유형
        """
        data = {
            "type": "message",
            "data": {
                "sender_type": sender_type,
                "content": message,
                "message_type": message_type,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"메시지 전송 실패: {e}")
            await self.disconnect(websocket)
    
    async def send_to_consultation(
        self,
        consultation_code: str,
        message: str,
        sender_type: str = "counselor",
        message_type: str = "text",
        exclude_websocket: Optional[WebSocket] = None,
        target_user_type: Optional[str] = None
    ):
        """
        특정 상담의 연결에 메시지 브로드캐스트
        
        Args:
            consultation_code: 상담 코드
            message: 메시지 내용
            sender_type: 발신자 유형 (user, counselor)
            message_type: 메시지 유형
            exclude_websocket: 제외할 WebSocket (발신자)
            target_user_type: 특정 사용자 유형에만 전송 (None이면 모든 연결)
        """
        if consultation_code in self.active_connections:
            connections_dict = self.active_connections[consultation_code]
            
            # 전송할 연결 목록 수집
            target_connections = []
            if target_user_type:
                target_connections = connections_dict.get(target_user_type, [])
            else:
                # 모든 연결에 전송
                for user_type_connections in connections_dict.values():
                    target_connections.extend(user_type_connections)
            
            # 동시에 모든 연결에 전송
            tasks = []
            for connection in target_connections:
                if connection != exclude_websocket:
                    task = self.send_personal_message(
                        message=message,
                        websocket=connection,
                        sender_type=sender_type,
                        message_type=message_type
                    )
                    tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def send_typing_status(
        self,
        websocket: WebSocket,
        consultation_code: str,
        is_typing: bool
    ):
        """
        타이핑 상태 전송
        
        Args:
            websocket: 발신자 WebSocket
            consultation_code: 상담 코드
            is_typing: 타이핑 중 여부
        """
        # 발신자 유형 결정
        connection_info = self.connection_map.get(websocket)
        sender_type = "user"
        if connection_info:
            _, user_type = connection_info
            sender_type = user_type
        
        data = {
            "type": "typing",
            "data": {
                "is_typing": is_typing,
                "sender_type": sender_type
            }
        }
        
        if consultation_code in self.active_connections:
            connections_dict = self.active_connections[consultation_code]
            for user_type_connections in connections_dict.values():
                for connection in user_type_connections:
                    if connection != websocket:
                        try:
                            await connection.send_json(data)
                        except Exception as e:
                            logger.error(f"타이핑 상태 전송 실패: {e}")
    
    async def send_system_message(
        self,
        websocket: WebSocket,
        message: str,
        event: Optional[str] = None
    ):
        """
        시스템 메시지 전송
        
        Args:
            websocket: WebSocket 인스턴스
            message: 시스템 메시지
            event: 이벤트 유형
        """
        data = {
            "type": "system",
            "data": {
                "message": message,
                "event": event,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"시스템 메시지 전송 실패: {e}")
    
    def get_consultation_connections(self, consultation_code: str) -> List[WebSocket]:
        """
        특정 상담의 활성 연결 목록 반환
        
        Args:
            consultation_code: 상담 코드
            
        Returns:
            List[WebSocket]: 활성 연결 목록
        """
        connections = []
        if consultation_code in self.active_connections:
            connections_dict = self.active_connections[consultation_code]
            for user_type_connections in connections_dict.values():
                connections.extend(user_type_connections)
        return connections
    
    def is_consultation_active(self, consultation_code: str) -> bool:
        """
        특정 상담에 활성 연결이 있는지 확인
        
        Args:
            consultation_code: 상담 코드
            
        Returns:
            bool: 활성 연결 존재 여부
        """
        if consultation_code not in self.active_connections:
            return False
        
        connections_dict = self.active_connections[consultation_code]
        total_connections = sum(len(connections) for connections in connections_dict.values())
        return total_connections > 0


class CounselorNotificationManager:
    """상담사 알림 WebSocket 관리자"""
    
    def __init__(self):
        # counselor_id -> WebSocket 매핑
        self.counselor_connections: Dict[int, WebSocket] = {}
        # WebSocket -> counselor_id 역방향 매핑
        self.connection_to_counselor: Dict[WebSocket, int] = {}
    
    async def connect(self, websocket: WebSocket, counselor_id: int):
        """상담사 알림 WebSocket 연결"""
        await websocket.accept()
        
        # 기존 연결이 있다면 끊기
        if counselor_id in self.counselor_connections:
            old_websocket = self.counselor_connections[counselor_id]
            await self.disconnect(old_websocket)
        
        self.counselor_connections[counselor_id] = websocket
        self.connection_to_counselor[websocket] = counselor_id
        
        logger.info(f"상담사 알림 WebSocket 연결됨: counselor_id={counselor_id}")
        
        # 연결 성공 메시지
        await websocket.send_json({
            "type": "connection",
            "data": {
                "status": "connected",
                "counselor_id": counselor_id,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        })
    
    async def disconnect(self, websocket: WebSocket):
        """상담사 알림 WebSocket 연결 해제"""
        counselor_id = self.connection_to_counselor.get(websocket)
        
        if counselor_id:
            if counselor_id in self.counselor_connections:
                del self.counselor_connections[counselor_id]
            del self.connection_to_counselor[websocket]
            
            logger.info(f"상담사 알림 WebSocket 연결 해제: counselor_id={counselor_id}")
    
    async def send_consultation_request(self, counselor_id: int, consultation_data: dict):
        """상담사에게 상담 요청 알림 전송"""
        if counselor_id in self.counselor_connections:
            websocket = self.counselor_connections[counselor_id]
            
            data = {
                "type": "consultation_request",
                "data": {
                    "consultation_id": consultation_data.get("id"),
                    "consultation_code": consultation_data.get("code"),
                    "user_nickname": consultation_data.get("user_nickname"),
                    "character_name": consultation_data.get("character_name"),
                    "request_id": consultation_data.get("request_id"),
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "timeout": 30  # 30초 타임아웃
                }
            }
            
            try:
                await websocket.send_json(data)
                logger.info(f"상담 요청 알림 전송 성공: counselor_id={counselor_id}")
                return True
            except Exception as e:
                logger.error(f"상담 요청 알림 전송 실패: {e}")
                await self.disconnect(websocket)
                return False
        
        return False
    
    async def send_heartbeat(self, counselor_id: int):
        """상담사 연결 상태 확인용 heartbeat"""
        if counselor_id in self.counselor_connections:
            websocket = self.counselor_connections[counselor_id]
            
            try:
                await websocket.send_json({
                    "type": "heartbeat",
                    "data": {
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                })
                return True
            except Exception as e:
                logger.error(f"Heartbeat 전송 실패: {e}")
                await self.disconnect(websocket)
                return False
        
        return False
    
    def is_counselor_connected(self, counselor_id: int) -> bool:
        """상담사 WebSocket 연결 상태 확인"""
        return counselor_id in self.counselor_connections


# 전역 연결 관리자 인스턴스
manager = ConnectionManager()
counselor_manager = CounselorNotificationManager()