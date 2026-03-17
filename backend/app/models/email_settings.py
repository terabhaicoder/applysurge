"""
EmailSettings model for user email configuration.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EmailSettings(Base):
    __tablename__ = "email_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True
    )

    # SMTP Configuration
    smtp_host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    smtp_port: Mapped[int] = mapped_column(Integer, default=587, nullable=False)
    smtp_username: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    encrypted_smtp_password: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    smtp_use_tls: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    smtp_use_ssl: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Sender info
    from_email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    from_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reply_to_email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)

    # Email signature
    signature_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    signature_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Provider settings (Gmail, Outlook, etc.)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    oauth_connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    encrypted_oauth_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    encrypted_oauth_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    oauth_token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Notification preferences
    send_application_confirmations: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    send_status_updates: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    send_match_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    send_weekly_digest: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    send_follow_up_reminders: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Follow-up settings
    auto_follow_up_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    follow_up_delay_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    max_follow_ups: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    follow_up_template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Rate limiting
    max_emails_per_day: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    emails_sent_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_email_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Status
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Extra configuration
    extra_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="email_settings")

    def __repr__(self) -> str:
        return f"<EmailSettings(user_id={self.user_id}, provider={self.provider})>"
