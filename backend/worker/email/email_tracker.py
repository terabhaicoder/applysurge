"""
Email event tracking via webhooks.

Processes open and click events from tracking pixels and link redirects.
Updates email statistics and triggers appropriate actions.
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class EmailTracker:
    """
    Tracks email opens and clicks via webhook events.
    Records events in the database and updates email status.
    """

    def __init__(self):
        self._db_session = None

    def _get_db_session(self):
        """Create database session."""
        if self._db_session is None:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker

            database_url = os.environ.get(
                "DATABASE_URL",
                "postgresql://jobpilot:jobpilot_pass@postgres:5432/jobpilot_db"
            )
            database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
            engine = create_engine(database_url, pool_size=5)
            Session = sessionmaker(bind=engine)
            self._db_session = Session()
        return self._db_session

    async def track_open(
        self,
        email_id: str,
        tracking_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record an email open event.

        Args:
            email_id: Internal email ID
            tracking_id: Tracking UUID
            ip_address: Opener's IP address
            user_agent: Opener's user agent

        Returns:
            Dict with event status
        """
        logger.info(f"Email open tracked: email_id={email_id}, tracking_id={tracking_id}")
        session = self._get_db_session()

        try:
            from sqlalchemy import text

            # Record the open event
            session.execute(text("""
                INSERT INTO email_events (
                    email_id, tracking_id, event_type,
                    ip_address, user_agent, created_at
                ) VALUES (
                    :email_id, :tracking_id, 'open',
                    :ip_address, :user_agent, :now
                )
            """), {
                "email_id": email_id,
                "tracking_id": tracking_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "now": datetime.now(timezone.utc),
            })

            # Update email open count and first open time
            session.execute(text("""
                UPDATE cold_emails
                SET open_count = COALESCE(open_count, 0) + 1,
                    first_opened_at = COALESCE(first_opened_at, :now),
                    last_opened_at = :now
                WHERE id = :email_id
            """), {
                "email_id": email_id,
                "now": datetime.now(timezone.utc),
            })

            # Get user_id for the event
            email_result = session.execute(text("""
                SELECT user_id FROM cold_emails WHERE id = :email_id
            """), {"email_id": email_id})
            row = email_result.first()

            if row:
                # Record in email_events with user_id for analytics
                session.execute(text("""
                    UPDATE email_events
                    SET user_id = :user_id
                    WHERE email_id = :email_id
                      AND tracking_id = :tracking_id
                      AND event_type = 'open'
                      AND created_at = (
                          SELECT MAX(created_at) FROM email_events
                          WHERE email_id = :email_id AND event_type = 'open'
                      )
                """), {
                    "user_id": row[0],
                    "email_id": email_id,
                    "tracking_id": tracking_id,
                })

            session.commit()

            return {
                "status": "tracked",
                "event_type": "open",
                "email_id": email_id,
            }

        except Exception as e:
            logger.error(f"Failed to track email open: {e}")
            session.rollback()
            return {"status": "error", "error": str(e)}

    async def track_click(
        self,
        email_id: str,
        tracking_id: str,
        clicked_url: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record an email link click event.

        Args:
            email_id: Internal email ID
            tracking_id: Tracking UUID
            clicked_url: The original URL that was clicked
            ip_address: Clicker's IP address
            user_agent: Clicker's user agent

        Returns:
            Dict with event status and redirect URL
        """
        logger.info(f"Email click tracked: email_id={email_id}, url={clicked_url[:50]}")
        session = self._get_db_session()

        try:
            from sqlalchemy import text

            # Record the click event
            session.execute(text("""
                INSERT INTO email_events (
                    email_id, tracking_id, event_type,
                    url, ip_address, user_agent, created_at
                ) VALUES (
                    :email_id, :tracking_id, 'click',
                    :url, :ip_address, :user_agent, :now
                )
            """), {
                "email_id": email_id,
                "tracking_id": tracking_id,
                "url": clicked_url,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "now": datetime.now(timezone.utc),
            })

            # Update email click count
            session.execute(text("""
                UPDATE cold_emails
                SET click_count = COALESCE(click_count, 0) + 1,
                    last_clicked_at = :now
                WHERE id = :email_id
            """), {
                "email_id": email_id,
                "now": datetime.now(timezone.utc),
            })

            # Get user_id
            email_result = session.execute(text("""
                SELECT user_id FROM cold_emails WHERE id = :email_id
            """), {"email_id": email_id})
            row = email_result.first()
            if row:
                session.execute(text("""
                    UPDATE email_events
                    SET user_id = :user_id
                    WHERE email_id = :email_id
                      AND tracking_id = :tracking_id
                      AND event_type = 'click'
                      AND created_at = (
                          SELECT MAX(created_at) FROM email_events
                          WHERE email_id = :email_id AND event_type = 'click'
                      )
                """), {
                    "user_id": row[0],
                    "email_id": email_id,
                    "tracking_id": tracking_id,
                })

            session.commit()

            return {
                "status": "tracked",
                "event_type": "click",
                "email_id": email_id,
                "redirect_url": clicked_url,
            }

        except Exception as e:
            logger.error(f"Failed to track email click: {e}")
            session.rollback()
            return {
                "status": "error",
                "error": str(e),
                "redirect_url": clicked_url,
            }

    async def track_bounce(
        self,
        email_id: str,
        bounce_type: str = "hard",
        reason: str = "",
    ) -> Dict[str, Any]:
        """
        Record an email bounce event.

        Args:
            email_id: Internal email ID
            bounce_type: Type of bounce (hard/soft)
            reason: Bounce reason from provider

        Returns:
            Dict with event status
        """
        logger.info(f"Email bounce tracked: email_id={email_id}, type={bounce_type}")
        session = self._get_db_session()

        try:
            from sqlalchemy import text

            # Record bounce event
            session.execute(text("""
                INSERT INTO email_events (
                    email_id, event_type, metadata, created_at
                ) VALUES (
                    :email_id, 'bounce',
                    :metadata, :now
                )
            """), {
                "email_id": email_id,
                "metadata": f'{{"type": "{bounce_type}", "reason": "{reason}"}}',
                "now": datetime.now(timezone.utc),
            })

            # Update email status
            session.execute(text("""
                UPDATE cold_emails
                SET status = 'bounced', bounced_at = :now
                WHERE id = :email_id
            """), {
                "email_id": email_id,
                "now": datetime.now(timezone.utc),
            })

            # Cancel pending followups
            session.execute(text("""
                UPDATE email_followups
                SET status = 'cancelled'
                WHERE email_id = :email_id AND status = 'pending'
            """), {"email_id": email_id})

            session.commit()

            return {
                "status": "tracked",
                "event_type": "bounce",
                "bounce_type": bounce_type,
            }

        except Exception as e:
            logger.error(f"Failed to track bounce: {e}")
            session.rollback()
            return {"status": "error", "error": str(e)}

    async def process_sendgrid_webhook(
        self, events: list
    ) -> Dict[str, Any]:
        """
        Process SendGrid webhook events.

        Args:
            events: List of SendGrid event dictionaries

        Returns:
            Dict with processing results
        """
        processed = 0
        errors = 0

        for event in events:
            try:
                event_type = event.get("event", "")
                email_id = event.get("email_id", "")  # From custom args
                tracking_id = event.get("tracking_id", "")

                if not email_id:
                    continue

                if event_type == "open":
                    await self.track_open(
                        email_id=email_id,
                        tracking_id=tracking_id,
                        ip_address=event.get("ip", ""),
                        user_agent=event.get("useragent", ""),
                    )
                elif event_type == "click":
                    await self.track_click(
                        email_id=email_id,
                        tracking_id=tracking_id,
                        clicked_url=event.get("url", ""),
                        ip_address=event.get("ip", ""),
                        user_agent=event.get("useragent", ""),
                    )
                elif event_type in ("bounce", "dropped"):
                    await self.track_bounce(
                        email_id=email_id,
                        bounce_type="hard" if event_type == "bounce" else "soft",
                        reason=event.get("reason", ""),
                    )

                processed += 1

            except Exception as e:
                logger.error(f"Failed to process webhook event: {e}")
                errors += 1

        return {"processed": processed, "errors": errors, "total": len(events)}

    def get_email_stats(self, email_id: str) -> Dict[str, Any]:
        """Get tracking statistics for an email."""
        session = self._get_db_session()
        try:
            from sqlalchemy import text

            result = session.execute(text("""
                SELECT open_count, click_count,
                       first_opened_at, last_opened_at,
                       last_clicked_at, status
                FROM cold_emails
                WHERE id = :email_id
            """), {"email_id": email_id})

            row = result.mappings().first()
            if row:
                return dict(row)
            return {}

        except Exception as e:
            logger.error(f"Failed to get email stats: {e}")
            return {}

    def close(self):
        """Close database session."""
        if self._db_session:
            self._db_session.close()
            self._db_session = None
