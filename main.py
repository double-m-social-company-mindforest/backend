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
from routers.consultation import consultation_router, websocket_router, messages_router, cards_router
from routers.consultation.music import router as music_router
from routers.counselor import counselor_router, dashboard_router
from routers.counselor.auth import router as counselor_auth_router
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
        "name": "dev-tools",
        "description": "🛠️ 개발자 도구 (개발 환경 전용)",
    },
]

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

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # 환경변수에서 허용된 오리진 사용
    allow_credentials=False,  # credentials False로 설정
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
app.include_router(music_router, tags=["consultation-music"])
app.include_router(counselor_router, tags=["counselors"])
app.include_router(dashboard_router, tags=["counselor-dashboard"])
app.include_router(counselor_auth_router, tags=["counselor-auth"])
if ENVIRONMENT == "development":
    app.include_router(dev_router, tags=["dev-tools"])

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)