"""
Notification schemas.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    """Schema for notification response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    type: str  # application_update, agent_status, system, etc.
    title: str
    message: str
    data: Optional[dict] = None
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime


class NotificationCountResponse(BaseModel):
    """Schema for unread notification count."""
    unread_count: int = 0
