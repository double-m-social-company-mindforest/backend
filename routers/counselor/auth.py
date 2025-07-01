from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from database.connection import get_db
from database.models import Counselor, CounselorStatus
from schemas.counselor.auth import (
    CounselorRegister,
    CounselorLogin,
    CounselorResponse,
    TokenResponse,
    PasswordChangeRequest,
    CounselingFieldsListResponse,
    UsernameCheckRequest,
    PhoneCheckRequest,
    EmailCheckRequest,
    CheckResponse,
    RefreshTokenRequest,
    RefreshTokenResponse
)
from services.counselor.auth_service import CounselorAuthService
from sqlalchemy.sql import func
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/counselors/auth",
    tags=["counselor-auth"]
)

security = HTTPBearer()


def get_current_counselor(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """현재 로그인한 상담사 정보 조회 (의존성)"""
    token = credentials.credentials
    return CounselorAuthService.get_current_counselor(db, token)


@router.get("/counseling-fields", response_model=CounselingFieldsListResponse)
def get_counseling_fields(db: Session = Depends(get_db)):
    """
    상담 분야 목록 조회
    
    회원가입 시 선택할 수 있는 상담 분야 목록을 반환합니다.
    """
    try:
        fields = CounselorAuthService.get_counseling_fields(db)
        return CounselingFieldsListResponse(
            fields=fields,
            total=len(fields)
        )
    except Exception as e:
        logger.error(f"상담 분야 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail="상담 분야 조회 중 오류가 발생했습니다")


@router.post("/check-username", response_model=CheckResponse)
def check_username_availability(
    request: UsernameCheckRequest,
    db: Session = Depends(get_db)
):
    """
    아이디 중복 확인
    
    - **username**: 확인할 아이디
    """
    try:
        is_available = CounselorAuthService.check_username_availability(db, request.username)
        return CheckResponse(
            is_available=is_available,
            message="사용 가능한 아이디입니다" if is_available else "이미 사용 중인 아이디입니다"
        )
    except Exception as e:
        logger.error(f"아이디 중복 확인 중 오류: {e}")
        raise HTTPException(status_code=500, detail="아이디 중복 확인 중 오류가 발생했습니다")


@router.post("/check-phone", response_model=CheckResponse)
def check_phone_availability(
    request: PhoneCheckRequest,
    db: Session = Depends(get_db)
):
    """
    휴대폰 번호 중복 확인
    
    - **phone**: 확인할 휴대폰 번호
    """
    try:
        is_available = CounselorAuthService.check_phone_availability(db, request.phone)
        return CheckResponse(
            is_available=is_available,
            message="사용 가능한 휴대폰 번호입니다" if is_available else "이미 등록된 휴대폰 번호입니다"
        )
    except Exception as e:
        logger.error(f"휴대폰 번호 중복 확인 중 오류: {e}")
        raise HTTPException(status_code=500, detail="휴대폰 번호 중복 확인 중 오류가 발생했습니다")


@router.post("/check-email", response_model=CheckResponse)
def check_email_availability(
    request: EmailCheckRequest,
    db: Session = Depends(get_db)
):
    """
    이메일 중복 확인
    
    - **email**: 확인할 이메일
    """
    try:
        is_available = CounselorAuthService.check_email_availability(db, request.email)
        return CheckResponse(
            is_available=is_available,
            message="사용 가능한 이메일입니다" if is_available else "이미 등록된 이메일입니다"
        )
    except Exception as e:
        logger.error(f"이메일 중복 확인 중 오류: {e}")
        raise HTTPException(status_code=500, detail="이메일 중복 확인 중 오류가 발생했습니다")


@router.post("/register", response_model=CounselorResponse, status_code=status.HTTP_201_CREATED)
def register_counselor(
    counselor_data: CounselorRegister,
    db: Session = Depends(get_db)
):
    """
    상담사 회원가입
    
    새로운 상담사 계정을 생성합니다. 관리자 승인 후 이용 가능합니다.
    
    **필수 정보:**
    - **username**: 아이디 (4-50자, 영문/숫자/언더스코어만)
    - **password**: 비밀번호 (8자 이상)
    - **password_confirm**: 비밀번호 확인
    - **name**: 실명 (2-100자)
    - **gender**: 성별 (male/female/other)
    - **birth_date**: 생년월일 (YYYY-MM-DD)
    - **phone**: 휴대폰 번호 (010-0000-0000 형식)
    - **counseling_fields**: 상담 분야 ID 목록 (1-9개)
    
    **선택 정보:**
    - **email**: 이메일
    - **bio**: 상담사 소개 (최대 1000자)
    - **license_number**: 자격증 번호
    - **experience_years**: 경력 연수 (0-50년)
    """
    try:
        return CounselorAuthService.register_counselor(db, counselor_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"회원가입 처리 중 오류: {e}")
        raise HTTPException(status_code=500, detail="회원가입 처리 중 오류가 발생했습니다")


@router.post("/login", response_model=TokenResponse)
def login_counselor(
    login_data: CounselorLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    상담사 로그인
    
    - **username**: 아이디
    - **password**: 비밀번호
    
    성공 시 JWT 액세스 토큰을 반환합니다. (유효기간: 30분)
    """
    try:
        return CounselorAuthService.login(db, login_data, request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그인 처리 중 오류: {e}")
        raise HTTPException(status_code=500, detail="로그인 처리 중 오류가 발생했습니다")


@router.get("/profile", response_model=CounselorResponse)
def get_counselor_profile(
    current_counselor = Depends(get_current_counselor)
):
    """
    상담사 프로필 조회
    
    현재 로그인한 상담사의 프로필 정보를 조회합니다.
    Authorization 헤더에 Bearer 토큰이 필요합니다.
    """
    return CounselorResponse.from_orm(current_counselor)


@router.post("/change-password")
def change_password(
    password_data: PasswordChangeRequest,
    current_counselor = Depends(get_current_counselor),
    db: Session = Depends(get_db)
):
    """
    비밀번호 변경
    
    - **current_password**: 현재 비밀번호
    - **new_password**: 새 비밀번호 (8자 이상)
    - **new_password_confirm**: 새 비밀번호 확인
    
    Authorization 헤더에 Bearer 토큰이 필요합니다.
    """
    try:
        return CounselorAuthService.change_password(db, current_counselor.id, password_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"비밀번호 변경 중 오류: {e}")
        raise HTTPException(status_code=500, detail="비밀번호 변경 중 오류가 발생했습니다")


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    토큰 갱신
    
    Refresh Token을 사용하여 새로운 Access Token을 발급받습니다.
    
    - **refresh_token**: 로그인 시 받은 Refresh Token
    
    성공 시 새로운 Access Token을 반환합니다. (유효기간: 30분)
    """
    try:
        result = CounselorAuthService.refresh_access_token(db, refresh_request.refresh_token)
        return RefreshTokenResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"토큰 갱신 중 오류: {e}")
        raise HTTPException(status_code=500, detail="토큰 갱신 중 오류가 발생했습니다")


@router.put("/status/waiting")
def start_waiting_for_call(
    current_counselor = Depends(get_current_counselor),
    db: Session = Depends(get_db)
):
    """
    콜대기 시작
    
    상담사가 콜대기 상태로 변경합니다.
    Authorization 헤더에 Bearer 토큰이 필요합니다.
    """
    try:
        # 상태를 waiting_for_call로 변경
        counselor = db.query(Counselor).filter(Counselor.id == current_counselor.id).first()
        if not counselor:
            raise HTTPException(status_code=404, detail="상담사를 찾을 수 없습니다")
        
        counselor.status = CounselorStatus.waiting_for_call
        counselor.last_active_at = func.now()
        db.commit()
        
        return {
            "message": "콜대기 상태로 변경되었습니다",
            "status": counselor.status.value
        }
    except Exception as e:
        logger.error(f"콜대기 상태 변경 중 오류: {e}")
        raise HTTPException(status_code=500, detail="상태 변경 중 오류가 발생했습니다")


@router.put("/status/offline")
def stop_waiting_for_call(
    current_counselor = Depends(get_current_counselor),
    db: Session = Depends(get_db)
):
    """
    콜대기 종료
    
    상담사가 오프라인 상태로 변경합니다.
    Authorization 헤더에 Bearer 토큰이 필요합니다.
    """
    try:
        # 상태를 offline으로 변경
        counselor = db.query(Counselor).filter(Counselor.id == current_counselor.id).first()
        if not counselor:
            raise HTTPException(status_code=404, detail="상담사를 찾을 수 없습니다")
        
        counselor.status = CounselorStatus.offline
        counselor.last_active_at = func.now()
        db.commit()
        
        return {
            "message": "오프라인 상태로 변경되었습니다",
            "status": counselor.status.value
        }
    except Exception as e:
        logger.error(f"오프라인 상태 변경 중 오류: {e}")
        raise HTTPException(status_code=500, detail="상태 변경 중 오류가 발생했습니다")


@router.get("/me", response_model=CounselorResponse)
def get_me(
    current_counselor = Depends(get_current_counselor),
    db: Session = Depends(get_db)
):
    """
    현재 로그인한 상담사 정보 조회
    
    Authorization 헤더에 Bearer 토큰이 필요합니다.
    """
    try:
        return CounselorResponse.from_orm(current_counselor)
    except Exception as e:
        logger.error(f"상담사 정보 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail="상담사 정보 조회 중 오류가 발생했습니다")


@router.post("/logout")
def logout_counselor(
    refresh_token: Optional[RefreshTokenRequest] = None,
    current_counselor = Depends(get_current_counselor),
    db: Session = Depends(get_db)
):
    """
    상담사 로그아웃
    
    Refresh Token을 무효화하여 로그아웃 처리합니다.
    
    - **refresh_token**: 무효화할 특정 Refresh Token (선택사항)
    - 미제공 시 해당 상담사의 모든 Refresh Token이 무효화됩니다.
    
    Authorization 헤더에 Bearer 토큰이 필요합니다.
    """
    try:
        token = refresh_token.refresh_token if refresh_token else None
        return CounselorAuthService.logout(db, current_counselor.id, token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그아웃 처리 중 오류: {e}")
        raise HTTPException(status_code=500, detail="로그아웃 처리 중 오류가 발생했습니다")


@router.get("/test-auth")
def test_auth(current_counselor = Depends(get_current_counselor)):
    """
    인증 테스트용 엔드포인트
    
    Authorization 헤더에 Bearer 토큰이 필요합니다.
    """
    return {
        "message": "인증 성공",
        "counselor_id": current_counselor.id,
        "username": current_counselor.username,
        "name": current_counselor.name
    }