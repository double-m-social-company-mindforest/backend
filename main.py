import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

# FastAPI 앱 생성
app = FastAPI(
    title="MindForest API",
    version="1.0.0",
    description="MindForest Backend API",
    debug=DEBUG
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
app.include_router(home_router)
app.include_router(health_router)
app.include_router(test_router)
app.include_router(types_router)
app.include_router(matching_router)
app.include_router(intermediate_types_router)