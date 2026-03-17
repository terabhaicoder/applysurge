"""
Authentication endpoints: register, login, logout, token refresh, password reset, OAuth.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db, rate_limit
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.user import (
    ForgotPasswordRequest,
    GoogleAuthRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit)],
)
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account and send verification email."""
    service = AuthService(db)
    user = await service.register(
        email=data.email,
        password=data.password,
        full_name=data.full_name,
    )

    # Generate verification token (email sending handled separately)
    await service.create_email_verification_token(user.id)

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit)],
)
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return access + refresh tokens."""
    service = AuthService(db)
    return await service.login(email=data.email, password=data.password)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Revoke the refresh token."""
    service = AuthService(db)
    await service.logout(data.refresh_token)
    return MessageResponse(message="Successfully logged out")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using a valid refresh token."""
    service = AuthService(db)
    return await service.refresh_access_token(data.refresh_token)


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    dependencies=[Depends(rate_limit)],
)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send password reset email if the account exists."""
    service = AuthService(db)
    await service.forgot_password(data.email)
    # Always return success to prevent email enumeration
    return MessageResponse(message="If an account exists with that email, a reset link has been sent")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using the reset token."""
    service = AuthService(db)
    await service.reset_password(token=data.token, new_password=data.new_password)
    return MessageResponse(message="Password reset successfully")


@router.get("/verify-email/{token}", response_model=MessageResponse)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Verify user email address with the provided token."""
    service = AuthService(db)
    await service.verify_email(token)
    return MessageResponse(message="Email verified successfully")


@router.post("/google", response_model=TokenResponse)
async def google_auth(
    data: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate or register via Google OAuth."""
    service = AuthService(db)
    return await service.google_auth(data.id_token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    """Get current authenticated user."""
    return UserResponse.model_validate(current_user)
