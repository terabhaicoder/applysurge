"""
Agent management service for controlling the automation agent.
Uses AgentSettings model for configuration and status tracking.
"""

from datetime import datetime, timezone
from typing import List
from uuid import UUID

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AgentError, QuotaExceededError
from app.models.agent_settings import AgentSettings
from app.models.application import Application
from app.models.job_match import JobMatch
from app.schemas.agent import (
    AgentStatusResponse,
    AgentSettingsUpdate,
    AgentSettingsResponse,
    AgentLogResponse,
)


class AgentService:
    """Service for agent operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_status(self, user_id: UUID) -> AgentStatusResponse:
        """Get current agent status."""
        agent_settings = await self._get_or_create_settings(user_id)

        # Auto-detect stale state: if DB says running but Redis lock is gone, task crashed
        if agent_settings.is_running:
            import redis as redis_lib
            r = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
            lock_exists = r.exists(f"jobpilot:agent:session_lock:{user_id}")
            r.close()
            if not lock_exists:
                agent_settings.is_running = False
                agent_settings.is_enabled = False
                await self.db.flush()

        # Count today's applications by agent
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        apps_result = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.created_at >= today_start,
                    Application.applied_via == "agent",
                )
            )
        )
        apps_today = apps_result.scalar() or 0

        # Get queue size
        queue_result = await self.db.execute(
            select(func.count(JobMatch.id)).where(
                JobMatch.user_id == user_id,
                JobMatch.status == "queued",
            )
        )
        queue_size = queue_result.scalar() or 0

        # Total applications (all-time) for beta limit
        total_result = await self.db.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
            )
        )
        apps_total = total_result.scalar() or 0

        status = "idle"
        if agent_settings.is_running:
            status = "running"
        elif agent_settings.is_enabled:
            status = "enabled"

        return AgentStatusResponse(
            is_running=agent_settings.is_running,
            is_paused=False,
            status=status,
            current_task=None,
            applications_made_today=apps_today,
            applications_limit_today=agent_settings.max_applications_per_day,
            applications_total=apps_total,
            applications_limit_total=settings.BETA_MAX_TOTAL_APPLICATIONS,
            session_start_time=agent_settings.last_run_at,
            last_activity_at=agent_settings.last_run_at,
            errors_count=agent_settings.consecutive_errors,
            queue_size=queue_size,
        )

    async def start_agent(self, user_id: UUID, user_email: str = "") -> AgentStatusResponse:
        """Start the automation agent."""
        agent_settings = await self._get_or_create_settings(user_id)

        if agent_settings.is_running:
            raise AgentError("Agent is already running")

        # Check beta quota before starting
        from app.services.user_service import UserService
        has_quota, total, limit = await UserService.check_beta_quota(
            self.db, user_id, user_email
        )
        if not has_quota:
            raise QuotaExceededError(
                f"Beta application limit reached ({total}/{limit}). "
                "You have used all your beta applications."
            )

        agent_settings.is_running = True
        agent_settings.is_enabled = True
        agent_settings.last_run_at = datetime.now(timezone.utc)
        agent_settings.consecutive_errors = 0
        agent_settings.last_error = None
        await self.db.flush()

        # Dispatch Celery task
        try:
            from worker.tasks.agent_tasks import run_agent_session
            run_agent_session.delay(str(user_id))
        except ImportError:
            pass  # Worker module may not be available in API context

        return await self.get_status(user_id)

    async def stop_agent(self, user_id: UUID) -> AgentStatusResponse:
        """Force-stop the automation agent. Always succeeds."""
        agent_settings = await self._get_or_create_settings(user_id)

        # Unconditionally mark as stopped - no guard on is_running
        agent_settings.is_running = False
        agent_settings.is_enabled = False
        await self.db.flush()

        # Send Redis stop signal AND release session lock (clean up stale locks)
        import redis as redis_lib
        r = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
        r.set(f"jobpilot:agent:stop:{user_id}", "1", ex=300)
        r.delete(f"jobpilot:agent:session_lock:{user_id}")
        r.close()

        return await self.get_status(user_id)

    async def pause_agent(self, user_id: UUID) -> AgentStatusResponse:
        """Pause the automation agent. Always succeeds."""
        agent_settings = await self._get_or_create_settings(user_id)

        # Unconditionally pause - no guard on is_running
        agent_settings.is_running = False
        # Keep is_enabled True so resume can restart it
        await self.db.flush()

        # Send Redis stop signal AND release session lock
        import redis as redis_lib
        r = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
        r.set(f"jobpilot:agent:stop:{user_id}", "1", ex=300)
        r.delete(f"jobpilot:agent:session_lock:{user_id}")
        r.close()

        return await self.get_status(user_id)

    async def resume_agent(self, user_id: UUID) -> AgentStatusResponse:
        """Resume a paused agent."""
        agent_settings = await self._get_or_create_settings(user_id)

        if agent_settings.is_running:
            raise AgentError("Agent is already running")

        if not agent_settings.is_enabled:
            raise AgentError("Agent is not enabled. Start it first.")

        agent_settings.is_running = True
        agent_settings.last_run_at = datetime.now(timezone.utc)
        agent_settings.consecutive_errors = 0
        agent_settings.last_error = None
        await self.db.flush()

        # Dispatch Celery task to restart the agent session
        try:
            from worker.tasks.agent_tasks import run_agent_session
            run_agent_session.delay(str(user_id))
        except ImportError:
            pass  # Worker module may not be available in API context

        return await self.get_status(user_id)

    async def get_settings(self, user_id: UUID) -> AgentSettingsResponse:
        """Get agent settings."""
        agent_settings = await self._get_or_create_settings(user_id)
        return AgentSettingsResponse(
            id=agent_settings.id,
            user_id=agent_settings.user_id,
            max_applications_per_day=agent_settings.max_applications_per_day,
            cooldown_seconds=agent_settings.cooldown_seconds,
            auto_apply=agent_settings.is_enabled,
            cover_letter_enabled=agent_settings.auto_generate_cover_letter,
            created_at=agent_settings.created_at,
            updated_at=agent_settings.updated_at,
        )

    async def update_settings(
        self, user_id: UUID, data: AgentSettingsUpdate
    ) -> AgentSettingsResponse:
        """Update agent settings."""
        agent_settings = await self._get_or_create_settings(user_id)

        update_data = data.model_dump(exclude_unset=True)

        # Map schema fields to model fields
        field_mapping = {
            "max_applications_per_day": "max_applications_per_day",
            "cooldown_seconds": "cooldown_seconds",
            "auto_apply": "is_enabled",
            "cover_letter_enabled": "auto_generate_cover_letter",
        }

        for schema_field, value in update_data.items():
            model_field = field_mapping.get(schema_field, schema_field)
            if hasattr(agent_settings, model_field):
                setattr(agent_settings, model_field, value)

        await self.db.flush()
        await self.db.refresh(agent_settings)

        return await self.get_settings(user_id)

    async def get_logs(
        self, user_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[AgentLogResponse]:
        """Get agent activity logs from application logs."""
        from app.models.application import ApplicationLog

        result = await self.db.execute(
            select(ApplicationLog)
            .join(Application)
            .where(
                Application.user_id == user_id,
                Application.applied_via == "agent",
            )
            .order_by(desc(ApplicationLog.created_at))
            .offset(offset)
            .limit(limit)
        )
        logs = result.scalars().all()

        return [
            AgentLogResponse(
                id=log.id,
                user_id=user_id,
                session_id=None,
                level="info",
                message=f"{log.action}: {log.message or ''}".strip(": "),
                details=log.details,
                created_at=log.created_at,
            )
            for log in logs
        ]

    async def _get_or_create_settings(self, user_id: UUID) -> AgentSettings:
        """Get or create agent settings for user."""
        result = await self.db.execute(
            select(AgentSettings).where(AgentSettings.user_id == user_id)
        )
        agent_settings = result.scalar_one_or_none()

        if not agent_settings:
            agent_settings = AgentSettings(user_id=user_id)
            self.db.add(agent_settings)
            await self.db.flush()
            await self.db.refresh(agent_settings)

        return agent_settings
