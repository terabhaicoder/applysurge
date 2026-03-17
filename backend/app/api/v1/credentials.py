"""
Platform credentials management endpoints.
"""

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.core.exceptions import NotFoundError
from app.models.credentials import PlatformCredentials
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.credentials import (
    CredentialCreate,
    CredentialDetailResponse,
    CredentialResponse,
    CredentialValidateResponse,
)

router = APIRouter()


@router.get("/", response_model=list[CredentialResponse])
async def list_credentials(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all stored platform credentials (passwords masked)."""
    result = await db.execute(
        select(PlatformCredentials).where(
            PlatformCredentials.user_id == current_user.id
        )
    )
    creds = result.scalars().all()
    return [_to_credential_response(c) for c in creds]


@router.post(
    "/linkedin",
    response_model=CredentialResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_linkedin_credentials(
    data: CredentialCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Store LinkedIn credentials."""
    return await _add_credential(db, current_user.id, "linkedin", data)


@router.post(
    "/naukri",
    response_model=CredentialResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_naukri_credentials(
    data: CredentialCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Store Naukri credentials."""
    return await _add_credential(db, current_user.id, "naukri", data)


@router.get("/{platform}/detail", response_model=CredentialDetailResponse)
async def get_credential_detail(
    platform: Literal["linkedin", "naukri"],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get stored credentials with decrypted password for editing."""
    result = await db.execute(
        select(PlatformCredentials).where(
            PlatformCredentials.user_id == current_user.id,
            PlatformCredentials.platform == platform,
        )
    )
    cred = result.scalar_one_or_none()
    if not cred:
        raise NotFoundError(f"Credentials for {platform}")

    return CredentialDetailResponse(
        platform=cred.platform,
        email=cred.platform_email or cred.platform_username or "",
        password=cred.get_password() or "",
    )


@router.delete("/{platform}", response_model=MessageResponse)
async def delete_credentials(
    platform: Literal["linkedin", "naukri"],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete stored credentials for a platform."""
    result = await db.execute(
        select(PlatformCredentials).where(
            PlatformCredentials.user_id == current_user.id,
            PlatformCredentials.platform == platform,
        )
    )
    cred = result.scalar_one_or_none()
    if not cred:
        raise NotFoundError(f"Credentials for {platform}")

    await db.delete(cred)
    await db.flush()
    return MessageResponse(message=f"{platform.title()} credentials deleted")


@router.post("/{platform}/validate", response_model=CredentialValidateResponse)
async def validate_credentials(
    platform: Literal["linkedin", "naukri"],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Validate stored credentials by dispatching a real login test."""
    result = await db.execute(
        select(PlatformCredentials).where(
            PlatformCredentials.user_id == current_user.id,
            PlatformCredentials.platform == platform,
        )
    )
    cred = result.scalar_one_or_none()
    if not cred:
        raise NotFoundError(f"Credentials for {platform}")

    # Dispatch Celery task to perform real login validation
    try:
        from worker.tasks.agent_tasks import validate_credentials_task
        validate_credentials_task.delay(str(current_user.id), platform)
    except ImportError:
        pass  # Worker module may not be available in API context

    return CredentialValidateResponse(
        platform=platform,
        is_valid=False,
        message="Validation in progress. Check back shortly for results.",
    )


async def _add_credential(
    db: AsyncSession,
    user_id: UUID,
    platform: str,
    data: CredentialCreate,
) -> CredentialResponse:
    """Helper to add or update platform credentials."""
    result = await db.execute(
        select(PlatformCredentials).where(
            PlatformCredentials.user_id == user_id,
            PlatformCredentials.platform == platform,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.platform_username = data.username
        existing.platform_email = data.username  # Store in both fields for discovery lookups
        existing.set_password(data.password)
        existing.is_verified = False
        await db.flush()
        await db.refresh(existing)
        return _to_credential_response(existing)

    cred = PlatformCredentials(
        user_id=user_id,
        platform=platform,
        platform_username=data.username,
        platform_email=data.username,  # Store in both fields for discovery lookups
    )
    cred.set_password(data.password)
    db.add(cred)
    await db.flush()
    await db.refresh(cred)
    return _to_credential_response(cred)


def _to_credential_response(cred: PlatformCredentials) -> CredentialResponse:
    """Convert model to response schema."""
    return CredentialResponse(
        id=cred.id,
        user_id=cred.user_id,
        platform=cred.platform,
        username=cred.platform_username or "",
        is_valid=cred.is_verified,
        last_validated_at=cred.last_verified_at,
        created_at=cred.created_at,
        updated_at=cred.updated_at,
    )
