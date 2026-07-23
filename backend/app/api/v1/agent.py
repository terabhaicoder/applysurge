"""
Agent control endpoints for managing the automation agent.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.agent import (
    AgentLogResponse,
    AgentSettingsResponse,
    AgentSettingsUpdate,
    AgentStatusResponse,
)
from app.services.agent_service import AgentService

router = APIRouter()


@router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current status of the automation agent."""
    service = AgentService(db)
    return await service.get_status(current_user.id)


@router.post("/start", response_model=AgentStatusResponse)
async def start_agent(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Start the automation agent."""
    service = AgentService(db)
    return await service.start_agent(current_user.id, user_email=current_user.email)


@router.post("/stop", response_model=AgentStatusResponse)
async def stop_agent(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Stop the automation agent."""
    service = AgentService(db)
    return await service.stop_agent(current_user.id)


@router.post("/pause", response_model=AgentStatusResponse)
async def pause_agent(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Pause the automation agent."""
    service = AgentService(db)
    return await service.pause_agent(current_user.id)


@router.post("/resume", response_model=AgentStatusResponse)
async def resume_agent(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Resume a paused automation agent."""
    service = AgentService(db)
    return await service.resume_agent(current_user.id)


@router.get("/settings", response_model=AgentSettingsResponse)
async def get_agent_settings(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get agent configuration settings."""
    service = AgentService(db)
    return await service.get_settings(current_user.id)


@router.put("/settings", response_model=AgentSettingsResponse)
async def update_agent_settings(
    data: AgentSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update agent configuration settings."""
    service = AgentService(db)
    return await service.update_settings(current_user.id, data)


@router.get("/logs")
async def get_agent_logs(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
):
    """Get agent activity logs from Redis (real-time)."""
    import json
    import redis as redis_lib
    from app.core.config import settings as app_settings

    r = redis_lib.from_url(app_settings.REDIS_URL, decode_responses=True)
    list_key = f"jobpilot:agent:logs:history:{current_user.id}"
    raw_logs = r.lrange(list_key, 0, limit - 1)
    r.close()

    return [json.loads(log) for log in raw_logs]
