"""
User profile models: UserProfile, UserEducation, UserExperience, UserSkill, UserCertification.
"""

import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True
    )

    # Personal info
    headline: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Professional
    current_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    years_of_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Links
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Preferences
    desired_salary_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    desired_salary_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    willing_to_relocate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    work_authorization: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    requires_sponsorship: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Metadata
    profile_completeness: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")
    education: Mapped[List["UserEducation"]] = relationship(
        "UserEducation", back_populates="profile", cascade="all, delete-orphan",
        order_by="desc(UserEducation.start_date)"
    )
    experience: Mapped[List["UserExperience"]] = relationship(
        "UserExperience", back_populates="profile", cascade="all, delete-orphan",
        order_by="desc(UserExperience.start_date)"
    )
    skills: Mapped[List["UserSkill"]] = relationship(
        "UserSkill", back_populates="profile", cascade="all, delete-orphan"
    )
    certifications: Mapped[List["UserCertification"]] = relationship(
        "UserCertification", back_populates="profile", cascade="all, delete-orphan",
        order_by="desc(UserCertification.issue_date)"
    )

    def __repr__(self) -> str:
        return f"<UserProfile(user_id={self.user_id}, headline={self.headline})>"


class UserEducation(Base):
    __tablename__ = "user_education"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    institution: Mapped[str] = mapped_column(String(500), nullable=False)
    degree: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    field_of_study: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    gpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    activities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    profile: Mapped["UserProfile"] = relationship("UserProfile", back_populates="education")

    def __repr__(self) -> str:
        return f"<UserEducation(institution={self.institution}, degree={self.degree})>"


class UserExperience(Base):
    __tablename__ = "user_experience"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    company: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    employment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responsibilities: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    achievements: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    technologies: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Relationships
    profile: Mapped["UserProfile"] = relationship("UserProfile", back_populates="experience")

    def __repr__(self) -> str:
        return f"<UserExperience(company={self.company}, title={self.title})>"


class UserSkill(Base):
    __tablename__ = "user_skills"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    proficiency_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    years_of_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    endorsements_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    profile: Mapped["UserProfile"] = relationship("UserProfile", back_populates="skills")

    def __repr__(self) -> str:
        return f"<UserSkill(name={self.name}, level={self.proficiency_level})>"


class UserCertification(Base):
    __tablename__ = "user_certifications"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    issuing_organization: Mapped[str] = mapped_column(String(500), nullable=False)
    credential_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    credential_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    does_not_expire: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    profile: Mapped["UserProfile"] = relationship("UserProfile", back_populates="certifications")

    def __repr__(self) -> str:
        return f"<UserCertification(name={self.name}, org={self.issuing_organization})>"
