"""
User schemas for authentication and user management.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    """Schema for Google OAuth login."""
    id_token: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh."""
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for password reset."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    """Schema for changing password."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class UserResponse(BaseModel):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    subscription_tier: str = "free"
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    avatar_url: Optional[str] = None


class UserUsageResponse(BaseModel):
    """Schema for user usage statistics."""
    model_config = ConfigDict(from_attributes=True)

    applications_today: int = 0
    applications_this_month: int = 0
    applications_total: int = 0
    applications_limit_daily: int = 50
    applications_limit_monthly: int = 500
    applications_limit_total: int = 10
    beta_quota_remaining: int = 10
    resumes_count: int = 0
    resumes_limit: int = 5
    agent_sessions_today: int = 0
    agent_sessions_limit: int = 3
