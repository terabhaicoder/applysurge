"""
Platform credentials schemas.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CredentialCreate(BaseModel):
    """Schema for creating platform credentials."""
    username: str = Field(..., min_length=1, max_length=255, strip_whitespace=True)
    password: str = Field(..., min_length=1, max_length=255)


class CredentialCreateCookie(BaseModel):
    """Schema for cookie-based authentication (e.g. LinkedIn li_at cookie)."""
    cookie: str = Field(..., min_length=10, max_length=1024, strip_whitespace=True)


class CredentialResponse(BaseModel):
    """Schema for credential response (no password exposed)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    platform: str
    username: str
    is_valid: bool = False
    has_cookie: bool = False
    auth_method: str = "password"
    last_validated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class CredentialDetailResponse(BaseModel):
    """Schema for credential detail with decrypted password (for edit form)."""
    platform: str
    email: str
    password: str
    has_cookie: bool = False
    masked_cookie: str = ""
    auth_method: str = "password"


class CredentialValidateResponse(BaseModel):
    """Schema for credential validation result."""
    platform: str
    is_valid: bool
    message: str
