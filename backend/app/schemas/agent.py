"""
Agent schemas for automation control.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgentStatusResponse(BaseModel):
    """Schema for agent status."""
    model_config = ConfigDict(from_attributes=True)

    is_running: bool = False
    is_paused: bool = False
    status: str = "idle"  # idle, running, paused, error
    current_task: Optional[str] = None
    applications_made_today: int = 0
    applications_limit_today: int = 50
    applications_total: int = 0
    applications_limit_total: int = 10
    session_start_time: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    errors_count: int = 0
    queue_size: int = 0


class AgentSettingsUpdate(BaseModel):
    """Schema for updating agent settings."""
    max_applications_per_day: Optional[int] = Field(None, ge=1, le=200)
    cooldown_seconds: Optional[int] = Field(None, ge=5, le=300)
    auto_apply: Optional[bool] = None
    preferred_apply_time_start: Optional[str] = None  # HH:MM format
    preferred_apply_time_end: Optional[str] = None
    skip_easy_apply: Optional[bool] = None
    require_salary_info: Optional[bool] = None
    cover_letter_enabled: Optional[bool] = None
    custom_answers: Optional[dict] = None


class AgentSettingsResponse(BaseModel):
    """Schema for agent settings response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    max_applications_per_day: int = 50
    cooldown_seconds: int = 30
    auto_apply: bool = False
    preferred_apply_time_start: Optional[str] = None
    preferred_apply_time_end: Optional[str] = None
    skip_easy_apply: bool = False
    require_salary_info: bool = False
    cover_letter_enabled: bool = True
    custom_answers: Optional[dict] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class AgentLogResponse(BaseModel):
    """Schema for agent log entry."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    session_id: Optional[UUID] = None
    level: str = "info"  # info, warning, error, debug
    message: str
    details: Optional[dict] = None
    created_at: datetime
