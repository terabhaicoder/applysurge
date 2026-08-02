"""
Analytics task.

Aggregates daily statistics for all users including applications,
responses, interviews, and conversion rates.
"""

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
    name="worker.tasks.analytics_task.update_daily_stats",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    soft_time_limit=300,
    time_limit=600,
)
def update_daily_stats(self):
    """
    Aggregate daily statistics for all active users.
    Runs daily at 11:55 PM via beat schedule.
    """
    logger.info("Updating daily statistics")
    session = _get_db_session()

    try:
        from sqlalchemy import text

        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)

        # Get all active users
        users_result = session.execute(text("""
            SELECT id FROM users WHERE is_active = true
        """))
        user_ids = [row[0] for row in users_result]

        stats_created = 0
        for user_id in user_ids:
            try:
                # Count today's applications
                apps_result = session.execute(text("""
                    SELECT COUNT(*) FROM applications
                    WHERE user_id = :user_id
                      AND DATE(applied_at) = :today
                """), {"user_id": user_id, "today": today})
                applications_count = apps_result.scalar() or 0

                # Count jobs discovered today
                discovered_result = session.execute(text("""
                    SELECT COUNT(*) FROM jobs j
                    INNER JOIN job_matches jm ON j.id = jm.job_id
                    WHERE jm.user_id = :user_id
                      AND DATE(j.created_at) = :today
                """), {"user_id": user_id, "today": today})
                discovered_count = discovered_result.scalar() or 0

                # Count jobs matched today
                matched_result = session.execute(text("""
                    SELECT COUNT(*) FROM job_matches
                    WHERE user_id = :user_id
                      AND DATE(created_at) = :today
                      AND status IN ('matched', 'queued', 'applied')
                """), {"user_id": user_id, "today": today})
                matched_count = matched_result.scalar() or 0

                # Count emails sent today (table may not exist yet)
                emails_sent = 0
                try:
                    emails_result = session.execute(text("""
                        SELECT COUNT(*) FROM cold_emails
                        WHERE user_id = :user_id
                          AND DATE(sent_at) = :today
                    """), {"user_id": user_id, "today": today})
                    emails_sent = emails_result.scalar() or 0
                except Exception:
                    session.rollback()

                # Count responses received today (table may not exist yet)
                response_stats = {}
                try:
                    responses_result = session.execute(text("""
                        SELECT
                            COUNT(*) FILTER (WHERE classification = 'interested') as positive,
                            COUNT(*) as total
                        FROM email_responses
                        WHERE user_id = :user_id
                          AND DATE(received_at) = :today
                    """), {"user_id": user_id, "today": today})
                    row = responses_result.mappings().first()
                    response_stats = dict(row) if row else {}
                except Exception:
                    session.rollback()

                # Count email opens today (table may not exist yet)
                email_opens = 0
                try:
                    opens_result = session.execute(text("""
                        SELECT COUNT(DISTINCT email_id) FROM email_events
                        WHERE user_id = :user_id
                          AND event_type = 'open'
                          AND DATE(created_at) = :today
                    """), {"user_id": user_id, "today": today})
                    email_opens = opens_result.scalar() or 0
                except Exception:
                    session.rollback()

                # Calculate response rate
                response_rate = (
                    (response_stats.get("total", 0) / emails_sent * 100)
                    if emails_sent > 0 else 0
                )

                # Check if stats row exists for today
                existing = session.execute(text("""
                    SELECT id FROM daily_stats
                    WHERE user_id = :user_id AND stats_date = :stats_date
                    LIMIT 1
                """), {"user_id": user_id, "stats_date": today}).scalar()

                params = {
                    "user_id": user_id,
                    "stats_date": today,
                    "discovered": discovered_count,
                    "matched": matched_count,
                    "applications": applications_count,
                    "emails_sent": emails_sent,
                    "opens": email_opens,
                    "positive": response_stats.get("positive", 0),
                    "responses_received": response_stats.get("total", 0),
                    "resp_rate": round(response_rate, 2),
                }

                if existing:
                    session.execute(text("""
                        UPDATE daily_stats SET
                            jobs_discovered = :discovered,
                            jobs_matched = :matched,
                            applications_sent = :applications,
                            emails_sent = :emails_sent,
                            emails_opened = :opens,
                            positive_responses = :positive,
                            responses_received = :responses_received,
                            response_rate = :resp_rate,
                            updated_at = NOW()
                        WHERE user_id = :user_id AND stats_date = :stats_date
                    """), params)
                else:
                    session.execute(text("""
                        INSERT INTO daily_stats (
                            id, user_id, stats_date,
                            jobs_discovered, jobs_matched,
                            applications_sent, applications_failed,
                            emails_sent, emails_opened,
                            positive_responses, responses_received,
                            response_rate,
                            jobs_bookmarked, jobs_dismissed,
                            applications_pending, applications_reviewed,
                            applications_rejected, applications_interview,
                            applications_offered, applications_withdrawn,
                            emails_replied, follow_ups_sent,
                            agent_runs, agent_errors, agent_runtime_seconds,
                            created_at, updated_at
                        ) VALUES (
                            gen_random_uuid(), :user_id, :stats_date,
                            :discovered, :matched,
                            :applications, 0,
                            :emails_sent, :opens,
                            :positive, :responses_received,
                            :resp_rate,
                            0, 0,
                            0, 0,
                            0, 0,
                            0, 0,
                            0, 0,
                            0, 0, 0,
                            NOW(), NOW()
                        )
                    """), params)

                stats_created += 1

            except Exception as e:
                logger.error(f"Failed to update stats for user {user_id}: {e}")
                session.rollback()
                continue

        session.commit()
        logger.info(f"Updated daily stats for {stats_created}/{len(user_ids)} users")
        return {"users_processed": stats_created, "date": str(today)}

    except Exception as exc:
        logger.error(f"Update daily stats failed: {exc}", exc_info=True)
        session.rollback()
        raise self.retry(exc=exc)
    finally:
        session.close()
