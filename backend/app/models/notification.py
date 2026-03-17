"""
Notification model for in-app user notifications.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Notification type and category
    type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(
        String(50), default="general", nullable=False, index=True
    )
    priority: Mapped[str] = mapped_column(
        String(20), default="normal", nullable=False
    )

    # Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    message_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Action
    action_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    action_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    action_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Related entity
    related_entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    related_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Delivery
    channels_sent: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    push_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    websocket_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Metadata
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Expiry
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Grouping
    group_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    group_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type={self.type}, user_id={self.user_id})>"

    def mark_as_read(self) -> None:
        """Mark notification as read with current timestamp."""
        from datetime import timezone as tz
        self.is_read = True
        self.read_at = datetime.now(tz.utc)

    def dismiss(self) -> None:
        """Dismiss the notification."""
        from datetime import timezone as tz
        self.is_dismissed = True
        self.dismissed_at = datetime.now(tz.utc)
