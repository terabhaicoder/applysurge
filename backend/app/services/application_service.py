"""
Application tracking service.
"""

from datetime import datetime, timezone
from typing import List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, ValidationError
from app.models.application import Application, ApplicationLog
from app.models.job import Job
from app.schemas.application import (
    ApplicationResponse,
    ApplicationStatusUpdate,
    ApplicationLogResponse,
    ApplicationListFilters,
    ApplicationStatsResponse,
)


class ApplicationService:
    """Service for application tracking operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_applications(
        self,
        user_id: UUID,
        filters: ApplicationListFilters,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ApplicationResponse], int]:
        """List applications with filtering and pagination."""
        query = select(Application).where(Application.user_id == user_id)
        count_query = select(func.count(Application.id)).where(
            Application.user_id == user_id
        )

        if filters.status:
            query = query.where(Application.status == filters.status)
            count_query = count_query.where(Application.status == filters.status)

        if filters.search:
            # Search across job title and company
            from app.models.job import Job
            from sqlalchemy import or_
            search_term = f"%{filters.search}%"
            query = query.join(Job).where(
                or_(Job.title.ilike(search_term), Job.company.ilike(search_term))
            )
            count_query = count_query.join(Job).where(
                or_(Job.title.ilike(search_term), Job.company.ilike(search_term))
            )
        elif filters.company:
            # Get company from job relationship
            from app.models.job import Job
            query = query.join(Job).where(Job.company.ilike(f"%{filters.company}%"))
            count_query = count_query.join(Job).where(Job.company.ilike(f"%{filters.company}%"))

        if filters.date_from:
            query = query.where(Application.created_at >= filters.date_from)
            count_query = count_query.where(Application.created_at >= filters.date_from)

        if filters.date_to:
            query = query.where(Application.created_at <= filters.date_to)
            count_query = count_query.where(Application.created_at <= filters.date_to)

        if filters.source:
            query = query.where(Application.applied_via == filters.source)
            count_query = count_query.where(Application.applied_via == filters.source)

        # Get total
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Sorting
        sort_column = getattr(Application, filters.sort_by, Application.created_at)
        order_func = desc if filters.sort_order == "desc" else asc
        query = query.order_by(order_func(sort_column))

        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Eagerly load job relationship
        query = query.options(selectinload(Application.job))

        result = await self.db.execute(query)
        applications = result.scalars().all()

        return [self._to_response(a, getattr(a, 'job', None)) for a in applications], total

    async def get_application(self, user_id: UUID, app_id: UUID) -> ApplicationResponse:
        """Get a specific application."""
        result = await self.db.execute(
            select(Application)
            .options(selectinload(Application.job))
            .where(Application.id == app_id, Application.user_id == user_id)
        )
        application = result.scalar_one_or_none()
        if not application:
            raise NotFoundError("Application")
        return self._to_response(application, getattr(application, 'job', None))

    async def get_application_logs(
        self, user_id: UUID, app_id: UUID
    ) -> List[ApplicationLogResponse]:
        """Get activity logs for an application."""
        await self._get_user_application(user_id, app_id)

        result = await self.db.execute(
            select(ApplicationLog)
            .where(ApplicationLog.application_id == app_id)
            .order_by(ApplicationLog.created_at.desc())
        )
        logs = result.scalars().all()
        return [
            ApplicationLogResponse(
                id=log.id,
                application_id=log.application_id,
                action=log.action,
                details=log.details,
                created_at=log.created_at,
            )
            for log in logs
        ]

    async def update_status(
        self, user_id: UUID, app_id: UUID, data: ApplicationStatusUpdate
    ) -> ApplicationResponse:
        """Update application status."""
        application = await self._get_user_application(user_id, app_id)

        old_status = application.status
        application.status = data.status
        if data.notes:
            application.notes = data.notes

        # Set appropriate date fields
        now = datetime.now(timezone.utc)
        if data.status == "interview" and not application.interview_at:
            application.interview_at = now
        elif data.status == "offered" and not application.offered_at:
            application.offered_at = now
        elif data.status == "rejected" and not application.rejected_at:
            application.rejected_at = now

        # Create log entry
        log = ApplicationLog(
            application_id=app_id,
            action="status_change",
            status_from=old_status,
            status_to=data.status,
            details={"notes": data.notes} if data.notes else None,
            performed_by="user",
        )
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(application)

        return self._to_response(application)

    async def withdraw_application(
        self, user_id: UUID, app_id: UUID
    ) -> ApplicationResponse:
        """Withdraw an application."""
        application = await self._get_user_application(user_id, app_id)

        if application.status == "withdrawn":
            raise ValidationError("Application already withdrawn")

        old_status = application.status
        application.status = "withdrawn"
        application.withdrawn_at = datetime.now(timezone.utc)

        log = ApplicationLog(
            application_id=app_id,
            action="withdrawn",
            status_from=old_status,
            status_to="withdrawn",
            performed_by="user",
        )
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(application)

        return self._to_response(application)

    async def get_stats(self, user_id: UUID) -> ApplicationStatsResponse:
        """Get application statistics for a user."""
        result = await self.db.execute(
            select(Application.status, func.count(Application.id))
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
        status_counts = dict(result.all())

        total = sum(status_counts.values())
        responses = sum(
            status_counts.get(s, 0)
            for s in ("interview", "offered", "rejected")
        )
        response_rate = (responses / total * 100) if total > 0 else 0.0

        return ApplicationStatsResponse(
            total=total,
            pending=status_counts.get("pending", 0),
            applied=status_counts.get("applied", 0),
            viewed=status_counts.get("viewed", 0),
            interview=status_counts.get("interview", 0),
            offered=status_counts.get("offered", 0),
            rejected=status_counts.get("rejected", 0),
            withdrawn=status_counts.get("withdrawn", 0),
            accepted=status_counts.get("accepted", 0),
            response_rate=round(response_rate, 1),
        )

    async def _get_user_application(self, user_id: UUID, app_id: UUID) -> Application:
        """Get application belonging to user."""
        result = await self.db.execute(
            select(Application).where(
                Application.id == app_id,
                Application.user_id == user_id,
            )
        )
        application = result.scalar_one_or_none()
        if not application:
            raise NotFoundError("Application")
        return application

    def _to_response(self, app: Application, job: Job = None) -> ApplicationResponse:
        """Convert Application model to response schema."""
        return ApplicationResponse(
            id=app.id,
            user_id=app.user_id,
            job_id=app.job_id,
            job_title=job.title if job else None,
            company=job.company if job else None,
            company_name=job.company if job else None,
            job_location=job.location if job else None,
            application_method=app.applied_via,
            status=app.status,
            applied_at=app.applied_at,
            resume_id=app.resume_id,
            cover_letter=app.cover_letter,
            notes=app.notes,
            source=app.applied_via,
            application_url=app.application_url,
            response_received=app.response_received,
            response_date=app.response_received_at,
            interview_date=app.interview_at,
            created_at=app.created_at,
            updated_at=app.updated_at,
        )
