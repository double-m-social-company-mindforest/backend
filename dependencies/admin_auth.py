from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from database.connection import get_db
from database.models import Admin, AdminRole
from services.admin.auth_service import AdminAuthService

security = HTTPBearer(auto_error=False)


async def get_current_admin(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Admin:
    """현재 로그인한 관리자 정보 조회 (Authorization 헤더 또는 쿠키에서)"""
    token = None
    
    # 1. Authorization 헤더에서 토큰 확인
    if credentials:
        token = credentials.credentials
    
    # 2. 쿠키에서 토큰 확인
    elif "access_token" in request.cookies:
        token = request.cookies["access_token"]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 필요합니다"
        )
    
    return AdminAuthService.get_current_admin(db, token)


async def get_current_active_admin(
    current_admin: Admin = Depends(get_current_admin)
) -> Admin:
    """활성화된 관리자 확인"""
    if not current_admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 관리자 계정입니다"
        )
    return current_admin


def require_admin_role(*allowed_roles: AdminRole):
    """특정 관리자 역할 권한 확인 데코레이터"""
    def role_checker(current_admin: Admin = Depends(get_current_active_admin)) -> Admin:
        if current_admin.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"이 작업을 수행할 권한이 없습니다. 필요한 권한: {[role.value for role in allowed_roles]}"
            )
        return current_admin
    return role_checker


# 특정 역할별 의존성 함수들
async def require_super_admin(
    current_admin: Admin = Depends(get_current_active_admin)
) -> Admin:
    """최고 관리자 권한 확인"""
    if current_admin.role != AdminRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="최고 관리자 권한이 필요합니다"
        )
    return current_admin


async def require_admin_or_above(
    current_admin: Admin = Depends(get_current_active_admin)
) -> Admin:
    """관리자 이상 권한 확인"""
    allowed_roles = [AdminRole.admin, AdminRole.super_admin]
    if current_admin.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 이상의 권한이 필요합니다"
        )
    return current_admin


async def require_moderator_or_above(
    current_admin: Admin = Depends(get_current_active_admin)
) -> Admin:
    """모더레이터 이상 권한 확인"""
    allowed_roles = [AdminRole.moderator, AdminRole.admin, AdminRole.super_admin]
    if current_admin.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="모더레이터 이상의 권한이 필요합니다"
        )
    return current_admin


class AdminPermissions:
    """관리자 권한 검사 유틸리티 클래스"""
    
    @staticmethod
    def can_create_admin(admin: Admin, target_role: AdminRole) -> bool:
        """관리자 생성 권한 확인"""
        if admin.role == AdminRole.super_admin:
            return True
        elif admin.role == AdminRole.admin:
            # 관리자는 모더레이터만 생성 가능
            return target_role == AdminRole.moderator
        return False
    
    @staticmethod
    def can_delete_admin(admin: Admin, target_admin: Admin) -> bool:
        """관리자 삭제 권한 확인"""
        if admin.role == AdminRole.super_admin:
            # 최고 관리자는 자신을 제외한 모든 관리자 삭제 가능
            return admin.id != target_admin.id
        elif admin.role == AdminRole.admin:
            # 관리자는 모더레이터만 삭제 가능
            return target_admin.role == AdminRole.moderator
        return False
    
    @staticmethod
    def can_approve_counselor(admin: Admin) -> bool:
        """상담사 승인 권한 확인"""
        return admin.role in [AdminRole.admin, AdminRole.super_admin]
    
    @staticmethod
    def can_manage_counselor(admin: Admin) -> bool:
        """상담사 관리 권한 확인"""
        return admin.role in [AdminRole.moderator, AdminRole.admin, AdminRole.super_admin]
    
    @staticmethod
    def can_view_admin_logs(admin: Admin) -> bool:
        """관리자 로그 조회 권한 확인"""
        return admin.role in [AdminRole.admin, AdminRole.super_admin]