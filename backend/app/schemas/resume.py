"""
Resume schemas for upload and management.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ResumeCreate(BaseModel):
    """Schema for resume upload metadata."""
    title: str = Field(..., max_length=255)
    is_default: bool = False


class ResumeUpdate(BaseModel):
    """Schema for updating resume metadata."""
    title: Optional[str] = Field(None, max_length=255)
    is_default: Optional[bool] = None


class ResumeResponse(BaseModel):
    """Schema for resume response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    file_name: str
    file_url: str
    file_size: int
    mime_type: str
    is_default: bool = False
    is_parsed: bool = False
    parsed_content: Optional[dict] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ResumeParseResponse(BaseModel):
    """Schema for resume parse result."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_parsed: bool = True
    parsed_content: Optional[dict] = None
    skills_extracted: list[str] = []
    experience_years: Optional[int] = None
