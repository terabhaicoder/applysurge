"""
Data export endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.services.export_service import ExportService

router = APIRouter()


@router.get("/")
async def list_exports(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all exports for the current user."""
    service = ExportService(db)
    return await service.list_exports(current_user.id)


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def create_export(
    export_type: str = Query("applications", pattern="^(applications|jobs|analytics)$"),
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new data export. Returns export ID and status."""
    service = ExportService(db)
    return await service.create_export(
        user_id=current_user.id,
        export_type=export_type,
        format=format,
    )


@router.get("/{export_id}")
async def get_export(
    export_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get export status and metadata."""
    service = ExportService(db)
    return await service.get_export(current_user.id, export_id)


@router.get("/{export_id}/download")
async def download_export(
    export_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a download URL for a completed export."""
    service = ExportService(db)
    url = await service.get_download_url(current_user.id, export_id)
    return {"download_url": url}
