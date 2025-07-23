from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from database.connection import get_db
from database.models import Admin
from schemas.admin.auth import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminCreateRequest,
    AdminInfo,
    AdminChangePasswordRequest,
    TokenRefreshRequest,
    TokenRefreshResponse
)
from services.admin.auth_service import AdminAuthService
from dependencies.admin_auth import (
    get_current_admin,
    require_super_admin,
    require_admin_or_above,
    AdminPermissions
)

router = APIRouter(prefix="/auth", tags=["관리자 인증"])


@router.post("/login", response_model=AdminLoginResponse, summary="관리자 로그인")
async def login(
    login_data: AdminLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    관리자 로그인
    
    - **username**: 관리자 아이디
    - **password**: 비밀번호
    """
    return AdminAuthService.login(db, login_data, request)


@router.post("/refresh", response_model=TokenRefreshResponse, summary="토큰 갱신")
async def refresh_token(
    refresh_data: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh Token으로 새로운 Access Token 발급
    
    - **refresh_token**: 유효한 Refresh Token
    """
    return AdminAuthService.refresh_access_token(db, refresh_data.refresh_token)


@router.post("/logout", summary="관리자 로그아웃")
async def logout(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    관리자 로그아웃 (모든 Refresh Token 무효화)
    """
    return AdminAuthService.logout(db, current_admin.id)


@router.get("/me", response_model=AdminInfo, summary="현재 관리자 정보 조회")
async def get_current_admin_info(
    current_admin: Admin = Depends(get_current_admin)
):
    """
    현재 로그인한 관리자 정보 조회
    """
    return AdminInfo.from_orm(current_admin)


@router.post("/change-password", summary="관리자 비밀번호 변경")
async def change_password(
    password_data: AdminChangePasswordRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    관리자 비밀번호 변경
    
    - **current_password**: 현재 비밀번호
    - **new_password**: 새 비밀번호 (8자 이상)
    - **new_password_confirm**: 새 비밀번호 확인
    """
    return AdminAuthService.change_password(db, current_admin.id, password_data)


@router.post("/create-admin", response_model=AdminInfo, summary="관리자 계정 생성")
async def create_admin(
    admin_data: AdminCreateRequest,
    current_admin: Admin = Depends(require_admin_or_above),
    db: Session = Depends(get_db)
):
    """
    새 관리자 계정 생성 (관리자 이상 권한 필요)
    
    - **username**: 관리자 아이디 (4-50자, 영문/숫자/언더스코어)
    - **password**: 비밀번호 (8자 이상)
    - **password_confirm**: 비밀번호 확인
    - **name**: 이름
    - **email**: 이메일
    - **role**: 관리자 역할 (moderator/admin/super_admin)
    
    권한 제한:
    - super_admin: 모든 역할 생성 가능
    - admin: moderator만 생성 가능
    """
    # 권한 확인
    if not AdminPermissions.can_create_admin(current_admin, admin_data.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"'{admin_data.role.value}' 역할의 관리자를 생성할 권한이 없습니다"
        )
    
    return AdminAuthService.create_admin(db, admin_data, current_admin.id)


@router.get("/check-username/{username}", summary="관리자 아이디 중복 확인")
async def check_username_availability(
    username: str,
    db: Session = Depends(get_db)
) -> Dict[str, bool]:
    """
    관리자 아이디 중복 확인
    
    - **username**: 확인할 아이디
    """
    is_available = AdminAuthService.check_username_availability(db, username)
    return {
        "available": is_available,
        "message": "사용 가능한 아이디입니다" if is_available else "이미 사용 중인 아이디입니다"
    }


@router.get("/check-email/{email}", summary="관리자 이메일 중복 확인")
async def check_email_availability(
    email: str,
    db: Session = Depends(get_db)
) -> Dict[str, bool]:
    """
    관리자 이메일 중복 확인
    
    - **email**: 확인할 이메일
    """
    is_available = AdminAuthService.check_email_availability(db, email)
    return {
        "available": is_available,
        "message": "사용 가능한 이메일입니다" if is_available else "이미 등록된 이메일입니다"
    }