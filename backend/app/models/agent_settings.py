"""
AgentSettings model for automation agent configuration per user.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AgentSettings(Base):
    __tablename__ = "agent_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True
    )

    # Agent status
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_running: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_error_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    consecutive_errors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Schedule
    run_schedule: Mapped[str] = mapped_column(String(50), default="daily", nullable=False)
    run_time_utc: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    run_days: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)

    # Application limits
    max_applications_per_day: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    max_applications_per_week: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    max_applications_per_month: Mapped[int] = mapped_column(Integer, default=150, nullable=False)
    applications_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    applications_this_week: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    applications_this_month: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_applications: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Matching criteria
    min_match_score: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    auto_apply_threshold: Mapped[float] = mapped_column(Float, default=0.85, nullable=False)
    require_salary_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    require_location_match: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    require_experience_match: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Application behavior
    auto_generate_cover_letter: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tailor_resume: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    answer_screening_questions: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    skip_already_applied: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    apply_to_easy_apply_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Platform preferences
    enabled_platforms: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    platform_priorities: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # AI settings
    ai_model_preference: Mapped[str] = mapped_column(String(100), default="gpt-4o", nullable=False)
    cover_letter_style: Mapped[str] = mapped_column(String(50), default="professional", nullable=False)
    cover_letter_tone: Mapped[str] = mapped_column(String(50), default="confident", nullable=False)
    cover_letter_length: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    custom_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Notification settings
    notify_on_apply: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_on_error: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_on_match: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notification_channels: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Cooldown and rate limiting
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    retry_delay_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    # Browser/session settings
    use_proxy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    proxy_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    user_agent_rotation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    headless_mode: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Statistics
    success_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_time_per_application: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Extra settings
    extra_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="agent_settings")

    def __repr__(self) -> str:
        return f"<AgentSettings(user_id={self.user_id}, enabled={self.is_enabled})>"

    def can_apply_today(self) -> bool:
        """Check if the agent can still apply today based on limits."""
        return self.applications_today < self.max_applications_per_day

    def can_apply_this_week(self) -> bool:
        """Check if the agent can still apply this week based on limits."""
        return self.applications_this_week < self.max_applications_per_week

    def increment_application_count(self) -> None:
        """Increment all application counters."""
        self.applications_today += 1
        self.applications_this_week += 1
        self.applications_this_month += 1
        self.total_applications += 1
