"""
Profile, education, experience, skills, and certifications schemas.
"""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class EducationCreate(BaseModel):
    """Schema for creating education entry."""
    institution: str = Field(..., max_length=255)
    degree: str = Field(..., max_length=255)
    field_of_study: Optional[str] = Field(None, max_length=255)
    start_date: date
    end_date: Optional[date] = None
    gpa: Optional[float] = Field(None, ge=0, le=4.0)
    description: Optional[str] = None
    is_current: bool = False


class EducationUpdate(BaseModel):
    """Schema for updating education entry."""
    institution: Optional[str] = Field(None, max_length=255)
    degree: Optional[str] = Field(None, max_length=255)
    field_of_study: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gpa: Optional[float] = Field(None, ge=0, le=4.0)
    description: Optional[str] = None
    is_current: Optional[bool] = None


class EducationResponse(BaseModel):
    """Schema for education response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    gpa: Optional[float] = None
    description: Optional[str] = None
    is_current: bool = False


class ExperienceCreate(BaseModel):
    """Schema for creating experience entry."""
    company: str = Field(..., max_length=255)
    title: str = Field(..., max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None
    is_current: bool = False


class ExperienceUpdate(BaseModel):
    """Schema for updating experience entry."""
    company: Optional[str] = Field(None, max_length=255)
    title: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    is_current: Optional[bool] = None


class ExperienceResponse(BaseModel):
    """Schema for experience response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company: str
    title: str
    location: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None
    is_current: bool = False


class SkillCreate(BaseModel):
    """Schema for creating a skill."""
    name: str = Field(..., max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    proficiency_level: Optional[int] = Field(None, ge=1, le=5)


class SkillResponse(BaseModel):
    """Schema for skill response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    category: Optional[str] = None
    proficiency_level: Optional[int] = None


class CertificationCreate(BaseModel):
    """Schema for creating a certification."""
    name: str = Field(..., max_length=255)
    issuing_organization: str = Field(..., max_length=255)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = Field(None, max_length=255)
    credential_url: Optional[str] = None


class CertificationUpdate(BaseModel):
    """Schema for updating a certification."""
    name: Optional[str] = Field(None, max_length=255)
    issuing_organization: Optional[str] = Field(None, max_length=255)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = Field(None, max_length=255)
    credential_url: Optional[str] = None


class CertificationResponse(BaseModel):
    """Schema for certification response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    issuing_organization: str
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None


class ProfileCreate(BaseModel):
    """Schema for creating a profile."""
    headline: Optional[str] = Field(None, max_length=255)
    summary: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=255)
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    years_of_experience: Optional[int] = Field(None, ge=0)


class ProfileUpdate(BaseModel):
    """Schema for updating a profile."""
    headline: Optional[str] = Field(None, max_length=255)
    summary: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=30)
    location: Optional[str] = Field(None, max_length=255)
    current_title: Optional[str] = Field(None, max_length=255)
    current_company: Optional[str] = Field(None, max_length=255)
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    years_of_experience: Optional[int] = Field(None, ge=0)


class ProfileResponse(BaseModel):
    """Schema for profile response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    headline: Optional[str] = None
    summary: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    years_of_experience: Optional[int] = None
    education: List[EducationResponse] = []
    experience: List[ExperienceResponse] = []
    skills: List[SkillResponse] = []
    certifications: List[CertificationResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
