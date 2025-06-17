import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from config.logging import setup_logging
from routers.health import router as health_router
from routers.home import router as home_router
from routers.test import router as test_router
from routers.types import router as types_router
from routers.matching import router as matching_router
from routers.intermediate_types import router as intermediate_types_router

load_dotenv()
setup_logging()

# 환경 변수 로드
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# API 문서 태그 정의
tags_metadata = [
    {
        "name": "홈",
        "description": "🏠 기본 홈페이지",
    },
    {
        "name": "헬스체크", 
        "description": "💊 서버 상태 확인",
    },
    {
        "name": "유형 계산",
        "description": "🧠 마음 유형 테스트 계산 - 키워드 기반 캐릭터 유형 분석",
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
        "name": "테스트",
        "description": "🧪 개발자 도구 및 디버깅",
    },
]

# FastAPI 앱 생성
app = FastAPI(
    title="🌲 MindForest API",
    version="1.0.0",
    description="키워드 기반 마음 유형 테스트 API - 3개 카테고리 키워드 선택으로 32개 캐릭터 유형 분석",
    openapi_tags=tags_metadata,
    debug=DEBUG,
    contact={
        "name": "Github MindForest",
        "url": "https://github.com/double-m-social-company-mindforest",
    },
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(home_router, tags=["홈"])
app.include_router(health_router, tags=["헬스체크"])
app.include_router(test_router, tags=["테스트"])
app.include_router(types_router, tags=["캐릭터 유형"])
app.include_router(matching_router, tags=["유형 계산"])
app.include_router(intermediate_types_router, tags=["중간 유형"])