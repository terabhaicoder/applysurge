"""
Analytics models: DailyStats and Export.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DailyStats(Base):
    __tablename__ = "daily_stats"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Date for this stats record
    stats_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Job discovery
    jobs_discovered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    jobs_matched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    jobs_bookmarked: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    jobs_dismissed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Applications
    applications_sent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    applications_pending: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    applications_reviewed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    applications_rejected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    applications_interview: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    applications_offered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    applications_withdrawn: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    applications_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Match scores
    avg_match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Response metrics
    responses_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    positive_responses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    response_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_response_time_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Agent activity
    agent_runs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    agent_errors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    agent_runtime_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Emails
    emails_sent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    emails_opened: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    emails_replied: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    follow_ups_sent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Platform breakdown
    platform_stats: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    skill_demand: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    location_breakdown: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    salary_stats: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Extra
    extra_metrics: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="daily_stats")

    def __repr__(self) -> str:
        return f"<DailyStats(user_id={self.user_id}, date={self.stats_date})>"


class Export(Base):
    __tablename__ = "exports"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Export info
    export_type: Mapped[str] = mapped_column(String(50), nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="csv")
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False, index=True
    )

    # File info
    file_name: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # Filters and parameters
    filters: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    date_range_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_range_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    include_fields: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    exclude_fields: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Progress
    total_records: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    processed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Completion
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Download tracking
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_downloaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Extra
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="exports")

    def __repr__(self) -> str:
        return f"<Export(id={self.id}, type={self.export_type}, status={self.status})>"
