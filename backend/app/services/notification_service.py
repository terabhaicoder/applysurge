"""
Notification creation and management service.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, update, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse, NotificationCountResponse


class NotificationService:
    """Service for notification operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_notifications(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
    ) -> Tuple[List[NotificationResponse], int]:
        """List notifications with pagination."""
        query = select(Notification).where(Notification.user_id == user_id)
        count_query = select(func.count(Notification.id)).where(
            Notification.user_id == user_id
        )

        if unread_only:
            query = query.where(Notification.is_read == False)
            count_query = count_query.where(Notification.is_read == False)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(desc(Notification.created_at)).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        notifications = result.scalars().all()

        return [self._to_response(n) for n in notifications], total

    async def get_unread_count(self, user_id: UUID) -> NotificationCountResponse:
        """Get count of unread notifications."""
        result = await self.db.execute(
            select(func.count(Notification.id)).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False,
                )
            )
        )
        count = result.scalar() or 0
        return NotificationCountResponse(unread_count=count)

    async def mark_as_read(self, user_id: UUID, notification_id: UUID) -> NotificationResponse:
        """Mark a notification as read."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()
        if not notification:
            raise NotFoundError("Notification")

        notification.mark_as_read()
        await self.db.flush()
        await self.db.refresh(notification)

        return self._to_response(notification)

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read. Returns count of updated."""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            update(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False,
                )
            )
            .values(is_read=True, read_at=now)
        )
        await self.db.flush()
        return result.rowcount

    async def create_notification(
        self,
        user_id: UUID,
        type: str,
        title: str,
        message: str,
        data: Optional[dict] = None,
    ) -> NotificationResponse:
        """Create a new notification."""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            extra_data=data,
        )
        self.db.add(notification)
        await self.db.flush()
        await self.db.refresh(notification)
        return self._to_response(notification)

    def _to_response(self, n: Notification) -> NotificationResponse:
        """Convert Notification model to response schema."""
        return NotificationResponse(
            id=n.id,
            user_id=n.user_id,
            type=n.type,
            title=n.title,
            message=n.message,
            data=n.extra_data,
            is_read=n.is_read,
            read_at=n.read_at,
            created_at=n.created_at,
        )
