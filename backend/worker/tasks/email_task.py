"""
Email tasks.

Handles sending cold emails with tracking and processing incoming responses.
"""

import asyncio
import logging
from typing import Dict, Any
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
    name="worker.tasks.email_task.send_cold_email_task",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    soft_time_limit=60,
    time_limit=120,
)
def send_cold_email_task(
    self,
    user_id: str,
    job_id: str,
    recipient_email: str,
    subject: str,
    body: str,
    cover_letter: str = "",
):
    """
    Send a cold email with open/click tracking.
    Stores the email record and schedules followups.
    """
    logger.info(f"Sending cold email for user {user_id} to {recipient_email}")
    session = _get_db_session()

    try:
        from sqlalchemy import text
        from worker.email.email_sender import EmailSender

        # Fetch user's email settings
        user_result = session.execute(text("""
            SELECT u.id, u.email, u.full_name,
                   up.sendgrid_api_key, up.from_email, up.from_name,
                   up.email_signature, up.resume_url
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            WHERE u.id = :user_id
        """), {"user_id": user_id})

        user = user_result.mappings().first()
        if not user:
            logger.error(f"User {user_id} not found")
            return {"status": "error", "reason": "user_not_found"}

        user = dict(user)

        # Create email record first
        result = session.execute(text("""
            INSERT INTO cold_emails (
                user_id, job_id, recipient_email,
                subject, body, cover_letter,
                status, created_at
            ) VALUES (
                :user_id, :job_id, :recipient_email,
                :subject, :body, :cover_letter,
                'sending', NOW()
            )
            RETURNING id
        """), {
            "user_id": user_id,
            "job_id": job_id,
            "recipient_email": recipient_email,
            "subject": subject,
            "body": body,
            "cover_letter": cover_letter,
        })
        email_id = result.scalar()
        session.commit()

        # Send the email with tracking
        sender = EmailSender(api_key=user.get("sendgrid_api_key"))
        send_result = asyncio.run(sender.send_tracked_email(
            email_id=str(email_id),
            from_email=user.get("from_email") or user["email"],
            from_name=user.get("from_name") or user["full_name"],
            to_email=recipient_email,
            subject=subject,
            body=body,
            signature=user.get("email_signature", ""),
            resume_url=user.get("resume_url"),
        ))

        if send_result["success"]:
            # Update email status
            session.execute(text("""
                UPDATE cold_emails
                SET status = 'sent',
                    sent_at = NOW(),
                    message_id = :message_id,
                    tracking_id = :tracking_id
                WHERE id = :email_id
            """), {
                "email_id": email_id,
                "message_id": send_result.get("message_id", ""),
                "tracking_id": send_result.get("tracking_id", ""),
            })

            # Schedule followup (3 days later)
            session.execute(text("""
                INSERT INTO email_followups (
                    email_id, user_id, job_id,
                    scheduled_at, followup_number, status
                ) VALUES (
                    :email_id, :user_id, :job_id,
                    NOW() + INTERVAL '3 days', 1, 'pending'
                )
            """), {
                "email_id": email_id,
                "user_id": user_id,
                "job_id": job_id,
            })

            session.commit()
            logger.info(f"Cold email {email_id} sent successfully to {recipient_email}")
        else:
            session.execute(text("""
                UPDATE cold_emails
                SET status = 'failed', error_message = :error
                WHERE id = :email_id
            """), {
                "email_id": email_id,
                "error": send_result.get("error", "Unknown error")[:500],
            })
            session.commit()
            logger.error(f"Failed to send cold email {email_id}: {send_result.get('error')}")

        return {
            "status": "sent" if send_result["success"] else "failed",
            "email_id": str(email_id),
            "recipient": recipient_email,
        }

    except Exception as exc:
        logger.error(f"Send cold email failed: {exc}", exc_info=True)
        session.rollback()
        raise self.retry(exc=exc)
    finally:
        session.close()


@celery_app.task(
    name="worker.tasks.email_task.process_email_response",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    soft_time_limit=60,
    time_limit=120,
)
def process_email_response(
    self,
    email_id: str,
    from_email: str,
    subject: str,
    body: str,
    received_at: str = None,
):
    """
    Process an incoming email response.
    Classifies the response and updates the application status.
    """
    logger.info(f"Processing email response for email {email_id} from {from_email}")
    session = _get_db_session()

    try:
        from sqlalchemy import text

        # Fetch original email context
        email_result = session.execute(text("""
            SELECT ce.*, j.title, j.company
            FROM cold_emails ce
            LEFT JOIN jobs j ON ce.job_id = j.id
            WHERE ce.id = :email_id
        """), {"email_id": email_id})

        original_email = email_result.mappings().first()
        if not original_email:
            logger.warning(f"Original email {email_id} not found")
            return {"status": "error", "reason": "email_not_found"}

        original_email = dict(original_email)

        # Classify the response using AI
        from worker.ai.response_classifier import ResponseClassifier
        classifier = ResponseClassifier()
        classification = asyncio.run(classifier.classify(
            original_subject=original_email["subject"],
            original_body=original_email["body"],
            response_subject=subject,
            response_body=body,
            company=original_email.get("company", ""),
            role=original_email.get("title", ""),
        ))

        # Store the response
        session.execute(text("""
            INSERT INTO email_responses (
                email_id, user_id, from_email,
                subject, body, classification,
                confidence, received_at
            ) VALUES (
                :email_id, :user_id, :from_email,
                :subject, :body, :classification,
                :confidence, :received_at
            )
        """), {
            "email_id": email_id,
            "user_id": original_email["user_id"],
            "from_email": from_email,
            "subject": subject,
            "body": body,
            "classification": classification["category"],
            "confidence": classification["confidence"],
            "received_at": received_at or datetime.now(timezone.utc).isoformat(),
        })

        # Update email status based on classification
        category = classification["category"]
        if category == "interested":
            new_status = "response_positive"
            # Cancel pending followups
            session.execute(text("""
                UPDATE email_followups
                SET status = 'cancelled'
                WHERE email_id = :email_id AND status = 'pending'
            """), {"email_id": email_id})
        elif category == "not_interested":
            new_status = "response_negative"
            session.execute(text("""
                UPDATE email_followups
                SET status = 'cancelled'
                WHERE email_id = :email_id AND status = 'pending'
            """), {"email_id": email_id})
        elif category == "question":
            new_status = "response_question"
            # Keep followups active
        else:
            new_status = "response_other"

        session.execute(text("""
            UPDATE cold_emails
            SET status = :status, responded_at = NOW()
            WHERE id = :email_id
        """), {"email_id": email_id, "status": new_status})

        # Update application status if positive
        if category == "interested":
            session.execute(text("""
                UPDATE applications
                SET status = 'response_received'
                WHERE user_id = :user_id AND job_id = :job_id
            """), {
                "user_id": original_email["user_id"],
                "job_id": original_email["job_id"],
            })

        session.commit()

        logger.info(
            f"Email response classified as '{category}' "
            f"(confidence: {classification['confidence']:.2f})"
        )

        return {
            "email_id": email_id,
            "classification": category,
            "confidence": classification["confidence"],
            "action_taken": new_status,
        }

    except Exception as exc:
        logger.error(f"Process email response failed: {exc}", exc_info=True)
        session.rollback()
        raise self.retry(exc=exc)
    finally:
        session.close()
