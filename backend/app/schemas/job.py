"""
Job listing schemas.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JobResponse(BaseModel):
    """Schema for job listing response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    company: str
    location: Optional[str] = None
    remote_type: Optional[str] = None
    is_remote: bool = False
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    salary_text: Optional[str] = None
    description: Optional[str] = None
    description_html: Optional[str] = None
    requirements: Optional[List[str]] = None
    responsibilities: Optional[List[str]] = None
    qualifications: Optional[List[str]] = None
    nice_to_have: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    company_logo_url: Optional[str] = None
    company_size: Optional[str] = None
    company_industry: Optional[str] = None
    applicant_count: Optional[int] = None
    is_easy_apply: bool = False
    is_saved: bool = False
    is_hidden: bool = False
    is_queued: bool = False
    match_score: Optional[float] = None
    match_reasoning: Optional[str] = None
    strengths: Optional[List[str]] = None
    gaps: Optional[List[str]] = None
    matched_skills: Optional[List[str]] = None
    missing_skills: Optional[List[str]] = None
    posted_at: Optional[datetime] = None
    created_at: datetime


class JobListFilters(BaseModel):
    """Schema for job listing filters."""
    search: Optional[str] = None
    location: Optional[str] = None
    remote_type: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    company: Optional[str] = None
    source: Optional[str] = None
    posted_after: Optional[datetime] = None
    skills: Optional[List[str]] = None
    sort_by: str = Field(default="posted_at", pattern="^(posted_at|match_score|salary_max|company)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class JobQueueItem(BaseModel):
    """Schema for a queued job item."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    user_id: UUID
    job: JobResponse
    priority: int = 0
    status: str = "pending"
    created_at: datetime
