# 마인드포레스트 상담 프로세스 API 가이드

## 개요
마인드포레스트는 콜택시 방식의 실시간 상담 매칭 시스템을 사용합니다. 사용자가 상담을 요청하면 대기 중인 상담사에게 알림이 가고, 상담사가 수락하면 실시간 채팅이 시작됩니다.

## 상담 진행 단계

### 1단계: 상담 요청 (사용자)

#### 1-1. 상담 시작 요청
```
POST /api/v1/consultations/start
```
**요청 본문:**
```json
{
  "nickname": "익명123",
  "character_type_preference": 1,  // 선택사항: 선호 캐릭터 ID
  "quick_match": true             // 빠른 매칭 여부 (기본값: true)
}
```
**응답:**
```json
{
  "id": 123,
  "consultation_code": "ABC123XYZ",
  "user_nickname": "익명123",
  "character_type_id": 1,
  "character_name": "따뜻한 곰돌이",
  "status": "waiting",
  "created_at": "2025-01-01T10:00:00"
}
```
- 상담 코드는 9자리 고유 문자열
- 상태는 `waiting` (상담사 배정 대기중)

### 2단계: 상담사 매칭 (시스템)

#### 2-1. 상담사 상태 변경 (상담사가 대기 시작)
```
PUT /api/v1/counselors/auth/status/waiting
```
- 상담사가 "콜대기" 상태로 전환
- 이제 상담 요청을 받을 수 있음

#### 2-2. 상담사 알림 수신 (WebSocket)
```
WebSocket: /ws/counselor/{counselor_id}/notifications
```
상담사는 실시간으로 새 상담 요청 알림을 받습니다.

#### 2-3. 대기 중인 요청 목록 조회 (상담사)
```
GET /api/v1/counselors/{counselor_id}/dashboard/requests
```
**응답:**
```json
{
  "requests": [
    {
      "id": 456,
      "consultation_id": 123,
      "user_nickname": "익명123",
      "character_preference": "따뜻한 곰돌이",
      "status": "pending",
      "requested_at": "2025-01-01T10:00:00"
    }
  ],
  "total": 1
}
```

### 3단계: 상담 수락/거절 (상담사)

#### 3-1. 상담 수락
```
POST /api/v1/counselors/{counselor_id}/dashboard/requests/{request_id}/accept
```
**요청 본문:**
```json
{
  "response_message": "안녕하세요! 상담을 시작하겠습니다."  // 선택사항
}
```
- 상담 상태가 `waiting` → `active`로 변경
- 상담사가 배정됨

#### 3-2. 상담 거절
```
POST /api/v1/counselors/{counselor_id}/dashboard/requests/{request_id}/reject
```
**요청 본문:**
```json
{
  "response_message": "죄송합니다. 다른 상담이 진행 중입니다."  // 선택사항
}
```
- 시스템이 다른 상담사를 찾아 재매칭 시도

### 4단계: 실시간 상담 진행

#### 4-1. WebSocket 연결 (사용자 & 상담사)
```
WebSocket: /ws/consultation/{consultation_code}
```
- 양방향 실시간 채팅
- 메시지는 자동으로 저장됨

#### 4-2. 메시지 히스토리 조회
```
GET /api/v1/consultations/{consultation_code}/messages?page=1&page_size=50
```
**응답:**
```json
{
  "messages": [
    {
      "id": 789,
      "sender_type": "user",
      "sender_name": "익명123",
      "message": "안녕하세요",
      "created_at": "2025-01-01T10:01:00"
    },
    {
      "id": 790,
      "sender_type": "counselor",
      "sender_name": "김상담사",
      "message": "안녕하세요! 무엇을 도와드릴까요?",
      "created_at": "2025-01-01T10:01:30"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 50
}
```

#### 4-3. 상담 재연결 (연결 끊김 시)
```
POST /api/v1/consultations/{consultation_code}/reconnect
```
**요청 본문:**
```json
{
  "nickname": "새닉네임"  // 선택사항: 닉네임 변경
}
```

### 5단계: 상담 종료

#### 5-1. 상담 종료 (사용자)
```
POST /api/v1/consultations/{consultation_code}/end
```
**응답:**
```json
{
  "status": "completed",
  "completed_at": "2025-01-01T11:00:00",
  "duration_minutes": 60
}
```
- 상담 상태가 `active` → `completed`로 변경

### 6단계: 상담 카드 발급

#### 6-1. 상담 카드 생성
```
POST /api/v1/consultations/{consultation_code}/card
```
**요청 본문:**
```json
{
  "additional_notes": "상담이 많은 도움이 되었습니다."  // 선택사항
}
```
**응답:**
```json
{
  "id": 321,
  "consultation_code": "ABC123XYZ",
  "counselor_name": "김상담사",
  "character_type": "따뜻한 곰돌이",
  "consultation_date": "2025-01-01",
  "duration_minutes": 60,
  "key_points": ["스트레스 관리", "자기 돌봄의 중요성"],
  "counselor_notes": "상담 내용 요약...",
  "additional_notes": "상담이 많은 도움이 되었습니다.",
  "created_at": "2025-01-01T11:05:00"
}
```

#### 6-2. 상담 카드 조회
```
GET /api/v1/consultations/{consultation_code}/card
```

#### 6-3. 상담 카드 수정 (추가 메모)
```
PUT /api/v1/consultations/{consultation_code}/card
```
**요청 본문:**
```json
{
  "additional_notes": "수정된 추가 메모입니다."
}
```

## 상담 상태 플로우

```
waiting (대기중) 
    ↓ (상담사 수락)
active (진행중)
    ↓ (상담 종료)
completed (완료) → 카드 발급 가능
    
또는

waiting (대기중)
    ↓ (비정상 종료)
terminated (종료됨)
```

## 주요 특징

1. **콜택시 방식**: 사용자가 요청하면 대기 중인 상담사에게 실시간 알림
2. **캐릭터 시스템**: 사용자가 선호하는 캐릭터 타입 선택 가능
3. **부하 분산**: 상담사의 현재 진행 중인 상담 수를 고려하여 균등 배분
4. **실시간 통신**: WebSocket을 통한 양방향 실시간 채팅
5. **상담 카드**: 상담 완료 후 요약 카드 발급으로 기록 보관

## 보조 API

### 상담사 관련
- `GET /api/v1/counselors/auth/counseling-fields` - 상담 분야 목록
- `GET /api/v1/counselors/` - 상담사 목록 조회
- `GET /api/v1/counselors/{counselor_id}/stats` - 상담사 통계

### 인증 관련
- `POST /api/v1/counselors/auth/login` - 상담사 로그인
- `POST /api/v1/counselors/auth/logout` - 상담사 로그아웃
- `POST /api/v1/counselors/auth/refresh` - 토큰 갱신