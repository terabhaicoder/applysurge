"""
Followup email task.

Checks for due followups and sends them using AI-generated content.
"""

import asyncio
import logging
from datetime import datetime, timezone

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
    name="worker.tasks.followup_task.send_scheduled_followups",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    soft_time_limit=300,
    time_limit=600,
)
def send_scheduled_followups(self):
    """
    Check for due followups and send them.
    Runs hourly via beat schedule.
    """
    logger.info("Checking for scheduled followups")
    session = _get_db_session()

    try:
        from sqlalchemy import text

        # Find due followups
        result = session.execute(text("""
            SELECT ef.id, ef.email_id, ef.user_id, ef.job_id,
                   ef.followup_number,
                   ce.recipient_email, ce.subject, ce.body,
                   j.title, j.company,
                   u.full_name, u.email as user_email,
                   up.sendgrid_api_key, up.from_email, up.from_name,
                   up.email_signature
            FROM email_followups ef
            INNER JOIN cold_emails ce ON ef.email_id = ce.id
            INNER JOIN jobs j ON ef.job_id = j.id
            INNER JOIN users u ON ef.user_id = u.id
            LEFT JOIN user_profiles up ON u.id = up.user_id
            WHERE ef.status = 'pending'
              AND ef.scheduled_at <= NOW()
              AND ce.status NOT IN ('response_positive', 'response_negative', 'bounced')
              AND ef.followup_number <= 3
            ORDER BY ef.scheduled_at ASC
            LIMIT 50
        """))

        followups = [dict(row) for row in result.mappings()]
        if not followups:
            logger.info("No followups due")
            return {"status": "no_followups"}

        logger.info(f"Found {len(followups)} followups to send")
        sent = 0
        failed = 0

        for followup in followups:
            try:
                # Generate followup content
                followup_content = asyncio.run(
                    _generate_followup(followup)
                )

                # Send the followup
                from worker.email.email_sender import EmailSender
                sender = EmailSender(api_key=followup.get("sendgrid_api_key"))

                send_result = asyncio.run(sender.send_tracked_email(
                    email_id=f"{followup['email_id']}_fu{followup['followup_number']}",
                    from_email=followup.get("from_email") or followup["user_email"],
                    from_name=followup.get("from_name") or followup["full_name"],
                    to_email=followup["recipient_email"],
                    subject=f"Re: {followup['subject']}",
                    body=followup_content["body"],
                    signature=followup.get("email_signature", ""),
                    is_followup=True,
                    original_message_id=followup.get("message_id"),
                ))

                if send_result["success"]:
                    # Update followup status
                    session.execute(text("""
                        UPDATE email_followups
                        SET status = 'sent', sent_at = NOW()
                        WHERE id = :id
                    """), {"id": followup["id"]})

                    # Schedule next followup if under limit
                    next_number = followup["followup_number"] + 1
                    if next_number <= 3:
                        # Increasing intervals: 3 days, 5 days, 7 days
                        interval_days = 2 * next_number + 1
                        session.execute(text("""
                            INSERT INTO email_followups (
                                email_id, user_id, job_id,
                                scheduled_at, followup_number, status
                            ) VALUES (
                                :email_id, :user_id, :job_id,
                                NOW() + INTERVAL ':days days',
                                :followup_number, 'pending'
                            )
                        """), {
                            "email_id": followup["email_id"],
                            "user_id": followup["user_id"],
                            "job_id": followup["job_id"],
                            "days": interval_days,
                            "followup_number": next_number,
                        })

                    sent += 1
                else:
                    session.execute(text("""
                        UPDATE email_followups
                        SET status = 'failed', error_message = :error
                        WHERE id = :id
                    """), {"id": followup["id"], "error": send_result.get("error", "")[:500]})
                    failed += 1

            except Exception as e:
                logger.error(f"Failed to send followup {followup['id']}: {e}")
                session.execute(text("""
                    UPDATE email_followups
                    SET status = 'failed', error_message = :error
                    WHERE id = :id
                """), {"id": followup["id"], "error": str(e)[:500]})
                failed += 1

        session.commit()
        logger.info(f"Followups: sent={sent}, failed={failed}")
        return {"sent": sent, "failed": failed, "total": len(followups)}

    except Exception as exc:
        logger.error(f"Send scheduled followups failed: {exc}", exc_info=True)
        session.rollback()
        raise self.retry(exc=exc)
    finally:
        session.close()


async def _generate_followup(followup: dict) -> dict:
    """Generate followup email content using AI."""
    from worker.ai.email_generator import EmailGenerator

    generator = EmailGenerator()
    content = await generator.generate_followup(
        original_subject=followup["subject"],
        original_body=followup["body"],
        company=followup["company"],
        role=followup["title"],
        followup_number=followup["followup_number"],
        sender_name=followup["full_name"],
    )
    return content
