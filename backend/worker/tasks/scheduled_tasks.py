"""
Scheduled maintenance tasks.

Handles daily limit resets and summary email notifications.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_db_session():
    """Create a synchronous database session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os

    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://jobpilot:jobpilot_pass@postgres:5432/jobpilot_db"
    )
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(database_url, pool_size=5, max_overflow=10)
    Session = sessionmaker(bind=engine)
    return Session()


@celery_app.task(
    name="worker.tasks.scheduled_tasks.reset_daily_limits",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    soft_time_limit=60,
    time_limit=120,
)
def reset_daily_limits(self):
    """
    Reset all users' daily application counters.
    Runs daily at midnight via beat schedule.
    """
    logger.info("Resetting daily application limits")
    session = _get_db_session()

    try:
        from sqlalchemy import text

        # Reset daily application counters in agent_settings
        result = session.execute(text("""
            UPDATE agent_settings
            SET consecutive_errors = 0,
                last_error = NULL
            WHERE user_id IN (SELECT id FROM users WHERE is_active = true)
        """))

        affected = result.rowcount
        session.commit()

        logger.info(f"Reset daily limits for {affected} users")
        return {"users_reset": affected}

    except Exception as exc:
        logger.error(f"Reset daily limits failed: {exc}", exc_info=True)
        session.rollback()
        raise self.retry(exc=exc)
    finally:
        session.close()


@celery_app.task(
    name="worker.tasks.scheduled_tasks.send_daily_summaries",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    soft_time_limit=600,
    time_limit=900,
)
def send_daily_summaries(self):
    """
    Send daily summary emails to all active users.
    Runs daily at 8 PM via beat schedule.
    """
    logger.info("Sending daily summary emails")
    session = _get_db_session()

    try:
        from sqlalchemy import text

        today = datetime.now(timezone.utc).date()

        # Get users who want daily summaries
        users_result = session.execute(text("""
            SELECT u.id, u.email, u.full_name
            FROM users u
            WHERE u.is_active = true
        """))

        users = [dict(row) for row in users_result.mappings()]
        if not users:
            return {"status": "no_users"}

        sent = 0
        failed = 0

        for user in users:
            try:
                # Fetch today's stats
                stats_result = session.execute(text("""
                    SELECT * FROM daily_stats
                    WHERE user_id = :user_id AND date = :today
                """), {"user_id": user["id"], "today": today})

                stats = stats_result.mappings().first()
                if not stats:
                    # Build stats from scratch if not yet aggregated
                    stats = _build_user_daily_stats(session, user["id"], today)

                stats = dict(stats) if stats else {}

                # Fetch pending queue items from job_matches
                try:
                    queue_result = session.execute(text("""
                        SELECT COUNT(*) FROM job_matches
                        WHERE user_id = :user_id AND status = 'queued'
                    """), {"user_id": user["id"]})
                    pending_count = queue_result.scalar() or 0
                except Exception:
                    pending_count = 0

                # Fetch notable responses (table may not exist yet)
                positive_responses = []
                try:
                    responses_result = session.execute(text("""
                        SELECT er.classification, er.from_email,
                               j.title, j.company
                        FROM email_responses er
                        INNER JOIN cold_emails ce ON er.email_id = ce.id
                        LEFT JOIN jobs j ON ce.job_id = j.id
                        WHERE er.user_id = :user_id
                          AND DATE(er.received_at) = :today
                          AND er.classification = 'interested'
                        LIMIT 5
                    """), {"user_id": user["id"], "today": today})
                    positive_responses = [dict(r) for r in responses_result.mappings()]
                except Exception:
                    pass

                # Generate and send summary email
                asyncio.run(_send_summary_email(user, stats, pending_count, positive_responses))
                sent += 1

            except Exception as e:
                logger.error(f"Failed to send summary to user {user['id']}: {e}")
                failed += 1

        logger.info(f"Daily summaries: sent={sent}, failed={failed}")
        return {"sent": sent, "failed": failed, "total": len(users)}

    except Exception as exc:
        logger.error(f"Send daily summaries failed: {exc}", exc_info=True)
        session.rollback()
        raise self.retry(exc=exc)
    finally:
        session.close()


def _build_user_daily_stats(session, user_id: str, date) -> dict:
    """Build daily stats on the fly if not yet aggregated."""
    from sqlalchemy import text

    apps = session.execute(text("""
        SELECT COUNT(*) FROM applications
        WHERE user_id = :user_id AND DATE(applied_at) = :date
    """), {"user_id": user_id, "date": date}).scalar() or 0

    # Use jobs + job_matches tables (user_jobs doesn't exist)
    discovered = 0
    matched = 0
    try:
        discovered = session.execute(text("""
            SELECT COUNT(*) FROM jobs j
            INNER JOIN job_matches jm ON j.id = jm.job_id
            WHERE jm.user_id = :user_id AND DATE(j.created_at) = :date
        """), {"user_id": user_id, "date": date}).scalar() or 0

        matched = session.execute(text("""
            SELECT COUNT(*) FROM job_matches
            WHERE user_id = :user_id AND DATE(created_at) = :date
              AND status IN ('matched', 'queued', 'applied')
        """), {"user_id": user_id, "date": date}).scalar() or 0
    except Exception:
        pass

    emails = 0
    try:
        emails = session.execute(text("""
            SELECT COUNT(*) FROM cold_emails
            WHERE user_id = :user_id AND DATE(sent_at) = :date
        """), {"user_id": user_id, "date": date}).scalar() or 0
    except Exception:
        pass

    return {
        "jobs_discovered": discovered,
        "jobs_matched": matched,
        "applications_sent": apps,
        "emails_sent": emails,
        "responses_positive": 0,
        "responses_negative": 0,
        "emails_opened": 0,
    }


async def _send_summary_email(
    user: dict, stats: dict, pending_count: int, positive_responses: list
):
    """Generate and send the daily summary email."""
    from worker.email.email_sender import EmailSender
    import os

    # Build summary HTML
    subject = f"JobPilot Daily Summary - {datetime.now(timezone.utc).strftime('%B %d, %Y')}"

    body = f"""Hi {user['full_name']},

Here's your daily job search summary:

ACTIVITY
- Jobs Discovered: {stats.get('jobs_discovered', 0)}
- Jobs Matched: {stats.get('jobs_matched', 0)}
- Applications Sent: {stats.get('applications_sent', 0)}
- Emails Sent: {stats.get('emails_sent', 0)}
- Emails Opened: {stats.get('emails_opened', 0)}

RESPONSES
- Positive: {stats.get('responses_positive', 0)}
- Negative: {stats.get('responses_negative', 0)}

QUEUE
- Pending Applications: {pending_count}
"""

    if positive_responses:
        body += "\nPOSITIVE RESPONSES TODAY:\n"
        for resp in positive_responses:
            body += f"  - {resp.get('company', 'Unknown')} ({resp.get('title', 'Unknown role')})\n"

    body += """
Keep up the momentum! Your AI agent is working around the clock to find your next opportunity.

Best,
The JobPilot Team
"""

    # Send via SendGrid or SMTP
    api_key = os.environ.get("SENDGRID_API_KEY", "")
    sender = EmailSender(api_key=api_key)
    await sender.send_email(
        from_email=os.environ.get("SMTP_FROM_EMAIL", "noreply@jobpilot.ai"),
        from_name="JobPilot",
        to_email=user["email"],
        subject=subject,
        body=body,
        is_html=False,
    )
