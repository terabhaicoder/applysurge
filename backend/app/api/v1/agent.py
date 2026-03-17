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


@router.get("/logs", response_model=list[AgentLogResponse])
async def get_agent_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get agent activity logs."""
    service = AgentService(db)
    return await service.get_logs(current_user.id, limit=limit, offset=offset)
