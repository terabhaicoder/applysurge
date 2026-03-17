"""
Application processing tasks.

Processes the application queue by automating job applications
on LinkedIn, Naukri, or via cold email.
Uses job_matches table for queue management and applications table for records.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from worker.celery_app import celery_app

logger = logging.getLogger(__name__)

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


def _get_applications_today(user_id: str, session) -> int:
    """Count applications made today for the user."""
    result = session.execute(text("""
        SELECT COUNT(*) FROM applications
        WHERE user_id = :user_id
          AND created_at >= CURRENT_DATE
    """), {"user_id": user_id})
    row = result.fetchone()
    return row[0] if row else 0


def _get_daily_limit(user_id: str, session) -> int:
    """Get the user's daily application limit from agent_settings."""
    result = session.execute(text("""
        SELECT max_applications_per_day FROM agent_settings
        WHERE user_id = :user_id
    """), {"user_id": user_id})
    row = result.fetchone()
    return row[0] if row else 25  # Default limit


def _get_primary_resume_path(user_id: str, session) -> Optional[str]:
    """Fetch the primary resume's filesystem path for the user."""
    result = session.execute(text("""
        SELECT file_path, file_name FROM resumes
        WHERE user_id = :user_id AND is_primary = true AND is_active = true
        ORDER BY created_at DESC
        LIMIT 1
    """), {"user_id": user_id})

    row = result.mappings().first()
    if not row:
        # Fall back to most recent active resume
        result = session.execute(text("""
            SELECT file_path, file_name FROM resumes
            WHERE user_id = :user_id AND is_active = true
            ORDER BY created_at DESC
            LIMIT 1
        """), {"user_id": user_id})
        row = result.mappings().first()

    if not row or not row["file_path"]:
        return None

    file_path = row["file_path"]
    # Convert stored URL/path to filesystem path
    if file_path.startswith("/storage/"):
        return f"/app{file_path}"
    return file_path


@celery_app.task(
    name="worker.tasks.application_task.process_queues",
    bind=True,
    max_retries=1,
    soft_time_limit=300,
    time_limit=600,
)
def process_queues(self):
    """
    Process application queues for all active users.
    Runs every 5 minutes via beat schedule.

    Finds users who have queued job matches and haven't hit their daily limit,
    then triggers per-user queue processing.
    """
    logger.info("Processing application queues for all users")
    session = _get_db_session()

    try:
        # Find users with queued job matches who have the agent enabled
        result = session.execute(text("""
            SELECT DISTINCT jm.user_id,
                   COALESCE(ag.max_applications_per_day, 25) AS daily_limit
            FROM job_matches jm
            INNER JOIN users u ON jm.user_id = u.id
            INNER JOIN agent_settings ag ON u.id = ag.user_id
            WHERE jm.status = 'queued'
              AND u.is_active = true
              AND ag.is_enabled = true
            ORDER BY jm.user_id
        """))

        users = [dict(row) for row in result.mappings()]
        logger.info(f"Found {len(users)} users with queued applications")

        triggered = 0
        for user in users:
            apps_today = _get_applications_today(str(user["user_id"]), session)
            remaining = user["daily_limit"] - apps_today
            if remaining > 0:
                process_user_queue.delay(
                    user_id=str(user["user_id"]),
                    max_applications=min(remaining, 5),  # Max 5 per cycle
                )
                triggered += 1

        return {"users_processed": triggered}

    except Exception as exc:
        logger.error(f"Process queues failed: {exc}", exc_info=True)
        raise self.retry(exc=exc)
    finally:
        session.close()


@celery_app.task(
    name="worker.tasks.application_task.process_user_queue",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    soft_time_limit=600,
    time_limit=900,
)
def process_user_queue(self, user_id: str, max_applications: int = 5):
    """
    Process queued job matches for a single user.
    Applies to jobs in priority order (highest match score first).
    """
    logger.info(f"Processing queue for user {user_id} (max: {max_applications})")
    session = _get_db_session()

    try:
        # Get queued job matches ordered by score
        result = session.execute(text("""
            SELECT jm.id as match_id, jm.job_id, jm.overall_score,
                   j.title, j.company, j.platform, j.source_url as url,
                   j.is_easy_apply, j.platform_job_id as external_id
            FROM job_matches jm
            INNER JOIN jobs j ON jm.job_id = j.id
            WHERE jm.user_id = :user_id
              AND jm.status = 'queued'
            ORDER BY jm.overall_score DESC, jm.created_at ASC
            LIMIT :limit
        """), {"user_id": user_id, "limit": max_applications})

        pending_jobs = [dict(row) for row in result.mappings()]
        if not pending_jobs:
            return {"status": "no_pending", "user_id": user_id}

        applied = 0
        failed = 0

        for job in pending_jobs:
            # Mark as processing
            session.execute(text("""
                UPDATE job_matches
                SET status = 'applying'
                WHERE id = :match_id
            """), {"match_id": str(job["match_id"])})
            session.commit()

            try:
                # Apply to the job synchronously within this task
                apply_to_job.apply(
                    args=[],
                    kwargs={
                        "user_id": user_id,
                        "job_id": str(job["job_id"]),
                        "match_id": str(job["match_id"]),
                    },
                )
                applied += 1
            except Exception as e:
                logger.error(
                    f"Failed to apply to job {job['job_id']} for user {user_id}: {e}"
                )
                session.execute(text("""
                    UPDATE job_matches
                    SET status = 'failed', user_notes = :error
                    WHERE id = :match_id
                """), {"match_id": str(job["match_id"]), "error": str(e)[:500]})
                session.commit()
                failed += 1

        logger.info(f"User {user_id}: applied={applied}, failed={failed}")
        return {"user_id": user_id, "applied": applied, "failed": failed}

    except Exception as exc:
        logger.error(f"Process user queue failed for {user_id}: {exc}", exc_info=True)
        session.rollback()
        raise self.retry(exc=exc)
    finally:
        session.close()


@celery_app.task(
    name="worker.tasks.application_task.apply_to_job",
    bind=True,
    max_retries=1,
    default_retry_delay=120,
    soft_time_limit=300,
    time_limit=600,
)
def apply_to_job(self, user_id: str, job_id: str, match_id: str):
    """
    Apply to a specific job via the appropriate platform.
    Supports LinkedIn Easy Apply, Naukri Apply, and cold email.
    """
    logger.info(f"Applying to job {job_id} for user {user_id}")
    session = _get_db_session()

    try:
        # Fetch job details via job_matches
        job_result = session.execute(text("""
            SELECT j.*, jm.overall_score as match_score
            FROM jobs j
            INNER JOIN job_matches jm ON j.id = jm.job_id AND jm.user_id = :user_id
            WHERE j.id = :job_id
        """), {"user_id": user_id, "job_id": job_id})

        job = job_result.mappings().first()
        if not job:
            logger.error(f"Job {job_id} not found for user {user_id}")
            return {"status": "error", "reason": "job_not_found"}

        job = dict(job)

        # Fetch user profile
        user_result = session.execute(text("""
            SELECT u.id, u.email, u.full_name, up.*
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            WHERE u.id = :user_id
        """), {"user_id": user_id})

        user = dict(user_result.mappings().first())

        # Attach primary resume filesystem path
        resume_path = _get_primary_resume_path(user_id, session)
        if resume_path:
            user["resume_file_path"] = resume_path

        # Apply based on platform
        platform = job.get("platform", "").lower()
        result = {}

        if platform == "linkedin" and job.get("is_easy_apply"):
            result = asyncio.run(_apply_linkedin(user, job))
        elif platform == "naukri":
            result = asyncio.run(_apply_naukri(user, job))
        else:
            # Fall back to cold email
            result = asyncio.run(_apply_via_email(user, job))

        # Update job match status
        match_status = "applied" if result.get("success") else "failed"
        session.execute(text("""
            UPDATE job_matches
            SET status = :status,
                is_applied = CASE WHEN :status = 'applied' THEN TRUE ELSE is_applied END,
                applied_at = CASE WHEN :status = 'applied' THEN NOW() ELSE applied_at END,
                user_notes = CASE WHEN :error IS NOT NULL THEN :error ELSE user_notes END
            WHERE id = :match_id
        """), {
            "match_id": match_id,
            "status": match_status,
            "error": result.get("error", "")[:500] if not result.get("success") else None,
        })

        # Create application record on success
        if result.get("success"):
            screenshots = result.get("screenshots") or []
            if result.get("screenshot_url"):
                screenshots.append(result["screenshot_url"])

            session.execute(text("""
                INSERT INTO applications (
                    id, user_id, job_id, platform, applied_via,
                    status, cover_letter, agent_screenshots,
                    response_received, follow_up_count, retry_count,
                    applied_at, created_at
                ) VALUES (
                    :id, :user_id, :job_id, :platform, 'agent',
                    'applied', :cover_letter, :screenshots,
                    false, 0, 0,
                    NOW(), NOW()
                )
            """), {
                "id": str(uuid4()),
                "user_id": user_id,
                "job_id": job_id,
                "platform": platform,
                "cover_letter": result.get("cover_letter", ""),
                "screenshots": json.dumps(screenshots) if screenshots else None,
            })

        session.commit()
        logger.info(f"Application result for job {job_id}: {match_status}")
        return {"status": match_status, "job_id": job_id, **result}

    except Exception as exc:
        logger.error(f"Apply to job failed: {exc}", exc_info=True)
        session.rollback()
        # Update match status to failed
        try:
            session.execute(text("""
                UPDATE job_matches
                SET status = 'failed', user_notes = :error
                WHERE id = :match_id
            """), {"match_id": match_id, "error": str(exc)[:500]})
            session.commit()
        except Exception:
            pass
        raise self.retry(exc=exc)
    finally:
        session.close()


def _get_platform_credentials(user_id: str, platform: str) -> Dict[str, Any]:
    """Fetch and decrypt platform credentials for a user."""
    from app.core.encryption import decrypt_value

    session = _get_db_session()
    try:
        result = session.execute(text("""
            SELECT platform_username, platform_email, encrypted_password
            FROM platform_credentials
            WHERE user_id = :user_id
              AND platform = :platform
              AND is_active = true
        """), {"user_id": user_id, "platform": platform})

        row = result.mappings().first()
        if not row:
            return None

        row = dict(row)
        # Decrypt password
        encrypted_password = row.get("encrypted_password")
        decrypted_password = decrypt_value(encrypted_password) if encrypted_password else None

        return {
            "email": row.get("platform_email") or row.get("platform_username"),
            "password": decrypted_password,
        }
    finally:
        session.close()


async def _apply_linkedin(user: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """Apply to a LinkedIn job using Easy Apply automation."""
    from worker.scrapers.linkedin_applicator import LinkedInApplicator

    # Get credentials from platform_credentials table
    credentials = _get_platform_credentials(str(user["id"]), "linkedin")
    if not credentials or not credentials.get("password"):
        return {
            "success": False,
            "error": "LinkedIn credentials not found or invalid",
            "method": "easy_apply",
        }

    applicator = LinkedInApplicator(user_id=str(user["id"]))
    try:
        await applicator.initialize()
        await applicator.login(credentials["email"], credentials["password"])
        result = await applicator.apply_to_job(
            job_url=job.get("source_url") or job.get("url", ""),
            user_profile=user,
            job_details=job,
        )
        return result
    finally:
        await applicator.cleanup()


async def _apply_naukri(user: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """Apply to a Naukri job."""
    from worker.scrapers.naukri_applicator import NaukriApplicator

    # Get credentials from platform_credentials table
    credentials = _get_platform_credentials(str(user["id"]), "naukri")
    if not credentials or not credentials.get("password"):
        return {
            "success": False,
            "error": "Naukri credentials not found or invalid",
            "method": "quick_apply",
        }

    applicator = NaukriApplicator(user_id=str(user["id"]))
    try:
        await applicator.initialize()
        await applicator.login(credentials["email"], credentials["password"])
        result = await applicator.apply_to_job(
            job_url=job.get("source_url") or job.get("url", ""),
            user_profile=user,
            job_details=job,
        )
        return result
    finally:
        await applicator.cleanup()


async def _apply_via_email(user: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """Apply via cold email when direct application is not available."""
    from worker.tasks.email_task import send_cold_email_task
    from worker.ai.cover_letter_generator import CoverLetterGenerator
    from worker.ai.email_generator import EmailGenerator

    # Generate cover letter
    cover_gen = CoverLetterGenerator()
    cover_letter = await cover_gen.generate(user, job)

    # Generate cold email
    email_gen = EmailGenerator()
    email_content = await email_gen.generate_cold_email(user, job, cover_letter)

    # Find hiring manager email
    from app.utils.email_finder import EmailFinder
    finder = EmailFinder()
    recipient_email = await finder.find_email(
        company=job.get("company", ""),
        domain=None,
        role="hiring manager",
    )

    if not recipient_email:
        return {
            "success": False,
            "error": "Could not find recipient email",
            "method": "email",
        }

    # Queue the email
    send_cold_email_task.delay(
        user_id=str(user["id"]),
        job_id=str(job["id"]),
        recipient_email=recipient_email,
        subject=email_content["subject"],
        body=email_content["body"],
        cover_letter=cover_letter,
    )

    return {
        "success": True,
        "method": "cold_email",
        "recipient": recipient_email,
        "cover_letter": cover_letter,
    }
