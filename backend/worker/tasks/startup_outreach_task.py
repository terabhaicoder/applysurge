"""
Celery tasks for the startup outreach pipeline.

Tasks:
- discover_startups_task: Periodic task to find new startups
- scrape_startup_contacts_task: Find contacts for discovered startups
- send_startup_outreach_task: Send personalized emails to startup contacts
- process_startup_pipeline: Orchestrator that runs the full pipeline

Schedule:
- Discovery: runs daily at 6 AM UTC
- Outreach batch: runs twice daily at 9 AM and 2 PM UTC
"""

import asyncio
import logging
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from celery import chain, chord, group
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail,
    TrackingSettings,
    ClickTracking,
    OpenTracking,
)
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from worker.celery_app import celery_app
from worker.scrapers.startup_discovery import (
    DiscoveryFilters,
    StartupDiscoveryScraper,
    discover_startups,
)
from worker.scrapers.company_email_scraper import scrape_company_emails
from worker.scrapers.careers_page_scraper import scrape_careers_page
from worker.ai.startup_email_generator import (
    generate_startup_outreach_email,
    generate_role_interest_email,
)

logger = logging.getLogger(__name__)

# Database setup for worker context
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://jobpilot:jobpilot_pass@postgres:5432/jobpilot_db",
)
engine = create_async_engine(DATABASE_URL, pool_size=5, max_overflow=2)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# SendGrid setup
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.environ.get("SENDGRID_FROM_EMAIL", "outreach@jobpilot.ai")

# Rate limiting constants
MAX_OUTREACH_EMAILS_PER_DAY = 20
MAX_DISCOVERY_PER_RUN = 50


def run_async(coro):
    """Helper to run async code in sync Celery tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _get_user_data(session: AsyncSession, user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch user profile data for email generation."""
    from app.models.user import User

    result = await session.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        return None

    return {
        "full_name": user.full_name,
        "email": user.email,
    }


async def _get_user_outreach_settings(session: AsyncSession, user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch user's startup outreach settings."""
    from app.models.startup_contact import StartupOutreachSettings

    result = await session.execute(
        select(StartupOutreachSettings).where(
            StartupOutreachSettings.user_id == uuid.UUID(user_id)
        )
    )
    settings = result.scalar_one_or_none()
    if not settings:
        return None

    return {
        "target_industries": settings.target_industries,
        "target_company_sizes": settings.target_company_sizes,
        "target_funding_stages": settings.target_funding_stages,
        "target_locations": settings.target_locations,
        "target_tech_stacks": settings.target_tech_stacks,
        "keywords": settings.keywords,
        "excluded_companies": settings.excluded_companies,
        "max_emails_per_day": settings.max_emails_per_day,
        "outreach_enabled": settings.outreach_enabled,
        "auto_send": settings.auto_send,
        "email_tone": settings.email_tone,
        "include_portfolio_link": settings.include_portfolio_link,
        "portfolio_url": settings.portfolio_url,
        "use_yc_directory": settings.use_yc_directory,
        "use_product_hunt": settings.use_product_hunt,
        "use_linkedin": settings.use_linkedin,
        "use_angellist": settings.use_angellist,
        "preferred_contact_titles": settings.preferred_contact_titles,
    }


async def _get_emails_sent_today(session: AsyncSession, user_id: str) -> int:
    """Count outreach emails sent today for rate limiting."""
    from app.models.startup_contact import StartupContact

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    result = await session.execute(
        select(func.count(StartupContact.id)).where(
            and_(
                StartupContact.user_id == uuid.UUID(user_id),
                StartupContact.email_sent_at >= today_start,
                StartupContact.outreach_status == "contacted",
            )
        )
    )
    return result.scalar() or 0


async def _save_startup_contact(
    session: AsyncSession,
    user_id: str,
    startup_data: Dict[str, Any],
    contact_data: Optional[Dict[str, Any]] = None,
    careers_data: Optional[Dict[str, Any]] = None,
) -> str:
    """Save or update a startup contact record."""
    from app.models.startup_contact import StartupContact

    # Check if already exists
    result = await session.execute(
        select(StartupContact).where(
            and_(
                StartupContact.user_id == uuid.UUID(user_id),
                StartupContact.company_name == startup_data.get("company_name", ""),
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing record
        if contact_data and contact_data.get("best_contact"):
            best = contact_data["best_contact"]
            existing.contact_name = best.get("name")
            existing.contact_title = best.get("title")
            existing.contact_email = best.get("email")
            existing.contact_linkedin = best.get("linkedin_url")
            existing.contact_source = best.get("source")
            existing.contact_confidence_score = best.get("confidence_score", 0.0)

        if careers_data:
            existing.careers_page_url = careers_data.get("careers_page_url")
            existing.open_roles = careers_data.get("open_roles")
            existing.matched_roles = careers_data.get("matched_roles")
            existing.application_instructions = careers_data.get("application_instructions")

        await session.commit()
        return str(existing.id)
    else:
        # Create new record
        contact = StartupContact(
            user_id=uuid.UUID(user_id),
            company_name=startup_data.get("company_name", ""),
            company_website=startup_data.get("company_website"),
            company_industry=startup_data.get("company_industry"),
            company_size=startup_data.get("company_size"),
            company_description=startup_data.get("company_description"),
            company_location=startup_data.get("company_location"),
            company_tech_stack=startup_data.get("company_tech_stack"),
            funding_stage=startup_data.get("funding_stage"),
            funding_amount=startup_data.get("funding_amount"),
            discovery_source=startup_data.get("discovery_source"),
            discovery_url=startup_data.get("discovery_url"),
            outreach_status="discovered",
            tags=startup_data.get("tags"),
        )

        if contact_data and contact_data.get("best_contact"):
            best = contact_data["best_contact"]
            contact.contact_name = best.get("name")
            contact.contact_title = best.get("title")
            contact.contact_email = best.get("email")
            contact.contact_linkedin = best.get("linkedin_url")
            contact.contact_source = best.get("source")
            contact.contact_confidence_score = best.get("confidence_score", 0.0)

        if careers_data:
            contact.careers_page_url = careers_data.get("careers_page_url")
            contact.open_roles = careers_data.get("open_roles")
            contact.matched_roles = careers_data.get("matched_roles")
            contact.application_instructions = careers_data.get("application_instructions")

        session.add(contact)
        await session.commit()
        await session.refresh(contact)
        return str(contact.id)


async def _send_email_via_sendgrid(
    to_email: str,
    from_email: str,
    subject: str,
    body: str,
    reply_to: Optional[str] = None,
) -> Optional[str]:
    """
    Send an email via SendGrid with open/click tracking.
    Returns the message ID if successful.
    """
    if not SENDGRID_API_KEY:
        logger.error("SendGrid API key not configured")
        return None

    try:
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            plain_text_content=body,
        )

        # Enable tracking
        tracking_settings = TrackingSettings()
        tracking_settings.click_tracking = ClickTracking(enable=True, enable_text=False)
        tracking_settings.open_tracking = OpenTracking(enable=True)
        message.tracking_settings = tracking_settings

        if reply_to:
            message.reply_to = reply_to

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code in (200, 201, 202):
            message_id = response.headers.get("X-Message-Id", "")
            logger.info(f"Email sent successfully to {to_email}, message_id: {message_id}")
            return message_id
        else:
            logger.error(f"SendGrid error: status={response.status_code}, body={response.body}")
            return None

    except Exception as e:
        logger.error(f"Error sending email via SendGrid: {e}")
        return None


@celery_app.task(
    name="worker.tasks.startup_outreach_task.discover_startups_task",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    soft_time_limit=600,
    time_limit=900,
)
def discover_startups_task(self, user_id: str, sources: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Periodic task to discover new startups matching user preferences.

    Scrapes configured sources and saves discovered startups to the database.
    Runs daily via Celery beat.

    Args:
        user_id: UUID of the user.
        sources: Optional list of sources to search.

    Returns:
        Dictionary with discovery results.
    """
    logger.info(f"Starting startup discovery for user {user_id}")

    try:
        result = run_async(_discover_startups_async(user_id, sources))
        return result
    except Exception as e:
        logger.error(f"Startup discovery failed for user {user_id}: {e}")
        self.retry(exc=e)


async def _discover_startups_async(user_id: str, sources: Optional[List[str]] = None) -> Dict[str, Any]:
    """Async implementation of startup discovery."""
    async with async_session_factory() as session:
        # Get user settings
        settings = await _get_user_outreach_settings(session, user_id)
        if not settings:
            logger.info(f"No outreach settings found for user {user_id}, using defaults")
            settings = {}

        if not settings.get("outreach_enabled", True):
            return {"status": "disabled", "discovered": 0}

        # Build discovery filters from settings
        filters = DiscoveryFilters(
            industries=settings.get("target_industries"),
            locations=settings.get("target_locations"),
            company_sizes=settings.get("target_company_sizes"),
            funding_stages=settings.get("target_funding_stages"),
            tech_stacks=settings.get("target_tech_stacks"),
            keywords=settings.get("keywords"),
            excluded_companies=settings.get("excluded_companies"),
            max_results=MAX_DISCOVERY_PER_RUN,
        )

        # Determine sources to use
        if not sources:
            sources = []
            if settings.get("use_yc_directory", True):
                sources.append("yc")
            if settings.get("use_product_hunt", True):
                sources.append("product_hunt")
            if settings.get("use_linkedin", False):
                sources.append("linkedin")
            if settings.get("use_angellist", True):
                sources.append("angellist")

        if not sources:
            sources = ["yc", "product_hunt", "angellist"]

        # Run discovery
        startups = await discover_startups(filters=filters, sources=sources)

        # Save to database
        saved_count = 0
        for startup_data in startups:
            try:
                await _save_startup_contact(session, user_id, startup_data)
                saved_count += 1
            except Exception as save_err:
                logger.error(f"Error saving startup {startup_data.get('company_name')}: {save_err}")
                continue

        logger.info(f"Discovery complete for user {user_id}: {saved_count} startups saved")
        return {
            "status": "success",
            "discovered": len(startups),
            "saved": saved_count,
            "sources": sources,
        }


@celery_app.task(
    name="worker.tasks.startup_outreach_task.scrape_startup_contacts_task",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    soft_time_limit=300,
    time_limit=600,
)
def scrape_startup_contacts_task(self, user_id: str, contact_id: str) -> Dict[str, Any]:
    """
    Find contacts and careers info for a discovered startup.

    Scrapes the company website for:
    1. Contact emails (team pages, Hunter.io, LinkedIn)
    2. Careers page and open roles

    Args:
        user_id: UUID of the user.
        contact_id: UUID of the startup_contact record.

    Returns:
        Dictionary with scraping results.
    """
    logger.info(f"Scraping contacts for startup {contact_id} (user: {user_id})")

    try:
        result = run_async(_scrape_contacts_async(user_id, contact_id))
        return result
    except Exception as e:
        logger.error(f"Contact scraping failed for {contact_id}: {e}")
        self.retry(exc=e)


async def _scrape_contacts_async(user_id: str, contact_id: str) -> Dict[str, Any]:
    """Async implementation of contact scraping."""
    from app.models.startup_contact import StartupContact

    async with async_session_factory() as session:
        # Get the startup contact record
        result = await session.execute(
            select(StartupContact).where(
                and_(
                    StartupContact.id == uuid.UUID(contact_id),
                    StartupContact.user_id == uuid.UUID(user_id),
                )
            )
        )
        contact = result.scalar_one_or_none()
        if not contact:
            return {"status": "error", "message": "Startup contact not found"}

        if not contact.company_website:
            return {"status": "error", "message": "No company website available"}

        company_name = contact.company_name
        company_website = contact.company_website

        # Scrape for emails
        email_result = await scrape_company_emails(
            company_name=company_name,
            company_website=company_website,
            search_linkedin=True,
            use_hunter=True,
        )

        # Scrape careers page
        careers_result = await scrape_careers_page(
            company_name=company_name,
            company_website=company_website,
        )

        # Update the record
        if email_result.get("best_contact"):
            best = email_result["best_contact"]
            contact.contact_name = best.get("name")
            contact.contact_title = best.get("title")
            contact.contact_email = best.get("email")
            contact.contact_linkedin = best.get("linkedin_url")
            contact.contact_source = best.get("source")
            contact.contact_confidence_score = best.get("confidence_score", 0.0)

        if careers_result.get("careers_page_found"):
            contact.careers_page_url = careers_result.get("careers_page_url")
            contact.open_roles = careers_result.get("open_roles")
            contact.matched_roles = careers_result.get("matched_roles")
            contact.application_instructions = careers_result.get("application_instructions")

        await session.commit()

        return {
            "status": "success",
            "contact_id": contact_id,
            "has_email": bool(contact.contact_email),
            "has_careers_page": bool(contact.careers_page_url),
            "open_roles_count": len(contact.open_roles) if contact.open_roles else 0,
            "matched_roles_count": len(contact.matched_roles) if contact.matched_roles else 0,
        }


@celery_app.task(
    name="worker.tasks.startup_outreach_task.send_startup_outreach_task",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    soft_time_limit=120,
    time_limit=180,
)
def send_startup_outreach_task(
    self,
    user_id: str,
    contact_id: str,
    email_type: str = "startup_outreach",
    custom_message: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send a personalized outreach email to a startup contact.

    Generates the email using AI, then sends via SendGrid with tracking.

    Args:
        user_id: UUID of the user.
        contact_id: UUID of the startup_contact record.
        email_type: Type of email (startup_outreach or role_interest).
        custom_message: Optional custom instructions for email generation.

    Returns:
        Dictionary with send results.
    """
    logger.info(f"Sending outreach to {contact_id} for user {user_id}")

    try:
        result = run_async(_send_outreach_async(user_id, contact_id, email_type, custom_message))
        return result
    except Exception as e:
        logger.error(f"Outreach send failed for {contact_id}: {e}")
        self.retry(exc=e)


async def _send_outreach_async(
    user_id: str,
    contact_id: str,
    email_type: str,
    custom_message: Optional[str],
) -> Dict[str, Any]:
    """Async implementation of outreach email sending."""
    from app.models.startup_contact import StartupContact

    async with async_session_factory() as session:
        # Rate limiting check
        emails_today = await _get_emails_sent_today(session, user_id)
        settings = await _get_user_outreach_settings(session, user_id)
        max_per_day = settings.get("max_emails_per_day", MAX_OUTREACH_EMAILS_PER_DAY) if settings else MAX_OUTREACH_EMAILS_PER_DAY

        if emails_today >= max_per_day:
            return {
                "status": "rate_limited",
                "message": f"Daily limit reached ({max_per_day} emails/day)",
                "emails_sent_today": emails_today,
            }

        # Get the startup contact
        result = await session.execute(
            select(StartupContact).where(
                and_(
                    StartupContact.id == uuid.UUID(contact_id),
                    StartupContact.user_id == uuid.UUID(user_id),
                )
            )
        )
        contact = result.scalar_one_or_none()
        if not contact:
            return {"status": "error", "message": "Startup contact not found"}

        if not contact.contact_email:
            return {"status": "error", "message": "No contact email available"}

        if contact.outreach_status == "contacted":
            return {"status": "error", "message": "Already contacted this startup"}

        # Get user data for email generation
        user_data = await _get_user_data(session, user_id)
        if not user_data:
            return {"status": "error", "message": "User not found"}

        # Add portfolio URL from settings if available
        if settings and settings.get("include_portfolio_link") and settings.get("portfolio_url"):
            user_data["portfolio_url"] = settings["portfolio_url"]

        # Build company data
        company_data = {
            "company_name": contact.company_name,
            "company_website": contact.company_website,
            "company_industry": contact.company_industry,
            "company_description": contact.company_description,
            "company_size": contact.company_size,
            "company_location": contact.company_location,
            "company_tech_stack": contact.company_tech_stack,
            "funding_stage": contact.funding_stage,
            "funding_amount": contact.funding_amount,
            "discovery_source": contact.discovery_source,
        }

        # Generate email
        tone = settings.get("email_tone", "professional") if settings else "professional"

        if email_type == "role_interest" and contact.matched_roles:
            # Use the best matched role
            best_role = contact.matched_roles[0]
            email_result = await generate_role_interest_email(
                company_data=company_data,
                user_data=user_data,
                role_data=best_role,
                contact_name=contact.contact_name,
                contact_title=contact.contact_title,
                tone=tone,
                custom_instructions=custom_message,
            )
        else:
            email_result = await generate_startup_outreach_email(
                company_data=company_data,
                user_data=user_data,
                contact_name=contact.contact_name,
                contact_title=contact.contact_title,
                tone=tone,
                custom_instructions=custom_message,
            )

        subject = email_result.get("subject", "")
        body = email_result.get("body", "")

        if not subject or not body:
            return {"status": "error", "message": "Failed to generate email"}

        # Send via SendGrid
        from_email = user_data.get("email", SENDGRID_FROM_EMAIL)
        message_id = await _send_email_via_sendgrid(
            to_email=contact.contact_email,
            from_email=from_email,
            subject=subject,
            body=body,
            reply_to=from_email,
        )

        if message_id:
            # Update contact record
            contact.outreach_status = "contacted"
            contact.email_subject = subject
            contact.email_body = body
            contact.email_sent_at = datetime.now(timezone.utc)
            contact.sendgrid_message_id = message_id
            contact.next_followup_at = datetime.now(timezone.utc) + timedelta(days=5)
            await session.commit()

            return {
                "status": "success",
                "contact_id": contact_id,
                "message_id": message_id,
                "subject": subject,
                "email_type": email_type,
                "sent_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            return {
                "status": "error",
                "message": "Failed to send email via SendGrid",
                "subject": subject,
            }


@celery_app.task(
    name="worker.tasks.startup_outreach_task.process_startup_pipeline",
    bind=True,
    max_retries=1,
    soft_time_limit=1800,
    time_limit=2400,
)
def process_startup_pipeline(self, user_id: str) -> Dict[str, Any]:
    """
    Orchestrator task that runs the full startup outreach pipeline:
    1. Discover startups matching user preferences
    2. Scrape their websites for contacts and open roles
    3. Generate personalized emails
    4. Send emails with proper rate limiting
    5. Track everything in the database

    This is the main entry point for the automated pipeline.

    Args:
        user_id: UUID of the user.

    Returns:
        Dictionary with pipeline results.
    """
    logger.info(f"Starting startup outreach pipeline for user {user_id}")

    try:
        result = run_async(_process_pipeline_async(user_id))
        return result
    except Exception as e:
        logger.error(f"Pipeline failed for user {user_id}: {e}")
        self.retry(exc=e)


async def _process_pipeline_async(user_id: str) -> Dict[str, Any]:
    """Async implementation of the full pipeline."""
    from app.models.startup_contact import StartupContact

    pipeline_result = {
        "user_id": user_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "discovery": None,
        "contacts_scraped": 0,
        "emails_generated": 0,
        "emails_sent": 0,
        "errors": [],
    }

    async with async_session_factory() as session:
        # Check if outreach is enabled
        settings = await _get_user_outreach_settings(session, user_id)
        if settings and not settings.get("outreach_enabled", True):
            pipeline_result["status"] = "disabled"
            return pipeline_result

    # Step 1: Discover new startups
    try:
        discovery_result = await _discover_startups_async(user_id, sources=None)
        pipeline_result["discovery"] = discovery_result
    except Exception as e:
        error = f"Discovery failed: {e}"
        logger.error(error)
        pipeline_result["errors"].append(error)

    # Step 2: Scrape contacts for startups without contact info
    async with async_session_factory() as session:
        result = await session.execute(
            select(StartupContact).where(
                and_(
                    StartupContact.user_id == uuid.UUID(user_id),
                    StartupContact.outreach_status == "discovered",
                    StartupContact.contact_email.is_(None),
                    StartupContact.company_website.isnot(None),
                )
            ).limit(10)  # Process 10 at a time
        )
        contacts_to_scrape = result.scalars().all()

    for contact in contacts_to_scrape:
        try:
            scrape_result = await _scrape_contacts_async(user_id, str(contact.id))
            if scrape_result.get("status") == "success":
                pipeline_result["contacts_scraped"] += 1
            # Add delay between scrapes
            await asyncio.sleep(random.uniform(5, 15))
        except Exception as e:
            logger.error(f"Scraping failed for {contact.company_name}: {e}")
            pipeline_result["errors"].append(f"Scrape error: {contact.company_name}")
            continue

    # Step 3: Send outreach to contacts with emails
    async with async_session_factory() as session:
        emails_today = await _get_emails_sent_today(session, user_id)
        max_per_day = MAX_OUTREACH_EMAILS_PER_DAY
        if settings:
            max_per_day = settings.get("max_emails_per_day", MAX_OUTREACH_EMAILS_PER_DAY)
            auto_send = settings.get("auto_send", False)
        else:
            auto_send = False

        remaining = max_per_day - emails_today

        if remaining <= 0:
            pipeline_result["rate_limited"] = True
            pipeline_result["status"] = "rate_limited"
            return pipeline_result

        if not auto_send:
            pipeline_result["status"] = "discovery_only"
            pipeline_result["message"] = "Auto-send is disabled. Emails generated but not sent."
            return pipeline_result

        # Get contacts ready for outreach
        result = await session.execute(
            select(StartupContact).where(
                and_(
                    StartupContact.user_id == uuid.UUID(user_id),
                    StartupContact.outreach_status == "discovered",
                    StartupContact.contact_email.isnot(None),
                    StartupContact.contact_confidence_score >= 0.4,
                )
            ).order_by(StartupContact.contact_confidence_score.desc()).limit(remaining)
        )
        contacts_to_email = result.scalars().all()

    for contact in contacts_to_email:
        try:
            # Determine email type
            email_type = "startup_outreach"
            if contact.matched_roles and len(contact.matched_roles) > 0:
                email_type = "role_interest"

            send_result = await _send_outreach_async(
                user_id=user_id,
                contact_id=str(contact.id),
                email_type=email_type,
                custom_message=None,
            )

            if send_result.get("status") == "success":
                pipeline_result["emails_sent"] += 1
            elif send_result.get("status") == "rate_limited":
                break

            # Random delay between sends (30-90 seconds)
            await asyncio.sleep(random.uniform(30, 90))

        except Exception as e:
            logger.error(f"Send failed for {contact.company_name}: {e}")
            pipeline_result["errors"].append(f"Send error: {contact.company_name}")
            continue

    pipeline_result["completed_at"] = datetime.now(timezone.utc).isoformat()
    pipeline_result["status"] = "success"
    logger.info(
        f"Pipeline complete for user {user_id}: "
        f"discovered={pipeline_result['discovery']}, "
        f"scraped={pipeline_result['contacts_scraped']}, "
        f"sent={pipeline_result['emails_sent']}"
    )
    return pipeline_result


@celery_app.task(
    name="worker.tasks.startup_outreach_task.process_all_users_pipeline",
    soft_time_limit=3600,
    time_limit=4200,
)
def process_all_users_pipeline() -> Dict[str, Any]:
    """
    Periodic task to run the startup outreach pipeline for all users
    who have outreach enabled.

    Scheduled via Celery beat.
    """
    logger.info("Starting startup outreach pipeline for all users")

    result = run_async(_process_all_users_async())
    return result


async def _process_all_users_async() -> Dict[str, Any]:
    """Process pipeline for all users with outreach enabled."""
    from app.models.startup_contact import StartupOutreachSettings

    async with async_session_factory() as session:
        result = await session.execute(
            select(StartupOutreachSettings.user_id).where(
                StartupOutreachSettings.outreach_enabled == True
            )
        )
        user_ids = [str(row[0]) for row in result.all()]

    results = {
        "total_users": len(user_ids),
        "processed": 0,
        "errors": 0,
    }

    for user_id in user_ids:
        try:
            # Dispatch individual pipeline tasks
            process_startup_pipeline.delay(user_id)
            results["processed"] += 1
        except Exception as e:
            logger.error(f"Failed to dispatch pipeline for user {user_id}: {e}")
            results["errors"] += 1

    return results
