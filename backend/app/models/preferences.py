"""
Job preferences model for storing user job search preferences.
"""

import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class JobPreferences(Base):
    __tablename__ = "job_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True
    )

    # Job type preferences
    job_types: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    work_arrangements: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    experience_levels: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Role preferences
    desired_titles: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    desired_roles: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    industries: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Skills and keywords
    required_skills: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    preferred_skills: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    excluded_keywords: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    included_keywords: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Location preferences
    preferred_locations: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    excluded_locations: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    remote_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hybrid_ok: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_commute_miles: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Salary preferences
    min_salary: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_salary: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    salary_period: Mapped[str] = mapped_column(String(20), default="yearly", nullable=False)

    # Company preferences
    preferred_company_sizes: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    preferred_companies: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    excluded_companies: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    company_culture_preferences: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Benefits and perks
    required_benefits: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    preferred_benefits: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Search settings
    search_frequency: Mapped[str] = mapped_column(String(50), default="daily", nullable=False)
    auto_apply: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    min_match_score: Mapped[int] = mapped_column(Integer, default=70, nullable=False)
    max_applications_per_day: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    # Platform sources
    search_platforms: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    excluded_platforms: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Additional filters
    visa_sponsorship_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    security_clearance_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    travel_willingness: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Custom filters as JSON
    custom_filters: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="preferences")

    def __repr__(self) -> str:
        return f"<JobPreferences(user_id={self.user_id})>"
