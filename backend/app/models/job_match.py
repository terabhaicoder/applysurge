"""
JobMatch model for storing AI-generated job matches with scores.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class JobMatch(Base):
    __tablename__ = "job_matches"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Match scores
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    skills_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    experience_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    education_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    salary_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    culture_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # AI analysis
    match_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    strengths: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    gaps: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    recommendations: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    matched_skills: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    missing_skills: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    ai_cover_letter_suggestions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Scoring metadata
    scoring_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    scoring_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    scored_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # User interaction
    is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    user_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50), default="new", nullable=False, index=True
    )
    viewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    bookmarked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    applied_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Resume used for matching
    resume_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="job_matches")
    job: Mapped["Job"] = relationship("Job", back_populates="matches")

    def __repr__(self) -> str:
        return f"<JobMatch(user_id={self.user_id}, job_id={self.job_id}, score={self.overall_score})>"
