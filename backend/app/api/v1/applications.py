"""
Application tracking endpoints.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.application import (
    ApplicationListFilters,
    ApplicationLogResponse,
    ApplicationResponse,
    ApplicationStatsResponse,
    ApplicationStatusUpdate,
)
from app.schemas.common import Page
from app.services.application_service import ApplicationService

router = APIRouter()


@router.get("/", response_model=Page[ApplicationResponse])
async def list_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    company: Optional[str] = None,
    search: Optional[str] = None,
    source: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List applications with filtering, search, and pagination."""
    filters = ApplicationListFilters(
        status=status,
        company=company,
        search=search,
        source=source,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    service = ApplicationService(db)
    items, total = await service.list_applications(
        user_id=current_user.id,
        filters=filters,
        page=page,
        page_size=page_size,
    )
    return Page.create(items=items, total=total, page=page, page_size=page_size)


@router.get("/stats", response_model=ApplicationStatsResponse)
async def get_application_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get application statistics summary."""
    service = ApplicationService(db)
    return await service.get_stats(current_user.id)


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific application."""
    service = ApplicationService(db)
    return await service.get_application(current_user.id, application_id)


@router.get("/{application_id}/logs", response_model=list[ApplicationLogResponse])
async def get_application_logs(
    application_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get activity logs for an application."""
    service = ApplicationService(db)
    return await service.get_application_logs(current_user.id, application_id)


@router.patch("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: UUID,
    data: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the status of an application."""
    service = ApplicationService(db)
    return await service.update_status(current_user.id, application_id, data)


@router.post("/{application_id}/withdraw", response_model=ApplicationResponse)
async def withdraw_application(
    application_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Withdraw an application."""
    service = ApplicationService(db)
    return await service.withdraw_application(current_user.id, application_id)
