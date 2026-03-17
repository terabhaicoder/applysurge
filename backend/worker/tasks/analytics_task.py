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
                    SELECT COUNT(*) FROM user_jobs
                    WHERE user_id = :user_id
                      AND DATE(discovered_at) = :today
                """), {"user_id": user_id, "today": today})
                discovered_count = discovered_result.scalar() or 0

                # Count jobs matched today
                matched_result = session.execute(text("""
                    SELECT COUNT(*) FROM user_jobs
                    WHERE user_id = :user_id
                      AND DATE(matched_at) = :today
                      AND status = 'matched'
                """), {"user_id": user_id, "today": today})
                matched_count = matched_result.scalar() or 0

                # Count emails sent today
                emails_result = session.execute(text("""
                    SELECT COUNT(*) FROM cold_emails
                    WHERE user_id = :user_id
                      AND DATE(sent_at) = :today
                """), {"user_id": user_id, "today": today})
                emails_sent = emails_result.scalar() or 0

                # Count responses received today
                responses_result = session.execute(text("""
                    SELECT
                        COUNT(*) FILTER (WHERE classification = 'interested') as positive,
                        COUNT(*) FILTER (WHERE classification = 'not_interested') as negative,
                        COUNT(*) FILTER (WHERE classification = 'question') as questions,
                        COUNT(*) as total
                    FROM email_responses
                    WHERE user_id = :user_id
                      AND DATE(received_at) = :today
                """), {"user_id": user_id, "today": today})
                response_stats = responses_result.mappings().first()
                response_stats = dict(response_stats) if response_stats else {}

                # Count email opens today
                opens_result = session.execute(text("""
                    SELECT COUNT(DISTINCT email_id) FROM email_events
                    WHERE user_id = :user_id
                      AND event_type = 'open'
                      AND DATE(created_at) = :today
                """), {"user_id": user_id, "today": today})
                email_opens = opens_result.scalar() or 0

                # Count email clicks today
                clicks_result = session.execute(text("""
                    SELECT COUNT(DISTINCT email_id) FROM email_events
                    WHERE user_id = :user_id
                      AND event_type = 'click'
                      AND DATE(created_at) = :today
                """), {"user_id": user_id, "today": today})
                email_clicks = clicks_result.scalar() or 0

                # Calculate conversion rates
                application_rate = (
                    (applications_count / matched_count * 100)
                    if matched_count > 0 else 0
                )
                response_rate = (
                    (response_stats.get("total", 0) / emails_sent * 100)
                    if emails_sent > 0 else 0
                )
                open_rate = (
                    (email_opens / emails_sent * 100)
                    if emails_sent > 0 else 0
                )

                # Upsert daily stats
                session.execute(text("""
                    INSERT INTO daily_stats (
                        user_id, date,
                        jobs_discovered, jobs_matched,
                        applications_sent, applications_failed,
                        emails_sent, emails_opened, emails_clicked,
                        responses_positive, responses_negative, responses_question,
                        application_rate, response_rate, open_rate,
                        created_at
                    ) VALUES (
                        :user_id, :date,
                        :discovered, :matched,
                        :applications, 0,
                        :emails_sent, :opens, :clicks,
                        :positive, :negative, :questions,
                        :app_rate, :resp_rate, :open_rate,
                        NOW()
                    )
                    ON CONFLICT (user_id, date) DO UPDATE SET
                        jobs_discovered = EXCLUDED.jobs_discovered,
                        jobs_matched = EXCLUDED.jobs_matched,
                        applications_sent = EXCLUDED.applications_sent,
                        emails_sent = EXCLUDED.emails_sent,
                        emails_opened = EXCLUDED.emails_opened,
                        emails_clicked = EXCLUDED.emails_clicked,
                        responses_positive = EXCLUDED.responses_positive,
                        responses_negative = EXCLUDED.responses_negative,
                        responses_question = EXCLUDED.responses_question,
                        application_rate = EXCLUDED.application_rate,
                        response_rate = EXCLUDED.response_rate,
                        open_rate = EXCLUDED.open_rate,
                        updated_at = NOW()
                """), {
                    "user_id": user_id,
                    "date": today,
                    "discovered": discovered_count,
                    "matched": matched_count,
                    "applications": applications_count,
                    "emails_sent": emails_sent,
                    "opens": email_opens,
                    "clicks": email_clicks,
                    "positive": response_stats.get("positive", 0),
                    "negative": response_stats.get("negative", 0),
                    "questions": response_stats.get("questions", 0),
                    "app_rate": round(application_rate, 2),
                    "resp_rate": round(response_rate, 2),
                    "open_rate": round(open_rate, 2),
                })

                stats_created += 1

            except Exception as e:
                logger.error(f"Failed to update stats for user {user_id}: {e}")
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
