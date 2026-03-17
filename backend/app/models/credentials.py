"""
Platform credentials model with encrypted storage for job platform logins.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.encryption import decrypt_value, encrypt_value
from app.db.base import Base


class PlatformCredentials(Base):
    __tablename__ = "platform_credentials"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Platform identification
    platform: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    platform_user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    platform_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    platform_email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)

    # Encrypted credentials
    encrypted_password: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    encrypted_access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    encrypted_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    encrypted_api_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    encrypted_cookies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # OAuth tokens
    oauth_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    oauth_scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_count: Mapped[int] = mapped_column(default=0, nullable=False)

    # Additional platform-specific data
    profile_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="credentials")

    def set_password(self, password: str) -> None:
        """Encrypt and store the platform password."""
        self.encrypted_password = encrypt_value(password)

    def get_password(self) -> Optional[str]:
        """Decrypt and return the platform password."""
        if self.encrypted_password:
            return decrypt_value(self.encrypted_password)
        return None

    def set_access_token(self, token: str) -> None:
        """Encrypt and store the access token."""
        self.encrypted_access_token = encrypt_value(token)

    def get_access_token(self) -> Optional[str]:
        """Decrypt and return the access token."""
        if self.encrypted_access_token:
            return decrypt_value(self.encrypted_access_token)
        return None

    def set_refresh_token(self, token: str) -> None:
        """Encrypt and store the refresh token."""
        self.encrypted_refresh_token = encrypt_value(token)

    def get_refresh_token(self) -> Optional[str]:
        """Decrypt and return the refresh token."""
        if self.encrypted_refresh_token:
            return decrypt_value(self.encrypted_refresh_token)
        return None

    def set_api_key(self, api_key: str) -> None:
        """Encrypt and store the API key."""
        self.encrypted_api_key = encrypt_value(api_key)

    def get_api_key(self) -> Optional[str]:
        """Decrypt and return the API key."""
        if self.encrypted_api_key:
            return decrypt_value(self.encrypted_api_key)
        return None

    def set_cookies(self, cookies: str) -> None:
        """Encrypt and store session cookies."""
        self.encrypted_cookies = encrypt_value(cookies)

    def get_cookies(self) -> Optional[str]:
        """Decrypt and return session cookies."""
        if self.encrypted_cookies:
            return decrypt_value(self.encrypted_cookies)
        return None

    def __repr__(self) -> str:
        return f"<PlatformCredentials(platform={self.platform}, user_id={self.user_id})>"
