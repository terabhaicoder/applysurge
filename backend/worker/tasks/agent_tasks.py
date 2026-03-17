"""
Agent orchestration tasks.

Main entry point for the automation agent. Handles the complete workflow:
- Job discovery across platforms
- Job matching and scoring
- Application queue processing
- Rate limiting and daily limits
- Start/stop/pause signal handling
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from worker.celery_app import celery_app

logger = logging.getLogger(__name__)

# Redis client for signals and state
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

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


def _check_stop_signal(user_id: str) -> bool:
    """Check if stop signal has been sent for this agent session.
    Uses atomic getdel to avoid race conditions with multiple workers."""
    stop_key = f"jobpilot:agent:stop:{user_id}"
    # Atomic get-and-delete: only one caller sees the value
    stopped = redis_client.getdel(stop_key)
    return stopped is not None


def _acquire_session_lock(user_id: str, ttl: int = 3900) -> bool:
    """Try to acquire an exclusive session lock for this user.
    Returns True if lock acquired, False if another session is already running.
    TTL matches the task hard time limit (1hr 5min)."""
    lock_key = f"jobpilot:agent:session_lock:{user_id}"
    return bool(redis_client.set(lock_key, "1", nx=True, ex=ttl))


def _release_session_lock(user_id: str):
    """Release the exclusive session lock for this user."""
    lock_key = f"jobpilot:agent:session_lock:{user_id}"
    redis_client.delete(lock_key)


def _set_agent_running(user_id: str, is_running: bool, session=None):
    """Update agent running status in database."""
    close_session = False
    if session is None:
        session = _get_db_session()
        close_session = True

    try:
        from sqlalchemy import text
        session.execute(text("""
            UPDATE agent_settings
            SET is_running = :is_running,
                last_run_at = CASE WHEN :is_running THEN NOW() ELSE last_run_at END
            WHERE user_id = :user_id
        """), {"user_id": user_id, "is_running": is_running})
        session.commit()
    finally:
        if close_session:
            session.close()


def _increment_error_count(user_id: str, error_message: str, session=None):
    """Increment consecutive error count and log the error."""
    close_session = False
    if session is None:
        session = _get_db_session()
        close_session = True

    try:
        from sqlalchemy import text
        session.execute(text("""
            UPDATE agent_settings
            SET consecutive_errors = consecutive_errors + 1,
                last_error = :error
            WHERE user_id = :user_id
        """), {"user_id": user_id, "error": error_message[:500]})
        session.commit()
    finally:
        if close_session:
            session.close()


def _reset_error_count(user_id: str, session=None):
    """Reset error count after successful operation."""
    close_session = False
    if session is None:
        session = _get_db_session()
        close_session = True

    try:
        from sqlalchemy import text
        session.execute(text("""
            UPDATE agent_settings
            SET consecutive_errors = 0, last_error = NULL
            WHERE user_id = :user_id
        """), {"user_id": user_id})
        session.commit()
    finally:
        if close_session:
            session.close()


def _log_agent_activity(user_id: str, action: str, message: str, details: Dict = None, session=None):
    """Log agent activity to Redis for real-time streaming."""
    import json
    from uuid import uuid4

    log_entry = {
        "id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "message": message,
        "details": details or {},
        "is_error": "error" in action.lower() or "fail" in action.lower(),
    }

    # Publish to Redis channel for real-time updates
    channel = f"jobpilot:agent:logs:{user_id}"
    redis_client.publish(channel, json.dumps(log_entry))

    # Also store in list for persistence (keep last 100)
    list_key = f"jobpilot:agent:logs:history:{user_id}"
    redis_client.lpush(list_key, json.dumps(log_entry))
    redis_client.ltrim(list_key, 0, 99)
    redis_client.expire(list_key, 86400 * 7)  # 7 days TTL


def _get_user_credentials(user_id: str, platform: str, session) -> Optional[Dict[str, str]]:
    """Fetch and decrypt user credentials for a platform."""
    from sqlalchemy import text
    from app.core.encryption import decrypt_value

    result = session.execute(text("""
        SELECT platform_email, platform_username, encrypted_password
        FROM platform_credentials
        WHERE user_id = :user_id AND platform = :platform AND is_active = true
    """), {"user_id": user_id, "platform": platform})

    row = result.mappings().first()
    if not row:
        return None

    # Decrypt password using the same module that encrypted it
    encrypted_password = row["encrypted_password"]
    if not encrypted_password:
        logger.error(f"No encrypted password found for {user_id}/{platform}")
        return None

    password = decrypt_value(encrypted_password)
    if not password:
        logger.error(f"Failed to decrypt credentials for {user_id}/{platform}")
        return None

    return {
        "email": row["platform_email"] or row["platform_username"],
        "password": password,
    }


def _get_primary_resume_path(user_id: str, session) -> Optional[str]:
    """Fetch the primary resume's filesystem path for the user.

    Returns the actual filesystem path (e.g. /app/storage/resumes/...)
    that can be used by Playwright's set_input_files().
    """
    from sqlalchemy import text

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
    # Stored as "/storage/resumes/..." by local storage, need "/app/storage/resumes/..."
    if file_path.startswith("/storage/"):
        return f"/app{file_path}"
    # If stored as S3 URL, download to temp location
    if file_path.startswith("http"):
        return _download_resume_to_temp(file_path, row["file_name"])
    # Already a filesystem path
    return file_path


def _download_resume_to_temp(url: str, filename: str) -> Optional[str]:
    """Download a resume from S3 URL to a temporary location."""
    import tempfile
    import requests

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        temp_dir = tempfile.mkdtemp(prefix="jobpilot_resume_")
        temp_path = os.path.join(temp_dir, filename or "resume.pdf")
        with open(temp_path, "wb") as f:
            f.write(response.content)
        return temp_path
    except Exception as e:
        logger.error(f"Failed to download resume from {url}: {e}")
        return None


def _get_agent_settings(user_id: str, session) -> Dict[str, Any]:
    """Fetch agent settings for user."""
    from sqlalchemy import text

    result = session.execute(text("""
        SELECT * FROM agent_settings WHERE user_id = :user_id
    """), {"user_id": user_id})

    row = result.mappings().first()
    if row:
        return dict(row)

    # Return defaults if not found
    return {
        "max_applications_per_day": 10,
        "cooldown_seconds": 30,
        "min_match_score": 0.7,
        "auto_generate_cover_letter": True,
        "apply_to_easy_apply_only": False,
        "headless_mode": True,
    }


def _get_applications_today(user_id: str, session) -> int:
    """Get count of applications made today."""
    from sqlalchemy import text

    result = session.execute(text("""
        SELECT COUNT(*) as count
        FROM applications
        WHERE user_id = :user_id
          AND applied_via = 'agent'
          AND created_at >= CURRENT_DATE
    """), {"user_id": user_id})

    row = result.fetchone()
    return row[0] if row else 0


def _get_total_applications(user_id: str, session) -> int:
    """Get total application count for beta quota check."""
    from sqlalchemy import text

    result = session.execute(text("""
        SELECT COUNT(*) as count
        FROM applications
        WHERE user_id = :user_id
    """), {"user_id": user_id})

    row = result.fetchone()
    return row[0] if row else 0


def _get_user_email(user_id: str, session) -> str:
    """Get user email for admin bypass check."""
    from sqlalchemy import text

    result = session.execute(text("""
        SELECT email FROM users WHERE id = :user_id
    """), {"user_id": user_id})

    row = result.fetchone()
    return row[0] if row else ""


def _is_admin_user(user_email: str) -> bool:
    """Check if user email is in the admin bypass list."""
    admin_emails_str = os.environ.get("ADMIN_EMAILS", "paarth.paan3@gmail.com")
    admin_emails = [e.strip().lower() for e in admin_emails_str.split(",") if e.strip()]
    return user_email.lower() in admin_emails


def _get_pending_jobs(user_id: str, limit: int, session) -> list:
    """Get pending jobs from queue ordered by match score."""
    from sqlalchemy import text

    result = session.execute(text("""
        SELECT
            jm.id as match_id,
            jm.job_id,
            jm.overall_score as match_score,
            j.title,
            j.company,
            j.location,
            j.source_url as url,
            j.platform,
            j.is_easy_apply,
            j.platform_job_id as external_id
        FROM job_matches jm
        INNER JOIN jobs j ON jm.job_id = j.id
        WHERE jm.user_id = :user_id
          AND jm.status = 'queued'
        ORDER BY jm.overall_score DESC, jm.created_at ASC
        LIMIT :limit
    """), {"user_id": user_id, "limit": limit})

    return [dict(row) for row in result.mappings()]


def _update_job_status(match_id: str, status: str, session, error: str = None):
    """Update job match status."""
    from sqlalchemy import text

    session.execute(text("""
        UPDATE job_matches
        SET status = :status,
            applied_at = CASE WHEN :status = 'applied' THEN NOW() ELSE applied_at END,
            is_applied = CASE WHEN :status = 'applied' THEN TRUE ELSE is_applied END,
            user_notes = CASE WHEN :error IS NOT NULL THEN :error ELSE user_notes END
        WHERE id = :match_id
    """), {"match_id": match_id, "status": status, "error": error})
    session.commit()


@celery_app.task(
    name="worker.tasks.agent_tasks.run_agent_session",
    bind=True,
    max_retries=0,
    soft_time_limit=3600,  # 1 hour soft limit
    time_limit=3900,  # 1 hour 5 min hard limit
)
def run_agent_session(self, user_id: str):
    """
    Main agent session orchestrator.

    This is the entry point when a user starts the agent.
    It runs a continuous loop of:
    1. Discover new jobs (if queue is low)
    2. Match jobs to user profile
    3. Apply to queued jobs
    4. Respect rate limits and daily caps
    5. Check for stop signals
    """
    logger.info(f"Starting agent session for user {user_id}")
    session = None

    # Create a single event loop for the entire session to avoid
    # asyncio.run() creating/destroying loops which breaks Playwright.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Prevent duplicate sessions: only one agent session per user at a time
    if not _acquire_session_lock(user_id):
        logger.warning(f"Agent session already running for user {user_id}, skipping duplicate")
        # Update DB to reflect actual state (lock might be stale from crashed worker)
        _set_agent_running(user_id, False)
        return {"status": "already_running", "user_id": user_id}

    try:
        session = _get_db_session()

        # Clear any stale stop signal from previous sessions
        _check_stop_signal(user_id)

        # Mark agent as running
        _set_agent_running(user_id, True, session)
        _log_agent_activity(user_id, "session_started", "Agent session started")

        # Get agent settings
        agent_settings = _get_agent_settings(user_id, session)
        cooldown = agent_settings.get("cooldown_seconds", 30)
        max_daily = agent_settings.get("max_applications_per_day", 10)
        min_score = agent_settings.get("min_match_score", 0.7)

        # Beta limit check
        beta_limit = int(os.environ.get("BETA_MAX_TOTAL_APPLICATIONS", "10"))
        user_email = _get_user_email(user_id, session)
        is_admin = _is_admin_user(user_email)

        if not is_admin:
            total_apps = _get_total_applications(user_id, session)
            if total_apps >= beta_limit:
                logger.info(f"Beta limit reached for user {user_id}: {total_apps}/{beta_limit}")
                _log_agent_activity(
                    user_id, "beta_limit_reached",
                    f"Beta application limit reached ({total_apps}/{beta_limit}). Session complete."
                )
                _log_agent_activity(user_id, "session_complete", "Agent session completed")
                return {"status": "beta_limit", "user_id": user_id}

        # Single iteration: discover → match → apply all queued → stop
        # Check for stop signal
        if _check_stop_signal(user_id):
            logger.info(f"Stop signal received for user {user_id}")
            _log_agent_activity(user_id, "session_stopped", "Agent stopped by user")
            _log_agent_activity(user_id, "session_complete", "Agent session completed")
            return {"status": "stopped", "user_id": user_id}

        # Check daily limit
        apps_today = _get_applications_today(user_id, session)
        if apps_today >= max_daily:
            logger.info(f"Daily limit reached for user {user_id}: {apps_today}/{max_daily}")
            _log_agent_activity(
                user_id, "daily_limit_reached",
                f"Daily application limit reached ({apps_today}/{max_daily})"
            )
            _log_agent_activity(user_id, "session_complete", "Agent session completed")
            return {"status": "daily_limit", "user_id": user_id}

        remaining = max_daily - apps_today
        # Cap remaining by beta limit
        if not is_admin:
            total_apps = _get_total_applications(user_id, session)
            beta_remaining = beta_limit - total_apps
            remaining = min(remaining, beta_remaining)

        # Get pending jobs from queue
        session.commit()
        pending_jobs = _get_pending_jobs(user_id, remaining, session)

        # If no queued jobs, run discovery + matching once
        if not pending_jobs:
            logger.info(f"No pending jobs for user {user_id}, triggering discovery")
            _log_agent_activity(user_id, "discovering_jobs", "Searching for new jobs...")

            try:
                from worker.tasks.job_discovery import discover_jobs_for_user
                discover_jobs_for_user.apply(args=[user_id])

                from worker.tasks.job_matching import match_jobs_for_user
                match_jobs_for_user.apply(args=[user_id])

                # CRITICAL: Re-set event loop after discovery/matching.
                # They use asyncio.run() internally which clears the loop.
                asyncio.set_event_loop(loop)

                time.sleep(10)
                session.commit()
                pending_jobs = _get_pending_jobs(user_id, remaining, session)
                logger.info(f"After discovery+matching: found {len(pending_jobs)} pending jobs")

            except Exception as e:
                logger.error(f"Job discovery failed for {user_id}: {e}")
                _log_agent_activity(user_id, "discovery_error", f"Job discovery error: {str(e)}")

        if not pending_jobs:
            _log_agent_activity(user_id, "no_jobs_found", "No matching jobs found in this run.")
            _log_agent_activity(user_id, "session_complete", "Agent session completed")
            return {"status": "no_jobs", "user_id": user_id}

        # Apply to all queued jobs
        logger.info(f"Processing {len(pending_jobs)} pending jobs for user {user_id}")
        for job in pending_jobs:
            # Check stop signal before each application
            if _check_stop_signal(user_id):
                logger.info(f"Stop signal received during processing for user {user_id}")
                _log_agent_activity(user_id, "session_stopped", "Agent stopped by user")
                break

            # Check daily limit
            apps_today = _get_applications_today(user_id, session)
            if apps_today >= max_daily:
                _log_agent_activity(
                    user_id, "daily_limit_reached",
                    f"Daily limit reached ({apps_today}/{max_daily}). Session complete."
                )
                break

            # Check beta limit before each application
            if not is_admin:
                total_apps = _get_total_applications(user_id, session)
                if total_apps >= beta_limit:
                    _log_agent_activity(
                        user_id, "beta_limit_reached",
                        f"Beta limit reached ({total_apps}/{beta_limit}). Session complete."
                    )
                    break

            job_title = job.get("title", "Unknown")
            company = job.get("company", "Unknown")
            platform = job.get("platform", "").lower()

            _log_agent_activity(
                user_id, "applying",
                f"Applying to {job_title} at {company}",
                {"job_id": str(job["job_id"]), "platform": platform}
            )

            try:
                # Mark job as processing
                _update_job_status(str(job["match_id"]), "applying", session)

                # Ensure event loop is set (may get cleared by prior asyncio.run calls)
                asyncio.set_event_loop(loop)

                # Apply based on platform
                logger.info(f"Applying to {job_title} at {company} via {platform} (easy_apply={job.get('is_easy_apply')})")
                if platform == "linkedin" and job.get("is_easy_apply"):
                    result = loop.run_until_complete(_apply_linkedin_job(user_id, job, session))
                elif platform == "naukri":
                    result = loop.run_until_complete(_apply_naukri_job(user_id, job, session))
                else:
                    _update_job_status(str(job["match_id"]), "skipped", session, "Platform not supported for auto-apply")
                    _log_agent_activity(
                        user_id, "skipped",
                        f"Skipped {job_title} - platform not supported for auto-apply"
                    )
                    continue

                if result.get("success"):
                    _update_job_status(str(job["match_id"]), "applied", session)
                    _reset_error_count(user_id, session)
                    _log_agent_activity(
                        user_id, "applied",
                        f"Successfully applied to {job_title} at {company}",
                        {"screenshot": result.get("screenshot_url")}
                    )
                    _create_application_record(user_id, job, result, session)
                elif result.get("expired"):
                    _update_job_status(str(job["match_id"]), "expired", session)
                    _log_agent_activity(
                        user_id, "job_expired",
                        f"Skipped {job_title} at {company} - job no longer accepting applications"
                    )
                elif result.get("already_applied"):
                    _update_job_status(str(job["match_id"]), "applied", session)
                    _log_agent_activity(
                        user_id, "already_applied",
                        f"Already applied to {job_title} at {company}"
                    )
                elif result.get("external_apply"):
                    _update_job_status(str(job["match_id"]), "skipped", session, "External apply - not Easy Apply")
                    try:
                        from sqlalchemy import text as sql_text
                        session.execute(
                            sql_text("UPDATE jobs SET is_easy_apply = false WHERE id = :job_id"),
                            {"job_id": str(job["job_id"])}
                        )
                        session.commit()
                    except Exception:
                        pass
                    _log_agent_activity(
                        user_id, "external_apply",
                        f"Skipped {job_title} at {company} - external apply (not Easy Apply)"
                    )
                else:
                    error_msg = result.get("error", "Unknown error")
                    _update_job_status(str(job["match_id"]), "failed", session, error_msg)
                    _increment_error_count(user_id, error_msg, session)
                    _create_application_record(user_id, job, result, session, status="failed")
                    _log_agent_activity(
                        user_id, "application_failed",
                        f"Failed to apply to {job_title}: {error_msg}"
                    )

            except Exception as e:
                error_msg = str(e)
                logger.error(f"Application error for job {job['job_id']}: {e}", exc_info=True)
                _update_job_status(str(job["match_id"]), "failed", session, error_msg)
                _increment_error_count(user_id, error_msg, session)
                _create_application_record(user_id, job, {"error": error_msg}, session, status="failed")
                _log_agent_activity(
                    user_id, "application_error",
                    f"Error applying to {job_title}: {error_msg}"
                )

            # Cooldown between applications
            _log_agent_activity(user_id, "cooldown", f"Waiting {cooldown} seconds...")
            time.sleep(cooldown)

        _log_agent_activity(user_id, "session_complete", "Agent session completed")
        return {"status": "completed", "user_id": user_id}

    except Exception as e:
        logger.error(f"Agent session error for {user_id}: {e}", exc_info=True)
        _log_agent_activity(user_id, "session_error", f"Agent session error: {str(e)}")
        _increment_error_count(user_id, str(e))
        raise

    finally:
        # Always release session lock and mark agent as not running
        _release_session_lock(user_id)
        if session:
            try:
                _set_agent_running(user_id, False, session)
            except Exception:
                pass
            session.close()
        try:
            loop.close()
        except Exception:
            pass


async def _apply_linkedin_job(user_id: str, job: Dict, session) -> Dict[str, Any]:
    """Apply to a LinkedIn job using Easy Apply."""
    from worker.scrapers.linkedin_applicator import LinkedInApplicator

    # Get credentials
    credentials = _get_user_credentials(user_id, "linkedin", session)
    if not credentials:
        return {"success": False, "error": "LinkedIn credentials not found"}

    # Get user profile
    from sqlalchemy import text
    result = session.execute(text("""
        SELECT u.email, u.full_name, up.*
        FROM users u
        LEFT JOIN user_profiles up ON u.id = up.user_id
        WHERE u.id = :user_id
    """), {"user_id": user_id})
    user_profile = dict(result.mappings().first() or {})

    # Attach primary resume filesystem path for Easy Apply upload
    resume_path = _get_primary_resume_path(user_id, session)
    if resume_path:
        user_profile["resume_file_path"] = resume_path

    applicator = LinkedInApplicator(user_id=user_id)
    try:
        await applicator.initialize()
        await applicator.login(credentials["email"], credentials["password"])

        result = await applicator.apply_to_job(
            job_url=job["url"],
            user_profile=user_profile,
            job_details=job,
        )
        return result

    except Exception as e:
        logger.error(f"LinkedIn application error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

    finally:
        await applicator.cleanup()


async def _apply_naukri_job(user_id: str, job: Dict, session) -> Dict[str, Any]:
    """Apply to a Naukri job."""
    from worker.scrapers.naukri_applicator import NaukriApplicator

    # Get credentials
    credentials = _get_user_credentials(user_id, "naukri", session)
    if not credentials:
        return {"success": False, "error": "Naukri credentials not found"}

    # Get user profile
    from sqlalchemy import text
    result = session.execute(text("""
        SELECT u.email, u.full_name, up.*
        FROM users u
        LEFT JOIN user_profiles up ON u.id = up.user_id
        WHERE u.id = :user_id
    """), {"user_id": user_id})
    user_profile = dict(result.mappings().first() or {})

    # Attach primary resume filesystem path for application upload
    resume_path = _get_primary_resume_path(user_id, session)
    if resume_path:
        user_profile["resume_file_path"] = resume_path

    applicator = NaukriApplicator(user_id=user_id)
    try:
        await applicator.initialize()
        await applicator.login(credentials["email"], credentials["password"])

        result = await applicator.apply_to_job(
            job_url=job["url"],
            user_profile=user_profile,
            job_details=job,
        )
        return result

    except Exception as e:
        logger.error(f"Naukri application error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

    finally:
        await applicator.cleanup()


def _create_application_record(user_id: str, job: Dict, result: Dict, session, status: str = "applied"):
    """Create an application record in the database."""
    from sqlalchemy import text
    from uuid import uuid4

    try:
        import json
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
                :status, :cover_letter, :screenshots,
                false, 0, 0,
                NOW(), NOW()
            )
        """), {
            "id": str(uuid4()),
            "user_id": user_id,
            "job_id": str(job["job_id"]),
            "platform": job.get("platform", "linkedin"),
            "status": status,
            "cover_letter": result.get("cover_letter", ""),
            "screenshots": json.dumps(screenshots) if screenshots else None,
        })
        session.commit()
    except Exception as e:
        logger.error(f"Failed to create application record: {e}")
        session.rollback()


@celery_app.task(
    name="worker.tasks.agent_tasks.validate_credentials_task",
    bind=True,
    max_retries=0,
    soft_time_limit=120,
    time_limit=180,
)
def validate_credentials_task(self, user_id: str, platform: str):
    """
    Validate user credentials by attempting a real login.

    Initializes the appropriate scraper, attempts login, and updates
    the credential record in the database with the result.
    """
    logger.info(f"Validating {platform} credentials for user {user_id}")
    session = _get_db_session()

    try:
        # Fetch and decrypt credentials
        credentials = _get_user_credentials(user_id, platform, session)
        if not credentials:
            _update_credential_status(
                user_id, platform, is_verified=False,
                error="Credentials not found", session=session,
            )
            return {"success": False, "error": "Credentials not found"}

        # Attempt login with the appropriate scraper
        login_success = asyncio.run(
            _test_login(platform, credentials["email"], credentials["password"])
        )

        if login_success:
            _update_credential_status(
                user_id, platform, is_verified=True, error=None, session=session,
            )
            return {"success": True, "message": f"{platform.title()} login successful"}
        else:
            _update_credential_status(
                user_id, platform, is_verified=False,
                error="Login failed - check username/password", session=session,
            )
            return {"success": False, "error": "Login failed"}

    except Exception as e:
        logger.error(f"Credential validation error for {user_id}/{platform}: {e}")
        _update_credential_status(
            user_id, platform, is_verified=False,
            error=str(e)[:500], session=session,
        )
        return {"success": False, "error": str(e)}

    finally:
        session.close()


async def _test_login(platform: str, email: str, password: str) -> bool:
    """Test login with the appropriate platform scraper."""
    if platform == "linkedin":
        from worker.scrapers.linkedin_applicator import LinkedInApplicator
        applicator = LinkedInApplicator(user_id="validation")
    elif platform == "naukri":
        from worker.scrapers.naukri_applicator import NaukriApplicator
        applicator = NaukriApplicator(user_id="validation")
    else:
        raise ValueError(f"Unsupported platform: {platform}")

    try:
        await applicator.initialize()
        result = await applicator.login(email, password)
        return bool(result)
    finally:
        await applicator.cleanup()


def _update_credential_status(
    user_id: str, platform: str, is_verified: bool,
    error: Optional[str], session=None,
):
    """Update credential verification status in the database."""
    close_session = False
    if session is None:
        session = _get_db_session()
        close_session = True

    try:
        from sqlalchemy import text
        session.execute(text("""
            UPDATE platform_credentials
            SET is_verified = :is_verified,
                last_verified_at = NOW(),
                last_error = :error
            WHERE user_id = :user_id AND platform = :platform
        """), {
            "user_id": user_id,
            "platform": platform,
            "is_verified": is_verified,
            "error": error,
        })
        session.commit()
    finally:
        if close_session:
            session.close()


@celery_app.task(
    name="worker.tasks.agent_tasks.stop_agent_session",
    bind=True,
)
def stop_agent_session(self, user_id: str):
    """Send stop signal to running agent session."""
    stop_key = f"jobpilot:agent:stop:{user_id}"
    redis_client.set(stop_key, "1", ex=300)  # 5 minute TTL
    _log_agent_activity(user_id, "stop_requested", "Stop signal sent to agent")
    return {"status": "stop_signal_sent", "user_id": user_id}


@celery_app.task(
    name="worker.tasks.agent_tasks.get_agent_logs",
    bind=True,
)
def get_agent_logs(self, user_id: str, limit: int = 50) -> list:
    """Get recent agent logs from Redis."""
    import json

    list_key = f"jobpilot:agent:logs:history:{user_id}"
    logs = redis_client.lrange(list_key, 0, limit - 1)

    return [json.loads(log) for log in logs]
