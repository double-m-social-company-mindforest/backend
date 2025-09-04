from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.auth import (
    SignupRequest,
    SignupResponse,
    LoginRequest,
    LoginResponse,
    CheckNicknameRequest,
    CheckNicknameResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutResponse,
    UserInfo
)
from services.auth.auth_service import (
    create_user,
    check_nickname_availability,
    login_user,
    refresh_access_token,
    logout_user
)
from services.auth.jwt_service import get_current_active_user
from models.user import User


router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)


@router.post("/signup", response_model=SignupResponse)
async def signup(
    request: SignupRequest,
    db: Session = Depends(get_db)
):
    """
    회원가입 API
    
    - nickname: 사용자 닉네임 (중복 불가)
    - password: 비밀번호
    - password_confirm: 비밀번호 확인
    """
    try:
        user = create_user(db, request.nickname, request.password)
        return SignupResponse(
            status="success",
            message="회원가입이 완료되었습니다",
            data={
                "user_id": user.id,
                "nickname": user.nickname
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원가입 처리 중 오류가 발생했습니다"
        )


@router.post("/check-nickname", response_model=CheckNicknameResponse)
async def check_nickname(
    request: CheckNicknameRequest,
    db: Session = Depends(get_db)
):
    """
    닉네임 중복 확인 API
    
    - nickname: 확인할 닉네임
    """
    available = check_nickname_availability(db, request.nickname)
    return CheckNicknameResponse(
        status="success",
        data={"available": available}
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    로그인 API
    
    - nickname: 사용자 닉네임
    - password: 비밀번호
    """
    try:
        token_data = login_user(db, request.nickname, request.password)
        return LoginResponse(
            status="success",
            message="로그인 성공",
            data=token_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다"
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Access Token 갱신 API
    
    - refresh_token: 리프레시 토큰
    """
    try:
        token_data = refresh_access_token(db, request.refresh_token)
        return RefreshTokenResponse(
            status="success",
            data=token_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="토큰 갱신 중 오류가 발생했습니다"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    로그아웃 API
    
    Authorization Header에 Bearer Token 필요
    """
    try:
        logout_user(db, current_user.id)
        return LogoutResponse(
            status="success",
            message="로그아웃 되었습니다"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그아웃 처리 중 오류가 발생했습니다"
        )


@router.get("/me", response_model=UserInfo)
async def get_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    현재 로그인한 사용자 정보 조회 API
    
    Authorization Header에 Bearer Token 필요
    """
    return UserInfo.from_orm(current_user)