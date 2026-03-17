"""
Job model for storing scraped/discovered job listings.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    # Source information
    platform: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    platform_job_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    apply_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # Job details
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    company: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    company_logo_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    company_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    company_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    company_industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Location
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    city: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    work_arrangement: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requirements: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    responsibilities: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    qualifications: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    nice_to_have: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    benefits: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Classification
    job_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    experience_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    function: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Compensation
    salary_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    salary_period: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    salary_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Skills and tags
    required_skills: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    preferred_skills: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    technologies: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Metadata
    posted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scraped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    applicant_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_easy_apply: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # AI-processed data
    embedding_vector: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_parsed_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Extra data
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    matches: Mapped[list["JobMatch"]] = relationship(
        "JobMatch", back_populates="job", cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(
        "Application", back_populates="job", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, title={self.title}, company={self.company})>"
