# React WebRTC 실시간 음성통화 구현 가이드

## 📋 개요

MindForest 백엔드에서 제공하는 WebRTC 시그널링 서버를 사용하여 React에서 실시간 음성통화를 구현하는 방법입니다.

## 🔧 필요한 패키지 설치

```bash
npm install simple-peer socket.io-client
# 또는
yarn add simple-peer socket.io-client
```

## 🎯 1. WebRTC 훅 구현

### `useWebRTC.js`

```javascript
import { useState, useRef, useCallback, useEffect } from 'react';

const useWebRTC = (consultationCode, userType = 'user') => {
  const [ws, setWs] = useState(null);
  const [localStream, setLocalStream] = useState(null);
  const [remoteStream, setRemoteStream] = useState(null);
  const [isCallActive, setIsCallActive] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  
  const peerConnection = useRef(null);
  const localAudioRef = useRef(null);
  const remoteAudioRef = useRef(null);

  // WebRTC 설정
  const rtcConfig = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' }
    ]
  };

  // WebSocket 연결
  const connectWebSocket = useCallback(() => {
    const websocket = new WebSocket(
      `ws://localhost:8000/ws/consultation/${consultationCode}?user_type=${userType}`
    );

    websocket.onopen = () => {
      console.log('WebSocket 연결됨');
      setWs(websocket);
    };

    websocket.onmessage = async (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'message':
          if (data.data.message_type === 'webrtc_offer') {
            await handleReceiveOffer(data.data.voice_data.offer);
          } else if (data.data.message_type === 'webrtc_answer') {
            await handleReceiveAnswer(data.data.voice_data.answer);
          } else if (data.data.message_type === 'webrtc_ice_candidate') {
            await handleReceiveIceCandidate(data.data.voice_data.candidate);
          } else if (data.data.message_type === 'voice_call_event') {
            handleVoiceCallEvent(data.data.voice_data.event);
          }
          break;
        case 'system':
          console.log('시스템 메시지:', data.data.message);
          break;
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket 오류:', error);
    };

    websocket.onclose = () => {
      console.log('WebSocket 연결 해제됨');
      setWs(null);
    };

    return websocket;
  }, [consultationCode, userType]);

  // 피어 연결 초기화
  const initializePeerConnection = useCallback(() => {
    if (peerConnection.current) {
      peerConnection.current.close();
    }

    const pc = new RTCPeerConnection(rtcConfig);
    
    // ICE Candidate 이벤트
    pc.onicecandidate = (event) => {
      if (event.candidate && ws) {
        ws.send(JSON.stringify({
          type: 'webrtc_ice_candidate',
          data: {
            candidate: {
              candidate: event.candidate.candidate,
              sdpMid: event.candidate.sdpMid,
              sdpMLineIndex: event.candidate.sdpMLineIndex
            }
          }
        }));
      }
    };

    // 원격 스트림 수신
    pc.ontrack = (event) => {
      console.log('원격 스트림 수신:', event.streams[0]);
      setRemoteStream(event.streams[0]);
      if (remoteAudioRef.current) {
        remoteAudioRef.current.srcObject = event.streams[0];
      }
    };

    // 연결 상태 변경
    pc.onconnectionstatechange = () => {
      console.log('연결 상태:', pc.connectionState);
      if (pc.connectionState === 'connected') {
        setIsConnecting(false);
        setIsCallActive(true);
      } else if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed') {
        endCall();
      }
    };

    peerConnection.current = pc;
    return pc;
  }, [ws]);

  // 로컬 오디오 스트림 가져오기
  const getLocalStream = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: true, 
        video: false 
      });
      
      setLocalStream(stream);
      if (localAudioRef.current) {
        localAudioRef.current.srcObject = stream;
        localAudioRef.current.muted = true; // 로컬 오디오는 음소거
      }
      
      return stream;
    } catch (error) {
      console.error('마이크 접근 실패:', error);
      throw error;
    }
  };

  // 통화 시작 (발신자)
  const startCall = async () => {
    try {
      setIsConnecting(true);
      
      // 통화 요청 전송
      ws.send(JSON.stringify({
        type: 'voice_call_request',
        data: {}
      }));

      const stream = await getLocalStream();
      const pc = initializePeerConnection();
      
      // 로컬 스트림을 피어 연결에 추가
      stream.getTracks().forEach(track => {
        pc.addTrack(track, stream);
      });

      // Offer 생성 및 전송
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      
      ws.send(JSON.stringify({
        type: 'webrtc_offer',
        data: { offer }
      }));

    } catch (error) {
      console.error('통화 시작 실패:', error);
      setIsConnecting(false);
    }
  };

  // 통화 수락 (수신자)
  const acceptCall = async () => {
    try {
      setIsConnecting(true);
      
      // 통화 수락 전송
      ws.send(JSON.stringify({
        type: 'voice_call_accept',
        data: {}
      }));

    } catch (error) {
      console.error('통화 수락 실패:', error);
      setIsConnecting(false);
    }
  };

  // Offer 수신 처리
  const handleReceiveOffer = async (offer) => {
    try {
      const stream = await getLocalStream();
      const pc = initializePeerConnection();
      
      // 로컬 스트림을 피어 연결에 추가
      stream.getTracks().forEach(track => {
        pc.addTrack(track, stream);
      });

      await pc.setRemoteDescription(offer);
      
      // Answer 생성 및 전송
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);
      
      ws.send(JSON.stringify({
        type: 'webrtc_answer',
        data: { answer }
      }));

    } catch (error) {
      console.error('Offer 처리 실패:', error);
    }
  };

  // Answer 수신 처리
  const handleReceiveAnswer = async (answer) => {
    try {
      if (peerConnection.current) {
        await peerConnection.current.setRemoteDescription(answer);
      }
    } catch (error) {
      console.error('Answer 처리 실패:', error);
    }
  };

  // ICE Candidate 수신 처리
  const handleReceiveIceCandidate = async (candidate) => {
    try {
      if (peerConnection.current && candidate.candidate) {
        await peerConnection.current.addIceCandidate(
          new RTCIceCandidate(candidate)
        );
      }
    } catch (error) {
      console.error('ICE Candidate 처리 실패:', error);
    }
  };

  // 음성 통화 이벤트 처리
  const handleVoiceCallEvent = (event) => {
    switch (event.event_type) {
      case 'request':
        console.log('통화 요청 수신');
        // UI에서 수락/거절 버튼 표시
        break;
      case 'start':
        console.log('통화 시작됨');
        setIsCallActive(true);
        break;
      case 'end':
        console.log('통화 종료됨');
        endCall();
        break;
    }
  };

  // 통화 종료
  const endCall = useCallback(() => {
    // WebSocket으로 통화 종료 알림
    if (ws) {
      ws.send(JSON.stringify({
        type: 'voice_call_end',
        data: {}
      }));
    }

    // 피어 연결 종료
    if (peerConnection.current) {
      peerConnection.current.close();
      peerConnection.current = null;
    }

    // 스트림 정리
    if (localStream) {
      localStream.getTracks().forEach(track => track.stop());
      setLocalStream(null);
    }
    
    setRemoteStream(null);
    setIsCallActive(false);
    setIsConnecting(false);
  }, [ws, localStream]);

  // 초기화
  useEffect(() => {
    const websocket = connectWebSocket();
    return () => {
      if (websocket) {
        websocket.close();
      }
      endCall();
    };
  }, [connectWebSocket, endCall]);

  return {
    ws,
    startCall,
    acceptCall,
    endCall,
    isCallActive,
    isConnecting,
    localStream,
    remoteStream,
    localAudioRef,
    remoteAudioRef
  };
};

export default useWebRTC;
```

## 🎨 2. React 컴포넌트 구현

### `VoiceCallComponent.jsx`

```jsx
import React, { useState } from 'react';
import useWebRTC from './hooks/useWebRTC';

const VoiceCallComponent = ({ consultationCode, userType }) => {
  const [incomingCall, setIncomingCall] = useState(false);
  
  const {
    startCall,
    acceptCall,
    endCall,
    isCallActive,
    isConnecting,
    localAudioRef,
    remoteAudioRef
  } = useWebRTC(consultationCode, userType);

  const handleStartCall = () => {
    startCall();
  };

  const handleAcceptCall = () => {
    acceptCall();
    setIncomingCall(false);
  };

  const handleRejectCall = () => {
    setIncomingCall(false);
    // 거절 메시지 전송 로직 추가 가능
  };

  const handleEndCall = () => {
    endCall();
  };

  return (
    <div className="voice-call-container">
      {/* 히든 오디오 엘리먼트 */}
      <audio ref={localAudioRef} autoPlay muted />
      <audio ref={remoteAudioRef} autoPlay />

      {/* 통화 UI */}
      <div className="call-controls">
        {!isCallActive && !isConnecting && !incomingCall && (
          <button 
            onClick={handleStartCall}
            className="btn-start-call"
          >
            🎤 음성 통화 시작
          </button>
        )}

        {incomingCall && (
          <div className="incoming-call">
            <p>📞 음성 통화 요청이 왔습니다</p>
            <button onClick={handleAcceptCall} className="btn-accept">
              ✅ 수락
            </button>
            <button onClick={handleRejectCall} className="btn-reject">
              ❌ 거절
            </button>
          </div>
        )}

        {isConnecting && (
          <div className="connecting">
            <p>🔄 연결 중...</p>
            <button onClick={handleEndCall} className="btn-cancel">
              취소
            </button>
          </div>
        )}

        {isCallActive && (
          <div className="active-call">
            <p>🎤 통화 중...</p>
            <button onClick={handleEndCall} className="btn-end-call">
              📞 통화 종료
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default VoiceCallComponent;
```

## 🎯 3. CSS 스타일링

### `VoiceCall.css`

```css
.voice-call-container {
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin: 10px 0;
}

.call-controls {
  text-align: center;
}

.btn-start-call {
  background: #4CAF50;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  font-size: 16px;
  cursor: pointer;
}

.btn-start-call:hover {
  background: #45a049;
}

.incoming-call {
  background: #f0f8ff;
  padding: 20px;
  border-radius: 8px;
  border: 2px solid #2196F3;
}

.incoming-call p {
  margin: 0 0 15px 0;
  font-size: 18px;
  font-weight: bold;
}

.btn-accept, .btn-reject {
  margin: 0 10px;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}

.btn-accept {
  background: #4CAF50;
  color: white;
}

.btn-reject {
  background: #f44336;
  color: white;
}

.connecting {
  background: #fff3cd;
  padding: 20px;
  border-radius: 8px;
  border: 2px solid #ffc107;
}

.active-call {
  background: #d4edda;
  padding: 20px;
  border-radius: 8px;
  border: 2px solid #28a745;
  animation: pulse 2s infinite;
}

.btn-end-call {
  background: #dc3545;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  font-size: 16px;
  cursor: pointer;
}

.btn-cancel {
  background: #6c757d;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}
```

## 🔧 4. 사용 예제

### `ConsultationPage.jsx`

```jsx
import React from 'react';
import VoiceCallComponent from './components/VoiceCallComponent';

const ConsultationPage = () => {
  const consultationCode = 'ABC123XYZ'; // 실제 상담 코드
  const userType = 'user'; // 'user' 또는 'counselor'

  return (
    <div className="consultation-page">
      <h1>상담 페이지</h1>
      
      {/* 채팅 영역 */}
      <div className="chat-area">
        {/* 채팅 메시지들... */}
      </div>

      {/* 음성 통화 컴포넌트 */}
      <VoiceCallComponent 
        consultationCode={consultationCode}
        userType={userType}
      />
    </div>
  );
};

export default ConsultationPage;
```

## 🚀 5. 고급 기능 추가

### 음성 볼륨 시각화

```jsx
// useAudioLevel.js
import { useState, useEffect, useRef } from 'react';

const useAudioLevel = (stream) => {
  const [audioLevel, setAudioLevel] = useState(0);
  const animationRef = useRef();

  useEffect(() => {
    if (!stream) return;

    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(stream);
    
    source.connect(analyser);
    analyser.fftSize = 256;
    
    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    const updateLevel = () => {
      analyser.getByteFrequencyData(dataArray);
      const level = dataArray.reduce((a, b) => a + b) / dataArray.length;
      setAudioLevel(level);
      animationRef.current = requestAnimationFrame(updateLevel);
    };

    updateLevel();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      audioContext.close();
    };
  }, [stream]);

  return audioLevel;
};

export default useAudioLevel;
```

### 통화 시간 표시

```jsx
// useCallTimer.js
import { useState, useEffect } from 'react';

const useCallTimer = (isActive) => {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    let interval = null;
    
    if (isActive) {
      interval = setInterval(() => {
        setSeconds(seconds => seconds + 1);
      }, 1000);
    } else {
      setSeconds(0);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isActive]);

  const formatTime = (totalSeconds) => {
    const minutes = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return formatTime(seconds);
};

export default useCallTimer;
```

## ⚡ 6. 에러 처리 및 최적화

### 에러 처리

```jsx
const useWebRTC = (consultationCode, userType) => {
  const [error, setError] = useState(null);
  const [connectionState, setConnectionState] = useState('disconnected');

  const handleError = (error, context) => {
    console.error(`WebRTC 오류 (${context}):`, error);
    setError({
      message: error.message || '알 수 없는 오류가 발생했습니다',
      context,
      timestamp: new Date().toISOString()
    });
  };

  // 연결 상태 모니터링
  useEffect(() => {
    if (peerConnection.current) {
      const pc = peerConnection.current;
      
      pc.onconnectionstatechange = () => {
        setConnectionState(pc.connectionState);
        
        if (pc.connectionState === 'failed') {
          handleError(new Error('연결이 실패했습니다'), 'connection');
        }
      };
    }
  }, [peerConnection.current]);

  return {
    // ... 기존 반환값
    error,
    connectionState,
    clearError: () => setError(null)
  };
};
```

## 📝 7. 요약

### 구현 단계:
1. **WebSocket 연결**: 백엔드와 시그널링 통신
2. **WebRTC 설정**: PeerConnection 초기화 및 ICE 서버 설정
3. **미디어 스트림**: 마이크 접근 및 오디오 스트림 관리
4. **시그널링**: Offer/Answer/ICE Candidate 교환
5. **UI 구성**: 통화 버튼 및 상태 표시
6. **에러 처리**: 연결 실패 및 권한 오류 처리

### 백엔드 API:
- WebSocket: `ws://localhost:8000/ws/consultation/{code}?user_type=user`
- REST API: `/api/consultation/voice/consultation/{code}/webrtc-session`

### 주요 특징:
- ✅ 실시간 P2P 음성 통화
- ✅ 시그널링 서버 통합
- ✅ 연결 상태 관리
- ✅ 에러 처리
- ✅ 반응형 UI

이제 React에서 완전한 실시간 음성 통화를 구현할 수 있습니다!