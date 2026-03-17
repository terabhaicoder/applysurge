"""
Application tracking schemas.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApplicationResponse(BaseModel):
    """Schema for application response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    job_id: UUID
    job_title: Optional[str] = None
    company: Optional[str] = None
    company_name: Optional[str] = None
    job_location: Optional[str] = None
    application_method: Optional[str] = None
    status: str = "pending"
    applied_at: Optional[datetime] = None
    resume_id: Optional[UUID] = None
    cover_letter: Optional[str] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    application_url: Optional[str] = None
    response_received: bool = False
    response_date: Optional[datetime] = None
    interview_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ApplicationStatusUpdate(BaseModel):
    """Schema for updating application status."""
    status: str = Field(..., pattern="^(pending|applied|viewed|interview|offered|rejected|withdrawn|accepted)$")
    notes: Optional[str] = None


class ApplicationLogResponse(BaseModel):
    """Schema for application activity log."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    action: str
    details: Optional[dict] = None
    created_at: datetime


class ApplicationListFilters(BaseModel):
    """Filters for listing applications."""
    status: Optional[str] = None
    company: Optional[str] = None
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    source: Optional[str] = None
    sort_by: str = Field(default="created_at", pattern="^(created_at|applied_at|status|company)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class ApplicationStatsResponse(BaseModel):
    """Schema for application statistics."""
    total: int = 0
    pending: int = 0
    applied: int = 0
    viewed: int = 0
    interview: int = 0
    offered: int = 0
    rejected: int = 0
    withdrawn: int = 0
    accepted: int = 0
    response_rate: float = 0.0
    avg_response_days: Optional[float] = None
