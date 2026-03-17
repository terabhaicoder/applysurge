"""
Analytics computation service.
"""

from datetime import date, datetime, timedelta, timezone
from typing import List
from uuid import UUID

from sqlalchemy import select, func, and_, case, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.job import Job
from app.models.job_match import JobMatch
from app.schemas.analytics import (
    AnalyticsOverview,
    ApplicationAnalytics,
    ResponseAnalytics,
    SourceAnalytics,
    DailyAnalytics,
    DailyAnalyticsResponse,
)


class AnalyticsService:
    """Service for computing analytics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(self, user_id: UUID) -> AnalyticsOverview:
        """Get analytics overview."""
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Total applications
        total_result = await self.db.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id
            )
        )
        total = total_result.scalar() or 0

        # This week
        week_result = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.created_at >= week_ago,
                )
            )
        )
        this_week = week_result.scalar() or 0

        # This month
        month_result = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.created_at >= month_ago,
                )
            )
        )
        this_month = month_result.scalar() or 0

        # Response rate
        responses_result = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.response_received == True,
                )
            )
        )
        responses = responses_result.scalar() or 0
        response_rate = (responses / total * 100) if total > 0 else 0.0

        # Interview rate
        interviews_result = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.status.in_(["interview", "offered", "accepted"]),
                )
            )
        )
        interviews = interviews_result.scalar() or 0
        interview_rate = (interviews / total * 100) if total > 0 else 0.0

        # Offer rate
        offers_result = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.status.in_(["offered", "accepted"]),
                )
            )
        )
        offers = offers_result.scalar() or 0
        offer_rate = (offers / total * 100) if total > 0 else 0.0

        # Avg response time
        avg_result = await self.db.execute(
            select(
                func.avg(
                    func.extract(
                        "epoch",
                        Application.response_received_at - Application.applied_at,
                    )
                    / 86400
                )
            ).where(
                and_(
                    Application.user_id == user_id,
                    Application.response_received_at.isnot(None),
                    Application.applied_at.isnot(None),
                )
            )
        )
        avg_response = avg_result.scalar()

        # Active applications
        active_result = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.status.in_(["pending", "applied", "viewed", "interview"]),
                )
            )
        )
        active = active_result.scalar() or 0

        # Queue size
        queue_result = await self.db.execute(
            select(func.count(JobMatch.id)).where(
                and_(
                    JobMatch.user_id == user_id,
                    JobMatch.status == "queued",
                )
            )
        )
        queue_size = queue_result.scalar() or 0

        return AnalyticsOverview(
            total_applications=total,
            applications_this_week=this_week,
            applications_this_month=this_month,
            response_rate=round(response_rate, 1),
            interview_rate=round(interview_rate, 1),
            offer_rate=round(offer_rate, 1),
            avg_response_time_days=round(avg_response, 1) if avg_response else None,
            active_applications=active,
            jobs_in_queue=queue_size,
        )

    async def get_application_analytics(self, user_id: UUID) -> ApplicationAnalytics:
        """Get detailed application analytics."""
        # By status
        status_result = await self.db.execute(
            select(Application.status, func.count(Application.id))
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
        by_status = dict(status_result.all())
        total = sum(by_status.values())

        # By source
        source_result = await self.db.execute(
            select(Application.applied_via, func.count(Application.id))
            .where(
                and_(
                    Application.user_id == user_id,
                    Application.applied_via.isnot(None),
                )
            )
            .group_by(Application.applied_via)
        )
        by_source = dict(source_result.all())

        # By company (top 10)
        company_result = await self.db.execute(
            select(Application.company, func.count(Application.id))
            .where(
                and_(
                    Application.user_id == user_id,
                    Application.company.isnot(None),
                )
            )
            .group_by(Application.company)
            .order_by(func.count(Application.id).desc())
            .limit(10)
        )
        by_company = [
            {"company": name, "count": count}
            for name, count in company_result.all()
        ]

        return ApplicationAnalytics(
            total=total,
            by_status=by_status,
            by_source=by_source,
            by_company=by_company,
        )

    async def get_response_analytics(self, user_id: UUID) -> ResponseAnalytics:
        """Get response analytics."""
        total_result = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.response_received == True,
                )
            )
        )
        total_responses = total_result.scalar() or 0

        positive_result = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.status.in_(["interview", "offered", "accepted"]),
                )
            )
        )
        positive = positive_result.scalar() or 0

        negative_result = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.status == "rejected",
                )
            )
        )
        negative = negative_result.scalar() or 0

        pending_result = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.status.in_(["pending", "applied", "viewed"]),
                )
            )
        )
        pending = pending_result.scalar() or 0

        all_apps_result = await self.db.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id
            )
        )
        all_apps = all_apps_result.scalar() or 0
        response_rate = (total_responses / all_apps * 100) if all_apps > 0 else 0.0

        return ResponseAnalytics(
            total_responses=total_responses,
            positive_responses=positive,
            negative_responses=negative,
            pending=pending,
            response_rate=round(response_rate, 1),
        )

    async def get_source_analytics(self, user_id: UUID) -> SourceAnalytics:
        """Get analytics by source."""
        result = await self.db.execute(
            select(
                Application.applied_via,
                func.count(Application.id).label("total"),
                func.sum(
                    case(
                        (Application.response_received == True, 1),
                        else_=0,
                    )
                ).label("responses"),
            )
            .where(
                and_(
                    Application.user_id == user_id,
                    Application.applied_via.isnot(None),
                )
            )
            .group_by(Application.applied_via)
        )
        rows = result.all()

        sources = []
        by_response_rate = {}
        best_source = None
        best_rate = 0.0

        for source, total, responses in rows:
            rate = (responses / total * 100) if total > 0 else 0.0
            sources.append({
                "source": source,
                "total": total,
                "responses": responses or 0,
                "response_rate": round(rate, 1),
            })
            by_response_rate[source] = round(rate, 1)
            if rate > best_rate:
                best_rate = rate
                best_source = source

        return SourceAnalytics(
            sources=sources,
            most_effective_source=best_source,
            by_response_rate=by_response_rate,
        )

    async def get_daily_analytics(
        self,
        user_id: UUID,
        days: int = 30,
    ) -> DailyAnalyticsResponse:
        """Get daily analytics for the past N days."""
        now = datetime.now(timezone.utc)
        start_date = (now - timedelta(days=days)).date()
        end_date = now.date()

        result = await self.db.execute(
            select(
                func.date(Application.created_at).label("day"),
                func.count(Application.id).label("applications"),
                func.sum(
                    case(
                        (Application.response_received == True, 1),
                        else_=0,
                    )
                ).label("responses"),
                func.sum(
                    case(
                        (Application.status == "interview", 1),
                        else_=0,
                    )
                ).label("interviews"),
                func.sum(
                    case(
                        (Application.status.in_(["offered", "accepted"]), 1),
                        else_=0,
                    )
                ).label("offers"),
            )
            .where(
                and_(
                    Application.user_id == user_id,
                    func.date(Application.created_at) >= start_date,
                )
            )
            .group_by(func.date(Application.created_at))
            .order_by(func.date(Application.created_at))
        )
        rows = result.all()

        # Build data with zeros for missing days
        data_map = {}
        for row in rows:
            data_map[row.day] = DailyAnalytics(
                date=row.day,
                applications=row.applications or 0,
                responses=row.responses or 0,
                interviews=row.interviews or 0,
                offers=row.offers or 0,
            )

        data = []
        current = start_date
        total_apps = 0
        total_responses = 0
        while current <= end_date:
            if current in data_map:
                data.append(data_map[current])
                total_apps += data_map[current].applications
                total_responses += data_map[current].responses
            else:
                data.append(DailyAnalytics(date=current))
            current += timedelta(days=1)

        return DailyAnalyticsResponse(
            data=data,
            period_start=start_date,
            period_end=end_date,
            total_applications=total_apps,
            total_responses=total_responses,
        )
