"""
EmailTemplate model for user-customizable email templates.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Template identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(
        String(100), default="general", nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Template content
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Template variables
    available_variables: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    default_variables: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Usage tracking
    times_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # AI generation metadata
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Version control
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    parent_template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Tags and metadata
    tags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="email_templates")

    def __repr__(self) -> str:
        return f"<EmailTemplate(id={self.id}, name={self.name}, category={self.category})>"

    def render(self, variables: dict) -> tuple[str, str]:
        """
        Render the template with provided variables.

        Args:
            variables: Dictionary of variable names to values.

        Returns:
            Tuple of (rendered_subject, rendered_body_text).
        """
        rendered_subject = self.subject
        rendered_body = self.body_text
        rendered_html = self.body_html or ""

        merged_vars = {}
        if self.default_variables:
            merged_vars.update(self.default_variables)
        merged_vars.update(variables)

        for key, value in merged_vars.items():
            placeholder = "{{" + key + "}}"
            str_value = str(value) if value is not None else ""
            rendered_subject = rendered_subject.replace(placeholder, str_value)
            rendered_body = rendered_body.replace(placeholder, str_value)
            rendered_html = rendered_html.replace(placeholder, str_value)

        return rendered_subject, rendered_body
