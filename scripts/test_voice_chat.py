#!/usr/bin/env python3
"""
음성채팅 기능 테스트 스크립트

이 스크립트는 다음 기능들을 테스트합니다:
1. 음성 메시지 저장 및 조회
2. 음성 통화 상태 관리
3. WebSocket 음성 메시지 처리
4. API 엔드포인트 테스트
"""

import sys
import os
import asyncio
import json
import base64
import websockets
import requests
from pathlib import Path
from datetime import datetime
import pytz

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection import SessionLocal
from database.models import Consultation, ConsultationStatus, FinalType, ConsultationMessage, MessageType, SenderType
from services.consultation.voice_service import VoiceService
from services.consultation.voice_call_service import VoiceCallService
from services.consultation.code_generator import generate_consultation_code


class VoiceChatTester:
    """음성채팅 기능 테스트 클래스"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws")
        self.db = SessionLocal()
        self.test_consultation_code = None
        
    def cleanup(self):
        """테스트 후 정리"""
        if self.db:
            self.db.close()
    
    def create_test_consultation(self) -> str:
        """테스트용 상담 생성"""
        try:
            # 첫 번째 캐릭터 타입 조회
            character_type = self.db.query(FinalType).first()
            if not character_type:
                print("❌ 캐릭터 타입이 없습니다. 먼저 데이터를 설정하세요.")
                return None
            
            # 첫 번째 활성 상담사 조회
            from database.models import Counselor
            counselor = self.db.query(Counselor).filter(
                Counselor.is_active == True,
                Counselor.is_approved == True
            ).first()
            
            if not counselor:
                print("❌ 활성 상담사가 없습니다. 먼저 상담사를 등록하세요.")
                return None
            
            # 상담 코드 생성
            consultation_code = generate_consultation_code(self.db)
            
            # 테스트 상담 생성  
            kst = pytz.timezone('Asia/Seoul')
            consultation = Consultation(
                consultation_code=consultation_code,
                user_nickname="테스트 사용자",
                character_type_id=character_type.id,
                character_name=character_type.name,
                status=ConsultationStatus.active,  # 바로 활성 상태로 설정
                counselor_id=counselor.id,  # 실제 존재하는 상담사 ID 사용
                created_at=datetime.now(kst)  # 한국 시간으로 저장
            )
            
            self.db.add(consultation)
            self.db.commit()
            self.db.refresh(consultation)
            
            print(f"✅ 테스트 상담 생성: {consultation_code}")
            return consultation_code
            
        except Exception as e:
            print(f"❌ 테스트 상담 생성 실패: {e}")
            self.db.rollback()
            return None
    
    def generate_sample_audio_data(self) -> str:
        """샘플 오디오 데이터 생성 (base64)"""
        # 간단한 더미 오디오 데이터 (실제로는 실제 오디오 파일을 사용해야 함)
        dummy_audio = b"RIFF" + b"\x00" * 100  # 최소한의 WAV 헤더 형태
        return base64.b64encode(dummy_audio).decode('utf-8')
    
    def test_voice_service(self):
        """음성 서비스 테스트"""
        print("\n🎵 음성 서비스 테스트 시작...")
        
        if not self.test_consultation_code:
            self.test_consultation_code = self.create_test_consultation()
            if not self.test_consultation_code:
                return False
        
        try:
            # 상담 조회
            consultation = self.db.query(Consultation).filter(
                Consultation.consultation_code == self.test_consultation_code
            ).first()
            
            if not consultation:
                print("❌ 테스트 상담을 찾을 수 없습니다.")
                return False
            
            # 1. 음성 메시지 저장 테스트
            print("1️⃣ 음성 메시지 저장 테스트...")
            sample_audio = self.generate_sample_audio_data()
            
            voice_message = VoiceService.save_voice_message(
                db=self.db,
                consultation_id=consultation.id,
                sender_type=SenderType.user,
                voice_data=sample_audio,
                file_extension=".wav",
                duration=15
            )
            
            if voice_message:
                print(f"✅ 음성 메시지 저장 성공: ID={voice_message.id}")
            else:
                print("❌ 음성 메시지 저장 실패")
                return False
            
            # 2. 음성 파일 데이터 조회 테스트
            print("2️⃣ 음성 파일 조회 테스트...")
            file_data = VoiceService.get_voice_file_data(voice_message.voice_file_path)
            
            if file_data:
                print(f"✅ 음성 파일 조회 성공: 크기={file_data['size']} bytes")
            else:
                print("❌ 음성 파일 조회 실패")
                return False
            
            # 3. 음성 데이터 검증 테스트
            print("3️⃣ 음성 데이터 검증 테스트...")
            is_valid = VoiceService.validate_voice_data(sample_audio)
            
            if is_valid:
                print("✅ 음성 데이터 검증 성공")
            else:
                print("❌ 음성 데이터 검증 실패")
                return False
            
            print("🎵 음성 서비스 테스트 완료!")
            return True
            
        except Exception as e:
            print(f"❌ 음성 서비스 테스트 실패: {e}")
            return False
    
    def test_voice_call_service(self):
        """음성 통화 서비스 테스트"""
        print("\n📞 음성 통화 서비스 테스트 시작...")
        
        if not self.test_consultation_code:
            self.test_consultation_code = self.create_test_consultation()
            if not self.test_consultation_code:
                return False
        
        try:
            # 1. 음성 통화 가능 여부 확인
            print("1️⃣ 음성 통화 가능 여부 확인...")
            is_available = VoiceCallService.is_voice_call_available(
                self.db, self.test_consultation_code
            )
            
            if is_available:
                print("✅ 음성 통화 가능")
            else:
                print("⚠️ 음성 통화 불가능 (정상적일 수 있음)")
            
            # 2. 음성 통화 시작 테스트
            print("2️⃣ 음성 통화 시작 테스트...")
            start_success = VoiceCallService.start_voice_call(
                self.db, self.test_consultation_code, "user"
            )
            
            if start_success:
                print("✅ 음성 통화 시작 성공")
            else:
                print("❌ 음성 통화 시작 실패")
                return False
            
            # 3. 음성 통화 상태 조회 테스트
            print("3️⃣ 음성 통화 상태 조회 테스트...")
            status = VoiceCallService.get_voice_call_status(
                self.db, self.test_consultation_code
            )
            
            if status and status.get('active'):
                print(f"✅ 음성 통화 상태 조회 성공: 활성={status['active']}")
            else:
                print("❌ 음성 통화 상태 조회 실패")
                return False
            
            # 4. 음성 통화 종료 테스트
            print("4️⃣ 음성 통화 종료 테스트...")
            end_success = VoiceCallService.end_voice_call(
                self.db, self.test_consultation_code, "user"
            )
            
            if end_success:
                print("✅ 음성 통화 종료 성공")
            else:
                print("❌ 음성 통화 종료 실패")
                return False
            
            print("📞 음성 통화 서비스 테스트 완료!")
            return True
            
        except Exception as e:
            print(f"❌ 음성 통화 서비스 테스트 실패: {e}")
            return False
    
    def test_api_endpoints(self):
        """API 엔드포인트 테스트"""
        print("\n🌐 API 엔드포인트 테스트 시작...")
        
        if not self.test_consultation_code:
            self.test_consultation_code = self.create_test_consultation()
            if not self.test_consultation_code:
                return False
        
        try:
            # 1. 음성 통화 상태 조회 API 테스트
            print("1️⃣ 음성 통화 상태 조회 API 테스트...")
            response = requests.get(
                f"{self.base_url}/api/consultation/voice/consultation/{self.test_consultation_code}/call-status"
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 음성 통화 상태 API 성공: 활성={data.get('active', False)}")
            else:
                print(f"❌ 음성 통화 상태 API 실패: {response.status_code}")
                return False
            
            # 2. 음성 메시지 목록 조회 API 테스트
            print("2️⃣ 음성 메시지 목록 조회 API 테스트...")
            response = requests.get(
                f"{self.base_url}/api/consultation/voice/consultation/{self.test_consultation_code}/messages"
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 음성 메시지 목록 API 성공: {len(data.get('messages', []))}개 메시지")
            else:
                print(f"❌ 음성 메시지 목록 API 실패: {response.status_code}")
                return False
            
            print("🌐 API 엔드포인트 테스트 완료!")
            return True
            
        except Exception as e:
            print(f"❌ API 엔드포인트 테스트 실패: {e}")
            return False
    
    async def test_websocket_voice_message(self):
        """WebSocket 음성 메시지 테스트"""
        print("\n🔌 WebSocket 음성 메시지 테스트 시작...")
        
        if not self.test_consultation_code:
            self.test_consultation_code = self.create_test_consultation()
            if not self.test_consultation_code:
                return False
        
        try:
            ws_url = f"{self.ws_url}/ws/consultation/{self.test_consultation_code}?user_type=user"
            
            # WebSocket 연결이 실패할 수 있으므로 타임아웃 설정
            try:
                async with websockets.connect(ws_url, timeout=5) as websocket:
                    print("✅ WebSocket 연결 성공")
                    
                    # 연결 확인 메시지 수신
                    try:
                        initial_message = await asyncio.wait_for(websocket.recv(), timeout=3)
                        print(f"📨 초기 메시지 수신: {initial_message[:100]}...")
                    except asyncio.TimeoutError:
                        print("⚠️ 초기 메시지 수신 타임아웃 (정상적일 수 있음)")
                    
                    # 음성 메시지 전송 테스트
                    print("1️⃣ 음성 메시지 전송 테스트...")
                    voice_message = {
                        "type": "voice_message",
                        "data": {
                            "audio_data": self.generate_sample_audio_data(),
                            "duration": 10,
                            "format": ".wav"
                        }
                    }
                    
                    await websocket.send(json.dumps(voice_message))
                    print("✅ 음성 메시지 전송 완료")
                    
                    # 응답 대기
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5)
                        print(f"📨 응답 수신: {response[:100]}...")
                    except asyncio.TimeoutError:
                        print("⚠️ 응답 수신 타임아웃")
                    
                    # 음성 통화 요청 테스트
                    print("2️⃣ 음성 통화 요청 테스트...")
                    call_request = {
                        "type": "voice_call_request",
                        "data": {}
                    }
                    
                    await websocket.send(json.dumps(call_request))
                    print("✅ 음성 통화 요청 전송 완료")
                    
                    # 응답 대기
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5)
                        print(f"📨 통화 요청 응답: {response[:100]}...")
                    except asyncio.TimeoutError:
                        print("⚠️ 통화 요청 응답 타임아웃")
                    
                    print("🔌 WebSocket 음성 메시지 테스트 완료!")
                    return True
                    
            except (ConnectionRefusedError, OSError) as e:
                print(f"❌ WebSocket 연결 실패: 서버가 실행되지 않았을 수 있습니다 - {e}")
                return False
            except Exception as e:
                print(f"❌ WebSocket 테스트 실패: {e}")
                return False
                
        except Exception as e:
            print(f"❌ WebSocket 음성 메시지 테스트 실패: {e}")
            return False
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🧪 음성채팅 기능 통합 테스트 시작")
        print("=" * 50)
        
        test_results = []
        
        # 1. 음성 서비스 테스트
        test_results.append(("음성 서비스", self.test_voice_service()))
        
        # 2. 음성 통화 서비스 테스트
        test_results.append(("음성 통화 서비스", self.test_voice_call_service()))
        
        # 3. API 엔드포인트 테스트
        test_results.append(("API 엔드포인트", self.test_api_endpoints()))
        
        # 4. WebSocket 테스트 (비동기)
        try:
            websocket_result = asyncio.run(self.test_websocket_voice_message())
            test_results.append(("WebSocket 음성 메시지", websocket_result))
        except Exception as e:
            print(f"❌ WebSocket 테스트 실행 실패: {e}")
            test_results.append(("WebSocket 음성 메시지", False))
        
        # 결과 출력
        print("\n" + "=" * 50)
        print("🧪 테스트 결과 요약")
        print("=" * 50)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ 성공" if result else "❌ 실패"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n📊 전체 결과: {passed}/{total} 테스트 통과")
        
        if passed == total:
            print("🎉 모든 테스트가 성공했습니다!")
        else:
            print("⚠️ 일부 테스트가 실패했습니다. 로그를 확인하세요.")
        
        return passed == total


def main():
    """메인 함수"""
    print("🎵 음성채팅 기능 테스트 스크립트")
    print("=" * 50)
    
    tester = VoiceChatTester()
    
    try:
        success = tester.run_all_tests()
        exit_code = 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 테스트가 중단되었습니다.")
        exit_code = 1
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 예상치 못한 오류: {e}")
        exit_code = 1
    finally:
        tester.cleanup()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()