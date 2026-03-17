"""
User management endpoints.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.user import (
    ChangePasswordRequest,
    UserResponse,
    UserUpdate,
    UserUsageResponse,
)
from app.services.user_service import UserService

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user details."""
    service = UserService(db)
    return await service.get_user(current_user.id)


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile fields."""
    service = UserService(db)
    return await service.update_user(current_user.id, data)


@router.delete("/me", status_code=status.HTTP_200_OK, response_model=MessageResponse)
async def delete_current_user(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete the current user's account."""
    service = UserService(db)
    await service.delete_user(current_user.id)
    return MessageResponse(message="Account deleted successfully")


@router.patch("/me/password", response_model=MessageResponse)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the current user's password."""
    service = UserService(db)
    await service.change_password(
        user_id=current_user.id,
        current_password=data.current_password,
        new_password=data.new_password,
    )
    return MessageResponse(message="Password changed successfully")


@router.get("/me/usage", response_model=UserUsageResponse)
async def get_user_usage(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's usage statistics and limits."""
    service = UserService(db)
    return await service.get_usage(current_user.id)
