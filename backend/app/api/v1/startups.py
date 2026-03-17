"""
API endpoints for startup outreach feature.

Provides endpoints for:
- Listing and filtering discovered startups
- Getting startup contact details
- Triggering startup discovery
- Sending outreach to specific startups
- Managing outreach status
- Outreach settings management
- Outreach statistics
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.db.session import get_async_session
from app.models.startup_contact import StartupContact, StartupOutreachSettings
from app.models.user import User
from app.schemas.startup import (
    StartupContactCreate,
    StartupContactList,
    StartupContactResponse,
    StartupContactUpdate,
    StartupDiscoveryRequest,
    StartupDiscoveryResponse,
    StartupOutreachRequest,
    StartupOutreachResponse,
    StartupOutreachSettingsCreate,
    StartupOutreachSettingsResponse,
    StartupOutreachSettingsUpdate,
    StartupOutreachStats,
    StartupSearchFilters,
    StartupStatusUpdate,
)

router = APIRouter(tags=["startups"])


async def _get_user_id_from_auth(
    current_user: User = Depends(get_current_active_user),
) -> uuid.UUID:
    """Extract authenticated user ID from JWT token."""
    return current_user.id


# ============================================================
# Startup Contact Endpoints
# ============================================================


@router.get("/", response_model=StartupContactList)
async def list_startups(
    user_id: uuid.UUID = Depends(_get_user_id_from_auth),
    session: AsyncSession = Depends(get_async_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    industry: Optional[str] = None,
    funding_stage: Optional[str] = None,
    outreach_status: Optional[str] = None,
    discovery_source: Optional[str] = None,
    has_contact_email: Optional[bool] = None,
    has_open_roles: Optional[bool] = None,
    search: Optional[str] = None,
    is_archived: bool = False,
    sort_by: str = Query("created_at", regex="^(created_at|company_name|outreach_status|funding_stage)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
):
    """
    List discovered startups with filtering and pagination.

    Supports filtering by industry, funding stage, outreach status,
    discovery source, and search by company name or description.
    """
    # Build query
    conditions = [
        StartupContact.user_id == user_id,
        StartupContact.is_archived == is_archived,
    ]

    if industry:
        conditions.append(StartupContact.company_industry.ilike(f"%{industry}%"))
    if funding_stage:
        conditions.append(StartupContact.funding_stage == funding_stage)
    if outreach_status:
        conditions.append(StartupContact.outreach_status == outreach_status)
    if discovery_source:
        conditions.append(StartupContact.discovery_source == discovery_source)
    if has_contact_email is not None:
        if has_contact_email:
            conditions.append(StartupContact.contact_email.isnot(None))
        else:
            conditions.append(StartupContact.contact_email.is_(None))
    if has_open_roles is not None:
        if has_open_roles:
            conditions.append(StartupContact.open_roles.isnot(None))
        else:
            conditions.append(StartupContact.open_roles.is_(None))
    if search:
        search_filter = or_(
            StartupContact.company_name.ilike(f"%{search}%"),
            StartupContact.company_description.ilike(f"%{search}%"),
            StartupContact.company_industry.ilike(f"%{search}%"),
        )
        conditions.append(search_filter)

    # Count total
    count_query = select(func.count(StartupContact.id)).where(and_(*conditions))
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Sort
    sort_column = getattr(StartupContact, sort_by)
    if sort_order == "desc":
        sort_column = sort_column.desc()
    else:
        sort_column = sort_column.asc()

    # Fetch items
    offset = (page - 1) * page_size
    query = (
        select(StartupContact)
        .where(and_(*conditions))
        .order_by(sort_column)
        .offset(offset)
        .limit(page_size)
    )
    result = await session.execute(query)
    items = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return StartupContactList(
        items=[StartupContactResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/stats", response_model=StartupOutreachStats)
async def get_outreach_stats(
    user_id: uuid.UUID = Depends(_get_user_id_from_auth),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get startup outreach statistics for the current user.

    Returns counts by status, response rate, emails sent today,
    top industries, and weekly activity.
    """
    # Status counts
    status_query = select(
        StartupContact.outreach_status,
        func.count(StartupContact.id),
    ).where(
        and_(
            StartupContact.user_id == user_id,
            StartupContact.is_archived == False,
        )
    ).group_by(StartupContact.outreach_status)

    status_result = await session.execute(status_query)
    status_counts = dict(status_result.all())

    total_discovered = status_counts.get("discovered", 0)
    total_contacted = status_counts.get("contacted", 0)
    total_responded = status_counts.get("responded", 0)
    total_not_interested = status_counts.get("not_interested", 0)
    total_interviews = status_counts.get("interview", 0)

    # Response rate
    response_rate = 0.0
    if total_contacted > 0:
        response_rate = (total_responded + total_not_interested + total_interviews) / total_contacted

    # Emails sent today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_query = select(func.count(StartupContact.id)).where(
        and_(
            StartupContact.user_id == user_id,
            StartupContact.email_sent_at >= today_start,
        )
    )
    today_result = await session.execute(today_query)
    emails_sent_today = today_result.scalar() or 0

    # Get max per day from settings
    settings_result = await session.execute(
        select(StartupOutreachSettings).where(StartupOutreachSettings.user_id == user_id)
    )
    settings = settings_result.scalar_one_or_none()
    max_per_day = settings.max_emails_per_day if settings else 20

    # Top industries
    industry_query = select(
        StartupContact.company_industry,
        func.count(StartupContact.id).label("count"),
    ).where(
        and_(
            StartupContact.user_id == user_id,
            StartupContact.company_industry.isnot(None),
        )
    ).group_by(StartupContact.company_industry).order_by(func.count(StartupContact.id).desc()).limit(5)

    industry_result = await session.execute(industry_query)
    top_industries = [
        {"industry": row[0], "count": row[1]}
        for row in industry_result.all()
    ]

    # Top sources
    source_query = select(
        StartupContact.discovery_source,
        func.count(StartupContact.id).label("count"),
    ).where(
        and_(
            StartupContact.user_id == user_id,
            StartupContact.discovery_source.isnot(None),
        )
    ).group_by(StartupContact.discovery_source).order_by(func.count(StartupContact.id).desc()).limit(5)

    source_result = await session.execute(source_query)
    top_sources = [
        {"source": row[0], "count": row[1]}
        for row in source_result.all()
    ]

    # Weekly outreach (last 7 days)
    from datetime import timedelta
    weekly_data = []
    for i in range(7):
        day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        day_end = day + timedelta(days=1)
        day_query = select(func.count(StartupContact.id)).where(
            and_(
                StartupContact.user_id == user_id,
                StartupContact.email_sent_at >= day,
                StartupContact.email_sent_at < day_end,
            )
        )
        day_result = await session.execute(day_query)
        count = day_result.scalar() or 0
        weekly_data.append({
            "date": day.strftime("%Y-%m-%d"),
            "emails_sent": count,
        })
    weekly_data.reverse()

    # Average response time
    avg_response_time = None
    response_time_query = select(
        func.avg(
            func.extract("epoch", StartupContact.response_received_at - StartupContact.email_sent_at) / 3600
        )
    ).where(
        and_(
            StartupContact.user_id == user_id,
            StartupContact.response_received_at.isnot(None),
            StartupContact.email_sent_at.isnot(None),
        )
    )
    rt_result = await session.execute(response_time_query)
    avg_hours = rt_result.scalar()
    if avg_hours is not None:
        avg_response_time = round(float(avg_hours), 1)

    return StartupOutreachStats(
        total_discovered=total_discovered,
        total_contacted=total_contacted,
        total_responded=total_responded,
        total_not_interested=total_not_interested,
        total_interviews=total_interviews,
        response_rate=round(response_rate, 3),
        emails_sent_today=emails_sent_today,
        emails_remaining_today=max(0, max_per_day - emails_sent_today),
        top_industries=top_industries,
        top_sources=top_sources,
        weekly_outreach=weekly_data,
        avg_response_time_hours=avg_response_time,
    )


@router.get("/settings", response_model=StartupOutreachSettingsResponse)
async def get_outreach_settings(
    user_id: uuid.UUID = Depends(_get_user_id_from_auth),
    session: AsyncSession = Depends(get_async_session),
):
    """Get the user's startup outreach preferences."""
    result = await session.execute(
        select(StartupOutreachSettings).where(StartupOutreachSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        # Create default settings
        settings = StartupOutreachSettings(
            user_id=user_id,
            outreach_enabled=False,
        )
        session.add(settings)
        await session.commit()
        await session.refresh(settings)

    return StartupOutreachSettingsResponse.model_validate(settings)


@router.put("/settings", response_model=StartupOutreachSettingsResponse)
async def update_outreach_settings(
    settings_update: StartupOutreachSettingsUpdate,
    user_id: uuid.UUID = Depends(_get_user_id_from_auth),
    session: AsyncSession = Depends(get_async_session),
):
    """Update the user's startup outreach preferences."""
    result = await session.execute(
        select(StartupOutreachSettings).where(StartupOutreachSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = StartupOutreachSettings(user_id=user_id)
        session.add(settings)

    # Update only provided fields
    update_data = settings_update.model_dump(exclude_unset=True, exclude_none=True)
    for field_name, value in update_data.items():
        setattr(settings, field_name, value)

    await session.commit()
    await session.refresh(settings)

    return StartupOutreachSettingsResponse.model_validate(settings)


@router.get("/{startup_id}", response_model=StartupContactResponse)
async def get_startup_contact(
    startup_id: uuid.UUID,
    user_id: uuid.UUID = Depends(_get_user_id_from_auth),
    session: AsyncSession = Depends(get_async_session),
):
    """Get detailed information about a specific startup contact."""
    result = await session.execute(
        select(StartupContact).where(
            and_(
                StartupContact.id == startup_id,
                StartupContact.user_id == user_id,
            )
        )
    )
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup contact not found",
        )

    return StartupContactResponse.model_validate(contact)


@router.post("/discover", response_model=StartupDiscoveryResponse)
async def trigger_startup_discovery(
    request: StartupDiscoveryRequest,
    user_id: uuid.UUID = Depends(_get_user_id_from_auth),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Trigger startup discovery to find new startups matching preferences.

    Dispatches a background task that scrapes configured sources
    and saves matching startups to the database.
    """
    from worker.tasks.startup_outreach_task import discover_startups_task

    # Validate sources
    valid_sources = {"yc", "product_hunt", "linkedin", "angellist"}
    sources = None
    if request.sources:
        sources = [s for s in request.sources if s in valid_sources]
        if not sources:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sources. Valid options: {', '.join(valid_sources)}",
            )

    # Dispatch task
    task = discover_startups_task.delay(
        user_id=str(user_id),
        sources=sources,
    )

    return StartupDiscoveryResponse(
        task_id=task.id,
        message="Startup discovery started. Results will appear in your startup list.",
        estimated_results=request.max_results,
    )


@router.post("/{startup_id}/outreach", response_model=StartupOutreachResponse)
async def send_outreach_to_startup(
    startup_id: uuid.UUID,
    request: StartupOutreachRequest,
    user_id: uuid.UUID = Depends(_get_user_id_from_auth),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Send a personalized outreach email to a specific startup.

    Generates an AI-written email based on the company profile
    and sends it via SendGrid with tracking.
    """
    from worker.tasks.startup_outreach_task import send_startup_outreach_task

    # Verify the contact exists and has an email
    result = await session.execute(
        select(StartupContact).where(
            and_(
                StartupContact.id == startup_id,
                StartupContact.user_id == user_id,
            )
        )
    )
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup contact not found",
        )

    if not contact.contact_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No contact email available. Run contact scraping first.",
        )

    if contact.outreach_status == "contacted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already contacted this startup. Use followup instead.",
        )

    # Check rate limit
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    count_query = select(func.count(StartupContact.id)).where(
        and_(
            StartupContact.user_id == user_id,
            StartupContact.email_sent_at >= today_start,
        )
    )
    count_result = await session.execute(count_query)
    emails_today = count_result.scalar() or 0

    settings_result = await session.execute(
        select(StartupOutreachSettings).where(StartupOutreachSettings.user_id == user_id)
    )
    settings = settings_result.scalar_one_or_none()
    max_per_day = settings.max_emails_per_day if settings else 20

    if emails_today >= max_per_day:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily outreach limit reached ({max_per_day} emails/day). Try again tomorrow.",
        )

    # Dispatch send task
    task = send_startup_outreach_task.delay(
        user_id=str(user_id),
        contact_id=str(startup_id),
        email_type=request.email_type,
        custom_message=request.custom_message,
    )

    return StartupOutreachResponse(
        success=True,
        message="Outreach email is being generated and sent.",
        contact_email=contact.contact_email,
    )


@router.put("/{startup_id}/status", response_model=StartupContactResponse)
async def update_outreach_status(
    startup_id: uuid.UUID,
    status_update: StartupStatusUpdate,
    user_id: uuid.UUID = Depends(_get_user_id_from_auth),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Update the outreach status for a startup contact.

    Valid statuses: discovered, contacted, responded, not_interested, interview, archived.
    """
    result = await session.execute(
        select(StartupContact).where(
            and_(
                StartupContact.id == startup_id,
                StartupContact.user_id == user_id,
            )
        )
    )
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup contact not found",
        )

    # Update status
    contact.outreach_status = status_update.outreach_status
    if status_update.notes:
        existing_notes = contact.notes or ""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        contact.notes = f"{existing_notes}\n[{timestamp}] {status_update.notes}".strip()

    # Set response timestamp if status is "responded"
    if status_update.outreach_status == "responded" and not contact.response_received_at:
        contact.response_received_at = datetime.now(timezone.utc)

    # Archive if status is "archived"
    if status_update.outreach_status == "archived":
        contact.is_archived = True

    await session.commit()
    await session.refresh(contact)

    return StartupContactResponse.model_validate(contact)


@router.post("/{startup_id}/scrape-contacts")
async def trigger_contact_scraping(
    startup_id: uuid.UUID,
    user_id: uuid.UUID = Depends(_get_user_id_from_auth),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Trigger contact scraping for a specific startup.

    Scrapes the company website, LinkedIn, and Hunter.io to find
    the best contact for outreach.
    """
    from worker.tasks.startup_outreach_task import scrape_startup_contacts_task

    # Verify the contact exists
    result = await session.execute(
        select(StartupContact).where(
            and_(
                StartupContact.id == startup_id,
                StartupContact.user_id == user_id,
            )
        )
    )
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup contact not found",
        )

    if not contact.company_website:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No company website available for scraping.",
        )

    # Dispatch task
    task = scrape_startup_contacts_task.delay(
        user_id=str(user_id),
        contact_id=str(startup_id),
    )

    return {
        "task_id": task.id,
        "message": "Contact scraping started. Results will be updated on the startup record.",
    }


@router.post("/pipeline/run")
async def trigger_full_pipeline(
    user_id: uuid.UUID = Depends(_get_user_id_from_auth),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Trigger the full startup outreach pipeline:
    1. Discover new startups
    2. Scrape contacts
    3. Generate and send emails

    This is the same pipeline that runs on the automated schedule.
    """
    from worker.tasks.startup_outreach_task import process_startup_pipeline

    # Check if outreach is enabled
    result = await session.execute(
        select(StartupOutreachSettings).where(StartupOutreachSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()

    if settings and not settings.outreach_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Startup outreach is disabled. Enable it in settings first.",
        )

    task = process_startup_pipeline.delay(user_id=str(user_id))

    return {
        "task_id": task.id,
        "message": "Full outreach pipeline started. This may take several minutes.",
    }


@router.delete("/{startup_id}")
async def delete_startup_contact(
    startup_id: uuid.UUID,
    user_id: uuid.UUID = Depends(_get_user_id_from_auth),
    session: AsyncSession = Depends(get_async_session),
):
    """Delete a startup contact record."""
    result = await session.execute(
        select(StartupContact).where(
            and_(
                StartupContact.id == startup_id,
                StartupContact.user_id == user_id,
            )
        )
    )
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup contact not found",
        )

    await session.delete(contact)
    await session.commit()

    return {"message": "Startup contact deleted successfully"}


@router.post("/{startup_id}/archive")
async def archive_startup_contact(
    startup_id: uuid.UUID,
    user_id: uuid.UUID = Depends(_get_user_id_from_auth),
    session: AsyncSession = Depends(get_async_session),
):
    """Archive a startup contact (soft delete)."""
    result = await session.execute(
        select(StartupContact).where(
            and_(
                StartupContact.id == startup_id,
                StartupContact.user_id == user_id,
            )
        )
    )
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup contact not found",
        )

    contact.is_archived = True
    contact.outreach_status = "archived"
    await session.commit()

    return {"message": "Startup contact archived successfully"}
