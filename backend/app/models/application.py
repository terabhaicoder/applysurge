"""
Application and ApplicationLog models for tracking job applications.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Application(Base):
    __tablename__ = "applications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Application status
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False, index=True
    )
    substatus: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Application method
    applied_via: Mapped[str] = mapped_column(String(50), default="agent", nullable=False)
    platform: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    application_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # Resume and cover letter
    resume_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True
    )
    cover_letter: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_letter_generated: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    custom_answers: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Tailored resume data
    tailored_resume_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    tailored_resume_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Match info at time of application
    match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    match_details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Dates
    applied_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    interview_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    offered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Response tracking
    response_received: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    response_received_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    follow_up_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_follow_up_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_follow_up_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Agent metadata
    agent_session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    agent_actions: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    agent_screenshots: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # User notes and feedback
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Extra data
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="applications")
    job: Mapped["Job"] = relationship("Job", back_populates="applications")
    logs: Mapped[List["ApplicationLog"]] = relationship(
        "ApplicationLog", back_populates="application", cascade="all, delete-orphan",
        order_by="desc(ApplicationLog.created_at)"
    )

    def __repr__(self) -> str:
        return f"<Application(id={self.id}, status={self.status}, user_id={self.user_id})>"


class ApplicationLog(Base):
    __tablename__ = "application_logs"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Log entry
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    status_from: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status_to: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Actor
    performed_by: Mapped[str] = mapped_column(
        String(50), default="system", nullable=False
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="logs")

    def __repr__(self) -> str:
        return f"<ApplicationLog(application_id={self.application_id}, action={self.action})>"
