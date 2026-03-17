"""
Authentication service handling registration, login, token management, and password reset.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_verification_token,
    hash_password,
    verify_password,
    verify_refresh_token,
    verify_verification_token,
)
from app.models.user import User
from app.schemas.user import TokenResponse, UserResponse


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, email: str, password: str, full_name: str) -> UserResponse:
        """Register a new user."""
        result = await self.db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ConflictError("User with this email already exists")

        hashed = hash_password(password)
        user = User(
            email=email,
            hashed_password=hashed,
            full_name=full_name,
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        return UserResponse.model_validate(user)

    async def create_email_verification_token(self, user_id: UUID) -> str:
        """Create an email verification token."""
        return create_verification_token(user_id, purpose="email_verification")

    async def verify_email(self, token: str) -> bool:
        """Verify a user's email with the provided token."""
        payload = verify_verification_token(token, purpose="email_verification")
        if not payload:
            raise ValidationError("Invalid or expired verification token")

        user_id = payload.get("sub")
        result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User")

        user.is_verified = True
        await self.db.flush()

        return True

    async def login(self, email: str, password: str) -> TokenResponse:
        """Authenticate user and return tokens."""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token."""
        payload = verify_refresh_token(refresh_token)
        if not payload:
            raise AuthenticationError("Invalid or expired refresh token")

        user_id = payload.get("sub")
        result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        new_access_token = create_access_token(user.id)
        new_refresh_token = create_refresh_token(user.id)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def logout(self, refresh_token: str) -> bool:
        """Revoke a refresh token."""
        payload = verify_refresh_token(refresh_token)
        if not payload:
            raise AuthenticationError("Invalid refresh token")
        # In production, add token jti to Redis blacklist
        return True

    async def forgot_password(self, email: str) -> Optional[str]:
        """Generate password reset token if user exists."""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            return None

        token = create_verification_token(user.id, purpose="password_reset")
        return token

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset user password with token."""
        payload = verify_verification_token(token, purpose="password_reset")
        if not payload:
            raise ValidationError("Invalid or expired reset token")

        user_id = payload.get("sub")
        result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User")

        user.hashed_password = hash_password(new_password)
        await self.db.flush()

        return True

    async def google_auth(self, id_token: str) -> TokenResponse:
        """Authenticate or register via Google OAuth."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
            )

        if response.status_code != 200:
            raise AuthenticationError("Invalid Google token")

        google_data = response.json()
        email = google_data.get("email")
        name = google_data.get("name", "")

        if not email:
            raise AuthenticationError("Google account has no email")

        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                email=email,
                full_name=name,
                is_active=True,
                is_verified=True,
                google_id=google_data.get("sub"),
            )
            self.db.add(user)
            await self.db.flush()
            await self.db.refresh(user)
        elif not user.google_id:
            user.google_id = google_data.get("sub")

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
