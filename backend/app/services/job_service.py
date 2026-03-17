"""
Job listing, filtering, and queue management service.
Uses JobMatch model for user-specific job interactions (save, hide, queue).
"""

from datetime import datetime, timezone
from typing import List, Tuple
from uuid import UUID

from sqlalchemy import select, func, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError
from app.models.job import Job
from app.models.job_match import JobMatch
from app.schemas.job import JobResponse, JobListFilters, JobQueueItem


class JobService:
    """Service for job operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_jobs(
        self,
        user_id: UUID,
        filters: JobListFilters,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[JobResponse], int]:
        """List jobs with filtering and pagination.

        Only shows jobs that have been discovered for this specific user
        (i.e., have a job_match entry) and are not dismissed.
        """
        # Only show jobs that belong to this user via job_matches
        user_job_ids = select(JobMatch.job_id).where(
            JobMatch.user_id == user_id,
            JobMatch.is_dismissed == False,
        )

        query = select(Job).where(Job.is_active == True, Job.id.in_(user_job_ids))
        count_query = select(func.count(Job.id)).where(Job.is_active == True, Job.id.in_(user_job_ids))

        # Apply filters
        if filters.search:
            search_filter = or_(
                Job.title.ilike(f"%{filters.search}%"),
                Job.company.ilike(f"%{filters.search}%"),
                Job.description.ilike(f"%{filters.search}%"),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        if filters.location:
            loc_filter = Job.location.ilike(f"%{filters.location}%")
            query = query.where(loc_filter)
            count_query = count_query.where(loc_filter)

        if filters.remote_type:
            query = query.where(Job.work_arrangement == filters.remote_type)
            count_query = count_query.where(Job.work_arrangement == filters.remote_type)

        if filters.job_type:
            query = query.where(Job.job_type == filters.job_type)
            count_query = count_query.where(Job.job_type == filters.job_type)

        if filters.experience_level:
            query = query.where(Job.experience_level == filters.experience_level)
            count_query = count_query.where(Job.experience_level == filters.experience_level)

        if filters.min_salary:
            query = query.where(Job.salary_max >= filters.min_salary)
            count_query = count_query.where(Job.salary_max >= filters.min_salary)

        if filters.max_salary:
            query = query.where(Job.salary_min <= filters.max_salary)
            count_query = count_query.where(Job.salary_min <= filters.max_salary)

        if filters.company:
            query = query.where(Job.company.ilike(f"%{filters.company}%"))
            count_query = count_query.where(Job.company.ilike(f"%{filters.company}%"))

        if filters.source:
            query = query.where(Job.platform == filters.source)
            count_query = count_query.where(Job.platform == filters.source)

        if filters.posted_after:
            query = query.where(Job.posted_at >= filters.posted_after)
            count_query = count_query.where(Job.posted_at >= filters.posted_after)

        # Total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Sorting
        sort_column = getattr(Job, filters.sort_by, Job.posted_at)
        order_func = desc if filters.sort_order == "desc" else asc
        query = query.order_by(order_func(sort_column))

        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        jobs = result.scalars().all()

        # Enrich with user-specific data from JobMatch
        job_ids = [j.id for j in jobs]
        if job_ids:
            matches_result = await self.db.execute(
                select(JobMatch).where(
                    JobMatch.user_id == user_id,
                    JobMatch.job_id.in_(job_ids),
                )
            )
            matches_map = {m.job_id: m for m in matches_result.scalars().all()}
        else:
            matches_map = {}

        responses = []
        for job in jobs:
            match = matches_map.get(job.id)
            response = self._to_response(job, match)
            responses.append(response)

        return responses, total

    async def get_job(self, user_id: UUID, job_id: UUID) -> JobResponse:
        """Get a specific job."""
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise NotFoundError("Job")

        # Get user match data
        match_result = await self.db.execute(
            select(JobMatch).where(
                JobMatch.user_id == user_id, JobMatch.job_id == job_id
            )
        )
        match = match_result.scalar_one_or_none()

        return self._to_response(job, match)

    async def save_job(self, user_id: UUID, job_id: UUID) -> bool:
        """Save (bookmark) a job."""
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        if not result.scalar_one_or_none():
            raise NotFoundError("Job")

        match = await self._get_or_create_match(user_id, job_id)
        if match.is_bookmarked:
            raise ConflictError("Job already saved")

        match.is_bookmarked = True
        match.bookmarked_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def hide_job(self, user_id: UUID, job_id: UUID) -> bool:
        """Hide (dismiss) a job from listing."""
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        if not result.scalar_one_or_none():
            raise NotFoundError("Job")

        match = await self._get_or_create_match(user_id, job_id)
        match.is_dismissed = True
        match.dismissed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def queue_job(self, user_id: UUID, job_id: UUID, priority: int = 0) -> bool:
        """Add a job to the application queue by setting status to 'queued'."""
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        if not result.scalar_one_or_none():
            raise NotFoundError("Job")

        match = await self._get_or_create_match(user_id, job_id)
        if match.status == "queued":
            raise ConflictError("Job already in queue")

        match.status = "queued"
        await self.db.flush()
        return True

    async def unqueue_job(self, user_id: UUID, job_id: UUID) -> bool:
        """Remove a job from the application queue."""
        result = await self.db.execute(
            select(JobMatch).where(
                JobMatch.user_id == user_id,
                JobMatch.job_id == job_id,
                JobMatch.status == "queued",
            )
        )
        match = result.scalar_one_or_none()
        if not match:
            raise NotFoundError("Job not found in queue")

        match.status = "new"
        await self.db.flush()
        return True

    async def get_queue(self, user_id: UUID) -> List[JobQueueItem]:
        """Get user's job application queue."""
        result = await self.db.execute(
            select(JobMatch)
            .where(
                JobMatch.user_id == user_id,
                JobMatch.status == "queued",
            )
            .order_by(JobMatch.overall_score.desc(), JobMatch.created_at.asc())
        )
        matches = result.scalars().all()

        responses = []
        for match in matches:
            job_result = await self.db.execute(
                select(Job).where(Job.id == match.job_id)
            )
            job = job_result.scalar_one_or_none()
            if job:
                responses.append(
                    JobQueueItem(
                        id=match.id,
                        job_id=match.job_id,
                        user_id=match.user_id,
                        job=self._to_response(job, match),
                        priority=0,
                        status=match.status,
                        created_at=match.created_at,
                    )
                )

        return responses

    async def _get_or_create_match(self, user_id: UUID, job_id: UUID) -> JobMatch:
        """Get or create a JobMatch entry."""
        result = await self.db.execute(
            select(JobMatch).where(
                JobMatch.user_id == user_id, JobMatch.job_id == job_id
            )
        )
        match = result.scalar_one_or_none()

        if not match:
            match = JobMatch(
                user_id=user_id,
                job_id=job_id,
                overall_score=0.0,
                status="new",
            )
            self.db.add(match)
            await self.db.flush()
            await self.db.refresh(match)

        return match

    def _to_response(self, job: Job, match: JobMatch = None) -> JobResponse:
        """Convert Job model to response schema."""
        return JobResponse(
            id=job.id,
            title=job.title,
            company=job.company,
            location=job.location,
            remote_type=job.work_arrangement,
            is_remote=job.is_remote or False,
            job_type=job.job_type,
            experience_level=job.experience_level,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_currency=job.salary_currency,
            salary_text=job.salary_text,
            description=job.description,
            description_html=job.description_html,
            requirements=job.requirements,
            responsibilities=job.responsibilities,
            qualifications=job.qualifications,
            nice_to_have=job.nice_to_have,
            benefits=job.benefits,
            skills=job.required_skills,
            preferred_skills=job.preferred_skills,
            technologies=job.technologies,
            source=job.platform,
            source_url=job.source_url,
            company_logo_url=job.company_logo_url,
            company_size=job.company_size,
            company_industry=job.company_industry,
            applicant_count=job.applicant_count,
            is_easy_apply=job.is_easy_apply or False,
            is_saved=match.is_bookmarked if match else False,
            is_hidden=match.is_dismissed if match else False,
            is_queued=(match.status == "queued") if match else False,
            match_score=match.overall_score if match else None,
            match_reasoning=match.match_reasoning if match else None,
            strengths=match.strengths if match else None,
            gaps=match.gaps if match else None,
            matched_skills=match.matched_skills if match else None,
            missing_skills=match.missing_skills if match else None,
            posted_at=job.posted_at,
            created_at=job.created_at,
        )
