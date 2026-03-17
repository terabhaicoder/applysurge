"""
User CRUD operations service.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, NotFoundError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.models.application import Application
from app.models.resume import Resume
from app.schemas.user import UserResponse, UserUpdate, UserUsageResponse


class UserService:
    """Service for user operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user(self, user_id: UUID) -> UserResponse:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User")
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: UUID, data: UserUpdate) -> UserResponse:
        """Update user profile fields."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)

        await self.db.flush()
        await self.db.refresh(user)

        return UserResponse.model_validate(user)

    async def delete_user(self, user_id: UUID) -> bool:
        """Soft-delete a user account by deactivating it."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User")

        user.is_active = False
        await self.db.flush()

        return True

    async def change_password(
        self, user_id: UUID, current_password: str, new_password: str
    ) -> bool:
        """Change user password."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User")

        if not user.hashed_password or not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")

        user.hashed_password = hash_password(new_password)
        await self.db.flush()

        return True

    @staticmethod
    async def check_beta_quota(db: AsyncSession, user_id: UUID, user_email: str = "") -> tuple[bool, int, int]:
        """Check if user has remaining beta application quota.
        Returns: (has_quota, total_used, limit)
        Admin emails are exempt (unlimited).
        """
        if user_email.lower() in settings.admin_email_list:
            return (True, 0, 999999)

        result = await db.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
            )
        )
        total = result.scalar() or 0
        limit = settings.BETA_MAX_TOTAL_APPLICATIONS
        return (total < limit, total, limit)

    async def get_usage(self, user_id: UUID) -> UserUsageResponse:
        """Get user usage statistics."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Applications today
        result = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.created_at >= today_start,
                )
            )
        )
        applications_today = result.scalar() or 0

        # Applications this month
        result = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.created_at >= month_start,
                )
            )
        )
        applications_this_month = result.scalar() or 0

        # Total applications (all-time)
        result = await self.db.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
            )
        )
        applications_total = result.scalar() or 0

        # Resume count
        result = await self.db.execute(
            select(func.count(Resume.id)).where(Resume.user_id == user_id)
        )
        resumes_count = result.scalar() or 0

        beta_limit = settings.BETA_MAX_TOTAL_APPLICATIONS

        return UserUsageResponse(
            applications_today=applications_today,
            applications_this_month=applications_this_month,
            applications_total=applications_total,
            applications_limit_total=beta_limit,
            beta_quota_remaining=max(0, beta_limit - applications_total),
            resumes_count=resumes_count,
        )
