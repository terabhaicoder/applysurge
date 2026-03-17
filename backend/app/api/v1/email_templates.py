"""
Email template management endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.email import (
    EmailTemplateCreate,
    EmailTemplateGenerateRequest,
    EmailTemplatePreviewRequest,
    EmailTemplatePreviewResponse,
    EmailTemplateResponse,
    EmailTemplateUpdate,
)
from app.services.email_service import EmailService

router = APIRouter()


@router.get("/", response_model=list[EmailTemplateResponse])
async def list_templates(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all email templates."""
    service = EmailService(db)
    return await service.list_templates(current_user.id)


@router.post(
    "/",
    response_model=EmailTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    data: EmailTemplateCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new email template."""
    service = EmailService(db)
    return await service.create_template(current_user.id, data)


@router.get("/{template_id}", response_model=EmailTemplateResponse)
async def get_template(
    template_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific email template."""
    service = EmailService(db)
    return await service.get_template(current_user.id, template_id)


@router.patch("/{template_id}", response_model=EmailTemplateResponse)
async def update_template(
    template_id: UUID,
    data: EmailTemplateUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an email template."""
    service = EmailService(db)
    return await service.update_template(current_user.id, template_id, data)


@router.delete("/{template_id}", response_model=MessageResponse)
async def delete_template(
    template_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an email template."""
    service = EmailService(db)
    await service.delete_template(current_user.id, template_id)
    return MessageResponse(message="Template deleted")


@router.post("/{template_id}/preview", response_model=EmailTemplatePreviewResponse)
async def preview_template(
    template_id: UUID,
    data: EmailTemplatePreviewRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Preview a template with variable substitution."""
    service = EmailService(db)
    return await service.preview_template(current_user.id, template_id, data.variables)


@router.post("/generate", response_model=EmailTemplateResponse)
async def generate_template(
    data: EmailTemplateGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an email template using AI."""
    service = EmailService(db)
    return await service.generate_template(current_user.id, data)
