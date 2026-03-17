"""
Resume model for storing user resume data and files.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Resume(Base):
    __tablename__ = "resumes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # File info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Parsed content
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parsed_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    sections: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # AI-extracted structured data
    extracted_skills: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    extracted_experience: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    extracted_education: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    extracted_certifications: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    extracted_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ats_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_parsed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Embedding for AI matching
    embedding_vector: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Tags and notes
    tags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="resumes")

    def __repr__(self) -> str:
        return f"<Resume(id={self.id}, title={self.title}, user_id={self.user_id})>"
