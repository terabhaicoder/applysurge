"""
Analytics endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsOverview,
    ApplicationAnalytics,
    DailyAnalyticsResponse,
    ResponseAnalytics,
    SourceAnalytics,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get high-level analytics overview."""
    service = AnalyticsService(db)
    return await service.get_overview(current_user.id)


@router.get("/applications", response_model=ApplicationAnalytics)
async def get_application_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed application analytics broken down by status, source, and company."""
    service = AnalyticsService(db)
    return await service.get_application_analytics(current_user.id)


@router.get("/responses", response_model=ResponseAnalytics)
async def get_response_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get response rate analytics."""
    service = AnalyticsService(db)
    return await service.get_response_analytics(current_user.id)


@router.get("/sources", response_model=SourceAnalytics)
async def get_source_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics broken down by application source."""
    service = AnalyticsService(db)
    return await service.get_source_analytics(current_user.id)


@router.get("/daily", response_model=DailyAnalyticsResponse)
async def get_daily_analytics(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get daily analytics data points for charting."""
    service = AnalyticsService(db)
    return await service.get_daily_analytics(current_user.id, days=days)
