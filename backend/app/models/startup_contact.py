"""
SQLAlchemy model for tracking startup outreach contacts and interactions.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StartupContact(Base):
    __tablename__ = "startup_contacts"

    # Foreign Keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Company Information
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    company_website: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    company_industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    company_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    company_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    company_tech_stack: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    funding_stage: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    funding_amount: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Contact Information
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    contact_linkedin: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    contact_source: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    contact_confidence_score: Mapped[Optional[float]] = mapped_column(
        nullable=True,
    )

    # Careers Page Information
    careers_page_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    open_roles: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSONB, nullable=True)
    matched_roles: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSONB, nullable=True)
    application_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Discovery Source
    discovery_source: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    discovery_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Outreach Status
    outreach_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="discovered",
        index=True,
    )
    email_subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    email_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    email_opened_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    email_clicked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    response_received_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    response_sentiment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Followup Tracking
    followup_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_followup_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_followup_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sendgrid_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="startup_contacts")

    def __repr__(self) -> str:
        return f"<StartupContact(id={self.id}, company={self.company_name}, status={self.outreach_status})>"


class StartupOutreachSettings(Base):
    __tablename__ = "startup_outreach_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Discovery Preferences
    target_industries: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    target_company_sizes: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    target_funding_stages: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    target_locations: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    target_tech_stacks: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    keywords: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    excluded_companies: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)

    # Outreach Preferences
    max_emails_per_day: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    outreach_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_send: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preferred_contact_titles: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    email_tone: Mapped[str] = mapped_column(String(50), default="professional", nullable=False)
    include_portfolio_link: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Schedule
    outreach_days: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=lambda: ["monday", "tuesday", "wednesday", "thursday", "friday"]
    )
    outreach_start_hour: Mapped[int] = mapped_column(Integer, default=9, nullable=False)
    outreach_end_hour: Mapped[int] = mapped_column(Integer, default=17, nullable=False)

    # Source Preferences
    use_yc_directory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    use_product_hunt: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    use_linkedin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    use_angellist: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="startup_outreach_settings")

    def __repr__(self) -> str:
        return f"<StartupOutreachSettings(user_id={self.user_id}, enabled={self.outreach_enabled})>"
