"""
Job matching task.

Uses AI to score and match discovered jobs against user profiles,
skills, and preferences. Scores range from 0-100.
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from worker.celery_app import celery_app

logger = logging.getLogger(__name__)

SCORING_MODEL = os.environ.get("LLM_PROVIDER", "gemini").lower()
SCORING_VERSION = "2.0"

# Module-level DB engine (shared across all calls to avoid connection pool exhaustion)
_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://jobpilot:jobpilot_pass@postgres:5432/jobpilot_db"
).replace("postgresql+asyncpg://", "postgresql://")
_engine = create_engine(
    _DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=1800,
)
_SessionFactory = sessionmaker(bind=_engine)


def _get_db_session():
    """Create a synchronous database session using the shared engine."""
    return _SessionFactory()


@celery_app.task(
    name="worker.tasks.job_matching.match_jobs_for_user",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    soft_time_limit=300,
    time_limit=600,
)
def match_jobs_for_user(self, user_id: str):
    """
    AI-powered job matching for a user.
    Scores each unscored job (0-100) based on user profile, skills, and preferences.
    Jobs scoring above threshold are queued for application.
    """
    logger.info(f"Starting job matching for user {user_id}")
    session = _get_db_session()

    try:
        from sqlalchemy import text

        # Fetch user profile data from actual tables
        user_result = session.execute(text("""
            SELECT u.id, u.full_name, u.email,
                   up.headline, up.summary, up.current_title,
                   up.current_company, up.years_of_experience,
                   up.industry, up.location,
                   jp.desired_titles, jp.preferred_locations,
                   jp.job_types, jp.min_salary, jp.max_salary,
                   jp.experience_levels, jp.remote_only,
                   jp.min_match_score
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            LEFT JOIN job_preferences jp ON u.id = jp.user_id
            WHERE u.id = :user_id
        """), {"user_id": user_id})

        user = user_result.mappings().first()
        if not user:
            logger.warning(f"User {user_id} not found")
            return {"status": "skipped", "reason": "user_not_found"}

        user = dict(user)
        match_threshold = user.get("min_match_score") or 70

        # Map DB field names to what JobMatcher._build_profile_context expects
        user["target_roles"] = user.get("desired_titles") or []
        user["target_locations"] = user.get("preferred_locations") or []
        user["experience_years"] = user.get("years_of_experience")
        user["preferred_job_types"] = user.get("job_types") or []
        user["bio"] = user.get("summary") or user.get("headline") or ""
        user["remote_preference"] = (
            "remote" if user.get("remote_only")
            else "any"
        )

        # Fetch user skills from user_skills table as flat list of names
        skills_result = session.execute(text("""
            SELECT us.name, us.proficiency_level, us.is_primary
            FROM user_skills us
            INNER JOIN user_profiles up ON us.profile_id = up.id
            WHERE up.user_id = :user_id
        """), {"user_id": user_id})
        skill_rows = [dict(r) for r in skills_result.mappings()]
        # JobMatcher expects skills as a comma-separated string or list of strings
        user["skills"] = ", ".join(r["name"] for r in skill_rows if r.get("name"))

        # Fetch unscored jobs from job_matches (status = 'new')
        jobs_result = session.execute(text("""
            SELECT j.id, j.title, j.company, j.location, j.description,
                   j.salary_min, j.salary_max, j.job_type,
                   j.required_skills, j.preferred_skills,
                   j.is_easy_apply, j.platform, j.source_url,
                   jm.id as match_id
            FROM jobs j
            INNER JOIN job_matches jm ON j.id = jm.job_id
            WHERE jm.user_id = :user_id
              AND jm.status = 'new'
              AND jm.overall_score = 0
            ORDER BY j.created_at DESC
            LIMIT 50
        """), {"user_id": user_id})

        jobs = [dict(row) for row in jobs_result.mappings()]
        if not jobs:
            logger.info(f"No unscored jobs for user {user_id}")
            return {"status": "no_jobs", "user_id": user_id}

        logger.info(f"Matching {len(jobs)} jobs for user {user_id}")

        # Score jobs using AI
        scores = asyncio.run(_score_jobs_batch(user, jobs))

        # Update scores and queue matched jobs
        matched_count = 0
        for job, score_data in zip(jobs, scores):
            score = score_data.get("score", 0)
            reasoning = score_data.get("reasoning", "")

            new_status = "queued" if score >= match_threshold else "rejected"

            # Extract component scores and details
            strengths = score_data.get("strengths", [])
            gaps = score_data.get("gaps", [])
            matched_skills = score_data.get("matched_skills", [])
            missing_skills = score_data.get("missing_skills", [])

            # Update job_matches with score, component scores, and status
            session.execute(text("""
                UPDATE job_matches
                SET overall_score = :score,
                    match_reasoning = :reasoning,
                    skills_score = :skills_score,
                    experience_score = :experience_score,
                    education_score = :education_score,
                    location_score = :location_score,
                    salary_score = :salary_score,
                    strengths = :strengths,
                    gaps = :gaps,
                    matched_skills = :matched_skills,
                    missing_skills = :missing_skills,
                    scoring_model = :scoring_model,
                    scoring_version = :scoring_version,
                    status = :status,
                    scored_at = NOW(),
                    is_applied = FALSE
                WHERE id = :match_id
            """), {
                "score": score,
                "reasoning": reasoning,
                "skills_score": score_data.get("skills_score", 0),
                "experience_score": score_data.get("experience_score", 0),
                "education_score": score_data.get("role_score", 0),
                "location_score": score_data.get("location_score", 0),
                "salary_score": score_data.get("salary_score", 0),
                "strengths": json.dumps(strengths) if strengths else None,
                "gaps": json.dumps(gaps) if gaps else None,
                "matched_skills": json.dumps(matched_skills) if matched_skills else None,
                "missing_skills": json.dumps(missing_skills) if missing_skills else None,
                "scoring_model": SCORING_MODEL,
                "scoring_version": SCORING_VERSION,
                "status": new_status,
                "match_id": job["match_id"],
            })

            if score >= match_threshold:
                matched_count += 1

        session.commit()
        logger.info(
            f"Matched {matched_count}/{len(jobs)} jobs for user {user_id} "
            f"(threshold: {match_threshold})"
        )

        return {
            "user_id": user_id,
            "total_scored": len(jobs),
            "matched": matched_count,
            "threshold": match_threshold,
        }

    except Exception as exc:
        logger.error(f"Job matching failed for user {user_id}: {exc}", exc_info=True)
        session.rollback()
        raise self.retry(exc=exc)
    finally:
        session.close()


async def _score_jobs_batch(
    user: Dict[str, Any], jobs: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Score a batch of jobs using AI matching."""
    from worker.ai.job_matcher import JobMatcher

    matcher = JobMatcher()
    scores = []

    # Process in chunks of 5 to avoid rate limits
    chunk_size = 5
    for i in range(0, len(jobs), chunk_size):
        chunk = jobs[i:i + chunk_size]
        chunk_scores = await matcher.score_jobs(user, chunk)
        scores.extend(chunk_scores)

    return scores
