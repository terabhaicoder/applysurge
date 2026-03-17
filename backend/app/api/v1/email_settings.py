"""
Email settings endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.email import (
    EmailSettingsResponse,
    EmailSettingsUpdate,
    EmailTestRequest,
    GmailConnectRequest,
    SmtpConnectRequest,
)
from app.services.email_service import EmailService

router = APIRouter()


@router.get("/", response_model=EmailSettingsResponse)
async def get_email_settings(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's email configuration."""
    service = EmailService(db)
    return await service.get_settings(current_user.id)


@router.put("/", response_model=EmailSettingsResponse)
async def update_email_settings(
    data: EmailSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update email settings."""
    service = EmailService(db)
    return await service.update_settings(current_user.id, data)


@router.post("/connect/gmail", response_model=EmailSettingsResponse)
async def connect_gmail(
    data: GmailConnectRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Connect Gmail via OAuth authorization code."""
    service = EmailService(db)
    return await service.connect_gmail(current_user.id, data.authorization_code)


@router.post("/connect/smtp", response_model=EmailSettingsResponse)
async def connect_smtp(
    data: SmtpConnectRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Connect via custom SMTP settings."""
    service = EmailService(db)
    return await service.connect_smtp(current_user.id, data)


@router.post("/verify", response_model=MessageResponse)
async def verify_email_connection(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify the email connection by attempting to connect to the SMTP server."""
    service = EmailService(db)
    await service.verify_connection(current_user.id)
    return MessageResponse(message="Email connection verified successfully")


@router.post("/test", response_model=MessageResponse)
async def send_test_email(
    data: EmailTestRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a test email to verify the configuration."""
    service = EmailService(db)
    await service.send_test_email(
        user_id=current_user.id,
        to_email=data.to_email,
        subject=data.subject,
    )
    return MessageResponse(message="Test email sent successfully")
