from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.health import router as health_router
from routers.home import router as home_router

# FastAPI 앱 생성
app = FastAPI(
    title="MindForest API",
    version="1.0.0",
    description="MindForest Backend API"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(home_router)
app.include_router(health_router)