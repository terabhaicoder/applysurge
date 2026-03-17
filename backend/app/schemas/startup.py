"""
Pydantic schemas for startup outreach feature.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


# ============================================================
# Startup Contact Schemas
# ============================================================


class StartupContactBase(BaseModel):
    """Base schema for startup contact fields."""
    company_name: str = Field(..., min_length=1, max_length=255)
    company_website: Optional[str] = None
    company_industry: Optional[str] = None
    company_size: Optional[str] = None
    company_description: Optional[str] = None
    company_location: Optional[str] = None
    company_tech_stack: Optional[List[str]] = None
    funding_stage: Optional[str] = None
    funding_amount: Optional[str] = None


class StartupContactCreate(StartupContactBase):
    """Schema for creating a new startup contact."""
    contact_name: Optional[str] = None
    contact_title: Optional[str] = None
    contact_email: Optional[str] = None
    contact_linkedin: Optional[str] = None
    contact_source: Optional[str] = None
    careers_page_url: Optional[str] = None
    open_roles: Optional[List[Dict[str, Any]]] = None
    discovery_source: Optional[str] = None
    discovery_url: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class StartupContactUpdate(BaseModel):
    """Schema for updating a startup contact."""
    model_config = ConfigDict(from_attributes=True)

    company_name: Optional[str] = None
    company_website: Optional[str] = None
    company_industry: Optional[str] = None
    company_size: Optional[str] = None
    company_description: Optional[str] = None
    company_location: Optional[str] = None
    company_tech_stack: Optional[List[str]] = None
    funding_stage: Optional[str] = None
    funding_amount: Optional[str] = None
    contact_name: Optional[str] = None
    contact_title: Optional[str] = None
    contact_email: Optional[str] = None
    contact_linkedin: Optional[str] = None
    contact_source: Optional[str] = None
    careers_page_url: Optional[str] = None
    open_roles: Optional[List[Dict[str, Any]]] = None
    outreach_status: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    is_archived: Optional[bool] = None


class StartupContactResponse(StartupContactBase):
    """Schema for returning a startup contact."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    contact_name: Optional[str] = None
    contact_title: Optional[str] = None
    contact_email: Optional[str] = None
    contact_linkedin: Optional[str] = None
    contact_source: Optional[str] = None
    contact_confidence_score: Optional[float] = None
    careers_page_url: Optional[str] = None
    open_roles: Optional[List[Dict[str, Any]]] = None
    matched_roles: Optional[List[Dict[str, Any]]] = None
    application_instructions: Optional[str] = None
    discovery_source: Optional[str] = None
    discovery_url: Optional[str] = None
    outreach_status: str
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    email_sent_at: Optional[datetime] = None
    email_opened_at: Optional[datetime] = None
    email_clicked_at: Optional[datetime] = None
    response_received_at: Optional[datetime] = None
    response_sentiment: Optional[str] = None
    followup_count: int = 0
    last_followup_at: Optional[datetime] = None
    next_followup_at: Optional[datetime] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime


class StartupContactList(BaseModel):
    """Paginated list of startup contacts."""
    model_config = ConfigDict(from_attributes=True)

    items: List[StartupContactResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================
# Outreach Settings Schemas
# ============================================================


class StartupOutreachSettingsBase(BaseModel):
    """Base schema for outreach settings."""
    target_industries: Optional[List[str]] = None
    target_company_sizes: Optional[List[str]] = None
    target_funding_stages: Optional[List[str]] = None
    target_locations: Optional[List[str]] = None
    target_tech_stacks: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    excluded_companies: Optional[List[str]] = None
    max_emails_per_day: int = Field(default=20, ge=1, le=50)
    outreach_enabled: bool = False
    auto_send: bool = False
    preferred_contact_titles: Optional[List[str]] = None
    email_tone: str = Field(default="professional", pattern="^(professional|casual|enthusiastic)$")
    include_portfolio_link: bool = True
    portfolio_url: Optional[str] = None
    outreach_days: Optional[List[str]] = None
    outreach_start_hour: int = Field(default=9, ge=0, le=23)
    outreach_end_hour: int = Field(default=17, ge=0, le=23)
    use_yc_directory: bool = True
    use_product_hunt: bool = True
    use_linkedin: bool = False
    use_angellist: bool = True


class StartupOutreachSettingsCreate(StartupOutreachSettingsBase):
    """Schema for creating outreach settings."""
    pass


class StartupOutreachSettingsUpdate(BaseModel):
    """Schema for updating outreach settings."""
    model_config = ConfigDict(from_attributes=True)

    target_industries: Optional[List[str]] = None
    target_company_sizes: Optional[List[str]] = None
    target_funding_stages: Optional[List[str]] = None
    target_locations: Optional[List[str]] = None
    target_tech_stacks: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    excluded_companies: Optional[List[str]] = None
    max_emails_per_day: Optional[int] = Field(default=None, ge=1, le=50)
    outreach_enabled: Optional[bool] = None
    auto_send: Optional[bool] = None
    preferred_contact_titles: Optional[List[str]] = None
    email_tone: Optional[str] = None
    include_portfolio_link: Optional[bool] = None
    portfolio_url: Optional[str] = None
    outreach_days: Optional[List[str]] = None
    outreach_start_hour: Optional[int] = Field(default=None, ge=0, le=23)
    outreach_end_hour: Optional[int] = Field(default=None, ge=0, le=23)
    use_yc_directory: Optional[bool] = None
    use_product_hunt: Optional[bool] = None
    use_linkedin: Optional[bool] = None
    use_angellist: Optional[bool] = None


class StartupOutreachSettingsResponse(StartupOutreachSettingsBase):
    """Schema for returning outreach settings."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


# ============================================================
# Search and Filter Schemas
# ============================================================


class StartupSearchFilters(BaseModel):
    """Filters for searching startup contacts."""
    industries: Optional[List[str]] = None
    company_sizes: Optional[List[str]] = None
    funding_stages: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    outreach_statuses: Optional[List[str]] = None
    discovery_sources: Optional[List[str]] = None
    has_contact_email: Optional[bool] = None
    has_open_roles: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search_query: Optional[str] = None
    is_archived: bool = False
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="created_at", pattern="^(created_at|company_name|outreach_status|funding_stage)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


# ============================================================
# Discovery Trigger Schemas
# ============================================================


class StartupDiscoveryRequest(BaseModel):
    """Request to trigger startup discovery."""
    sources: Optional[List[str]] = Field(
        default=None,
        description="Sources to search: yc, product_hunt, linkedin, angellist"
    )
    industries: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    max_results: int = Field(default=50, ge=1, le=200)


class StartupDiscoveryResponse(BaseModel):
    """Response from startup discovery trigger."""
    task_id: str
    message: str
    estimated_results: Optional[int] = None


# ============================================================
# Outreach Trigger Schemas
# ============================================================


class StartupOutreachRequest(BaseModel):
    """Request to send outreach to a specific startup."""
    custom_message: Optional[str] = None
    include_resume: bool = True
    email_type: str = Field(
        default="startup_outreach",
        pattern="^(startup_outreach|role_interest)$"
    )


class StartupOutreachResponse(BaseModel):
    """Response from outreach trigger."""
    success: bool
    message: str
    email_subject: Optional[str] = None
    email_preview: Optional[str] = None
    contact_email: Optional[str] = None
    sent_at: Optional[datetime] = None


# ============================================================
# Status Update Schema
# ============================================================


class StartupStatusUpdate(BaseModel):
    """Schema for updating outreach status."""
    outreach_status: str = Field(
        ...,
        pattern="^(discovered|contacted|responded|not_interested|interview|archived)$"
    )
    notes: Optional[str] = None


# ============================================================
# Statistics Schema
# ============================================================


class StartupOutreachStats(BaseModel):
    """Statistics for startup outreach."""
    total_discovered: int = 0
    total_contacted: int = 0
    total_responded: int = 0
    total_not_interested: int = 0
    total_interviews: int = 0
    response_rate: float = 0.0
    emails_sent_today: int = 0
    emails_remaining_today: int = 20
    top_industries: List[Dict[str, Any]] = []
    top_sources: List[Dict[str, Any]] = []
    weekly_outreach: List[Dict[str, Any]] = []
    avg_response_time_hours: Optional[float] = None
