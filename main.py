import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from config.logging import setup_logging
from routers.health import router as health_router
from routers.home import router as home_router
from routers.keywords import router as keywords_router
from routers.personality import router as personality_router
from routers.types import router as types_router
from routers.intermediate_types import router as intermediate_types_router
from routers.consultation import consultation_router, websocket_router, messages_router, cards_router, voice_router
from routers.consultation.music import router as music_router
from routers.counselor import counselor_router, dashboard_router
from routers.counselor.auth import router as counselor_auth_router
from routers.admin.auth import router as admin_auth_router
from routers.admin.counselor_management import router as admin_counselor_router
from routers.dev import router as dev_router

load_dotenv()
setup_logging()

# 환경 변수 로드
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# API 문서 태그 정의
tags_metadata = [
    {
        "name": "system",
        "description": "🏠 홈페이지, 헬스체크 등 기본 시스템 기능",
    },
    {
        "name": "keywords",
        "description": "🔑 키워드 및 카테고리 관리",
    },
    {
        "name": "personality",
        "description": "🧠 성격 유형 계산 - 키워드 기반 캐릭터 유형 분석",
    },
    {
        "name": "캐릭터 유형",
        "description": "🎭 32개 최종 캐릭터 유형 관리",
    },
    {
        "name": "중간 유형", 
        "description": "⚖️ 16개 중간 유형 관리",
    },
    {
        "name": "consultations",
        "description": "💬 실시간 상담 기능 - 상담사와의 1:1 상담",
    },
    {
        "name": "consultation-music",
        "description": "🎵 상담 중 음원 추천 - 대화 기반 배경음악 추천",
    },
    {
        "name": "counselor-auth",
        "description": "🔐 상담사 인증 - 회원가입, 로그인, 프로필 관리",
    },
    {
        "name": "counselors",
        "description": "👨‍⚕️ 상담사 관리 - 상담사 등록, 상태 관리",
    },
    {
        "name": "counselor-dashboard",
        "description": "📊 상담사 대시보드 - 상담 요청 수락/거절, 대기열 관리",
    },
    {
        "name": "관리자 인증",
        "description": "🔐 관리자 인증 - 로그인, 계정 관리, 권한 관리",
    },
    {
        "name": "관리자 상담사 관리",
        "description": "👨‍💼 관리자 상담사 관리 - 상담사 승인, 목록 조회, 상태 관리",
    },
    {
        "name": "dev-tools",
        "description": "🛠️ 개발자 도구 (개발 환경 전용)",
    },
]

# WebSocket 문서를 위한 OpenAPI 확장
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title="🌲 MindForest API",
        version="1.1.0",
        description="키워드 기반 성격 유형 분석과 실시간 상담 서비스 API",
        routes=app.routes,
        tags=tags_metadata,
    )
    
    # WebSocket 엔드포인트 정보 추가
    openapi_schema["paths"]["/ws/consultation/{consultation_code}"] = {
        "get": {
            "tags": ["consultations"],
            "summary": "🔌 실시간 상담 WebSocket",
            "description": """
## WebSocket 실시간 상담 연결

실시간 채팅을 위한 WebSocket 연결입니다.

### 연결 방법
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/consultation/{consultation_code}?user_type=user');
```

### 메시지 형식

#### 클라이언트 → 서버
```json
{
  "type": "message",
  "data": {
    "content": "안녕하세요"
  }
}
```

#### 서버 → 클라이언트
```json
{
  "type": "message",
  "data": {
    "sender_type": "user",
    "content": "안녕하세요",
    "message_type": "text",
    "timestamp": "2025-07-22T12:34:56.789Z"
  }
}
```

#### 타이핑 상태
```json
{
  "type": "typing",
  "data": {
    "is_typing": true
  }
}
```

#### 시스템 메시지
```json
{
  "type": "system",
  "data": {
    "message": "상담사가 연결되었습니다",
    "event": "connection_established",
    "timestamp": "2025-07-22T12:34:56.789Z"
  }
}
```

### 매개변수
- **consultation_code** (path): 9자리 상담 코드
- **user_type** (query): 사용자 유형 ("user" 또는 "counselor")

### 응답 코드
- **1000**: 정상 연결 종료
- **4003**: 종료된 상담 접근
- **4004**: 존재하지 않는 상담 코드
            """,
            "parameters": [
                {
                    "name": "consultation_code",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "pattern": "^[A-Z0-9]{9}$"},
                    "description": "9자리 상담 코드 (예: ABC123XYZ)"
                },
                {
                    "name": "user_type",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string", "enum": ["user", "counselor"], "default": "user"},
                    "description": "사용자 유형"
                }
            ],
            "responses": {
                "101": {
                    "description": "WebSocket 연결 성공 (Switching Protocols)"
                },
                "400": {
                    "description": "잘못된 요청"
                },
                "4003": {
                    "description": "종료된 상담 접근"
                },
                "4004": {
                    "description": "존재하지 않는 상담 코드"
                }
            }
        }
    }
    
    openapi_schema["paths"]["/ws/counselor/{counselor_id}/notifications"] = {
        "get": {
            "tags": ["counselor-dashboard"],
            "summary": "🔔 상담사 알림 WebSocket",
            "description": """
## 상담사 알림 WebSocket

상담사가 실시간으로 상담 요청을 받기 위한 WebSocket 연결입니다.

### 연결 방법
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/counselor/{counselor_id}/notifications');
```

### 메시지 형식

#### 상담 요청 알림
```json
{
  "type": "consultation_request",
  "data": {
    "consultation_id": 123,
    "consultation_code": "ABC123456",
    "user_nickname": "익명의 사용자",
    "character_name": "숲속의 현자",
    "request_id": "req_12345",
    "timestamp": "2025-07-22T12:34:56.789Z",
    "timeout": 30
  }
}
```

#### Heartbeat
```json
{
  "type": "heartbeat",
  "data": {}
}
```

#### 응답
```json
{
  "type": "heartbeat_ack",
  "data": {
    "status": "alive"
  }
}
```

### 매개변수
- **counselor_id** (path): 상담사 ID

### 사용법
1. 상담사가 '콜대기' 상태로 전환
2. WebSocket 연결
3. 상담 요청 시 실시간 알림 수신
4. 수락/거절 API 호출
            """,
            "parameters": [
                {
                    "name": "counselor_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"},
                    "description": "상담사 ID"
                }
            ],
            "responses": {
                "101": {
                    "description": "WebSocket 연결 성공 (Switching Protocols)"
                },
                "400": {
                    "description": "잘못된 요청"
                },
                "401": {
                    "description": "인증 실패"
                }
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# FastAPI 앱 생성
app = FastAPI(
    title="🌲 MindForest API",
    version="1.0.0",
    description="키워드 기반 성격 유형 분석과 실시간 상담 서비스 API",
    openapi_tags=tags_metadata,
    debug=DEBUG,
    contact={
        "name": "Github MindForest",
        "url": "https://github.com/double-m-social-company-mindforest",
    },
    docs_url="/docs",
    redoc_url="/redoc"
)

# 커스텀 OpenAPI 스키마 적용
app.openapi = custom_openapi

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # 환경변수에서 허용된 오리진 사용
    allow_credentials=True,  # JWT 인증을 위해 credentials 허용
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(home_router, tags=["system"])
app.include_router(health_router, tags=["system"])
app.include_router(keywords_router, tags=["keywords"])
app.include_router(personality_router, tags=["personality"])
app.include_router(types_router, tags=["캐릭터 유형"])
app.include_router(intermediate_types_router, tags=["중간 유형"])
app.include_router(consultation_router, tags=["consultations"])
app.include_router(websocket_router)
app.include_router(messages_router, tags=["consultations"])
app.include_router(cards_router, tags=["consultations"])
app.include_router(voice_router, prefix="/api/consultation", tags=["voice"])
app.include_router(music_router, tags=["consultation-music"])
app.include_router(counselor_router, tags=["counselors"])
app.include_router(dashboard_router, tags=["counselor-dashboard"])
app.include_router(counselor_auth_router, tags=["counselor-auth"])
app.include_router(admin_auth_router, prefix="/api/v1/admin", tags=["관리자 인증"])
app.include_router(admin_counselor_router, prefix="/api/v1/admin", tags=["관리자 상담사 관리"])
if ENVIRONMENT == "development":
    app.include_router(dev_router, tags=["dev-tools"])

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)