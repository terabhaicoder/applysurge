"""
Email settings and template schemas.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmailSettingsUpdate(BaseModel):
    """Schema for updating email settings."""
    provider: Optional[str] = Field(None, pattern="^(gmail|smtp|sendgrid)$")
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = Field(None, ge=1, le=65535)
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    from_email: Optional[EmailStr] = None
    from_name: Optional[str] = Field(None, max_length=255)
    signature: Optional[str] = None
    daily_send_limit: Optional[int] = Field(None, ge=1, le=500)
    enabled: Optional[bool] = None


class EmailSettingsResponse(BaseModel):
    """Schema for email settings response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    provider: str = "smtp"
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_use_tls: bool = True
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    signature: Optional[str] = None
    daily_send_limit: int = 50
    enabled: bool = False
    is_verified: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


class GmailConnectRequest(BaseModel):
    """Schema for connecting Gmail."""
    authorization_code: str


class SmtpConnectRequest(BaseModel):
    """Schema for connecting via SMTP."""
    host: str
    port: int = Field(..., ge=1, le=65535)
    username: str
    password: str
    use_tls: bool = True
    from_email: EmailStr
    from_name: Optional[str] = None


class EmailVerifyRequest(BaseModel):
    """Schema for verifying email connection."""
    pass


class EmailTestRequest(BaseModel):
    """Schema for sending a test email."""
    to_email: EmailStr
    subject: Optional[str] = "JobPilot Test Email"


class EmailTemplateCreate(BaseModel):
    """Schema for creating email template."""
    name: str = Field(..., max_length=255)
    subject: str = Field(..., max_length=500)
    body: str
    template_type: str = Field(default="cover_letter", pattern="^(cover_letter|follow_up|thank_you|custom)$")
    variables: Optional[list[str]] = None


class EmailTemplateUpdate(BaseModel):
    """Schema for updating email template."""
    name: Optional[str] = Field(None, max_length=255)
    subject: Optional[str] = Field(None, max_length=500)
    body: Optional[str] = None
    template_type: Optional[str] = Field(None, pattern="^(cover_letter|follow_up|thank_you|custom)$")
    variables: Optional[list[str]] = None


class EmailTemplateResponse(BaseModel):
    """Schema for email template response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    subject: str
    body: str
    template_type: str = "cover_letter"
    variables: Optional[list[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class EmailTemplatePreviewRequest(BaseModel):
    """Schema for previewing a template with variables."""
    variables: dict[str, str] = {}


class EmailTemplatePreviewResponse(BaseModel):
    """Schema for template preview result."""
    subject: str
    body: str


class EmailTemplateGenerateRequest(BaseModel):
    """Schema for generating a template with AI."""
    template_type: str = Field(..., pattern="^(cover_letter|follow_up|thank_you|custom)$")
    job_title: Optional[str] = None
    company: Optional[str] = None
    tone: str = Field(default="professional", pattern="^(professional|casual|formal|enthusiastic)$")
    additional_context: Optional[str] = None
