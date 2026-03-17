"""
Job listing and queue management endpoints.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.core.exceptions import QuotaExceededError
from app.models.user import User
from app.schemas.common import MessageResponse, Page
from app.schemas.job import JobListFilters, JobQueueItem, JobResponse
from app.services.job_service import JobService
from app.services.user_service import UserService

router = APIRouter()


@router.get("/", response_model=Page[JobResponse])
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    location: Optional[str] = None,
    remote_type: Optional[str] = None,
    job_type: Optional[str] = None,
    experience_level: Optional[str] = None,
    min_salary: Optional[int] = None,
    max_salary: Optional[int] = None,
    company: Optional[str] = None,
    source: Optional[str] = None,
    sort_by: str = "posted_at",
    sort_order: str = "desc",
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List jobs with filtering, sorting, and pagination."""
    filters = JobListFilters(
        search=search,
        location=location,
        remote_type=remote_type,
        job_type=job_type,
        experience_level=experience_level,
        min_salary=min_salary,
        max_salary=max_salary,
        company=company,
        source=source,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    service = JobService(db)
    items, total = await service.list_jobs(
        user_id=current_user.id,
        filters=filters,
        page=page,
        page_size=page_size,
    )
    return Page.create(items=items, total=total, page=page, page_size=page_size)


@router.get("/queue", response_model=list[JobQueueItem])
async def get_job_queue(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the user's job application queue."""
    service = JobService(db)
    return await service.get_queue(current_user.id)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific job listing."""
    service = JobService(db)
    return await service.get_job(current_user.id, job_id)


@router.post("/{job_id}/apply", response_model=MessageResponse)
async def apply_to_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Add job to application queue. Does NOT start the agent."""
    has_quota, total, limit = await UserService.check_beta_quota(
        db, current_user.id, current_user.email
    )
    if not has_quota:
        raise QuotaExceededError(
            f"Beta application limit reached ({total}/{limit}). "
            "You have used all your beta applications."
        )

    service = JobService(db)
    await service.queue_job(current_user.id, job_id, priority=5)
    await db.commit()
    return MessageResponse(message="Job added to application queue")


@router.post("/{job_id}/skip", response_model=MessageResponse)
async def skip_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Skip/hide a job from the listing."""
    service = JobService(db)
    await service.hide_job(current_user.id, job_id)
    return MessageResponse(message="Job skipped")


@router.post("/{job_id}/save", response_model=MessageResponse)
async def save_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Save a job to the user's saved list."""
    service = JobService(db)
    await service.save_job(current_user.id, job_id)
    return MessageResponse(message="Job saved")


@router.post("/{job_id}/hide", response_model=MessageResponse)
async def hide_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Hide a job from the listing."""
    service = JobService(db)
    await service.hide_job(current_user.id, job_id)
    return MessageResponse(message="Job hidden")


@router.post("/{job_id}/queue", response_model=MessageResponse)
async def queue_job(
    job_id: UUID,
    priority: int = Query(0, ge=0, le=10),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a job to the application queue."""
    has_quota, total, limit = await UserService.check_beta_quota(
        db, current_user.id, current_user.email
    )
    if not has_quota:
        raise QuotaExceededError(
            f"Beta application limit reached ({total}/{limit}). "
            "You have used all your beta applications."
        )

    service = JobService(db)
    await service.queue_job(current_user.id, job_id, priority)
    return MessageResponse(message="Job added to queue")


@router.delete("/{job_id}/queue", response_model=MessageResponse)
async def unqueue_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a job from the application queue."""
    service = JobService(db)
    await service.unqueue_job(current_user.id, job_id)
    await db.commit()
    return MessageResponse(message="Job removed from queue")
