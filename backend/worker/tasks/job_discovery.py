"""
Job discovery tasks.

Discovers new jobs for users by scraping LinkedIn and Naukri
based on their preferences and search criteria.
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from worker.celery_app import celery_app
from worker.scrapers.linkedin_scraper import LinkedInScraper
from worker.scrapers.naukri_scraper import NaukriScraper
from worker.tasks.job_matching import match_jobs_for_user

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


def _get_active_users(session) -> List[Dict[str, Any]]:
    """Fetch all active users who have the agent enabled."""
    from sqlalchemy import text

    result = session.execute(text("""
        SELECT u.id, u.email, u.full_name
        FROM users u
        INNER JOIN agent_settings ag ON u.id = ag.user_id
        WHERE u.is_active = true
          AND ag.is_enabled = true
    """))

    users = []
    for row in result.mappings():
        users.append(dict(row))
    return users


def _get_user_credentials(user_id: str, platform: str, session) -> Dict[str, str]:
    """Fetch decrypted credentials from platform_credentials table."""
    from sqlalchemy import text
    from app.core.encryption import decrypt_value

    result = session.execute(text("""
        SELECT platform_email, platform_username, encrypted_password
        FROM platform_credentials
        WHERE user_id = :user_id AND platform = :platform AND is_active = true
    """), {"user_id": user_id, "platform": platform})

    row = result.mappings().first()
    if not row:
        return {}

    encrypted_password = row["encrypted_password"]
    if not encrypted_password:
        return {}

    password = decrypt_value(encrypted_password)
    if not password:
        return {}

    return {
        "email": row["platform_email"] or row["platform_username"],
        "password": password,
    }


def _get_user_preferences(user_id: str, session) -> Dict[str, Any]:
    """Fetch job preferences from job_preferences table."""
    from sqlalchemy import text

    result = session.execute(text("""
        SELECT desired_titles, preferred_locations, job_types,
               remote_only, hybrid_ok, min_salary, max_salary,
               experience_levels, min_match_score
        FROM job_preferences
        WHERE user_id = :user_id
    """), {"user_id": user_id})

    row = result.mappings().first()
    if row:
        return dict(row)

    return {
        "desired_titles": [],
        "preferred_locations": [],
        "job_types": ["full-time"],
        "remote_only": False,
        "hybrid_ok": True,
        "min_salary": None,
        "max_salary": None,
        "experience_levels": [],
        "min_match_score": 70,
    }


@celery_app.task(
    name="worker.tasks.job_discovery.discover_jobs_for_all_users",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    soft_time_limit=1800,
    time_limit=2400,
)
def discover_jobs_for_all_users(self):
    """
    Find all active users and trigger job discovery for each.
    Runs hourly via beat schedule.
    """
    logger.info("Starting job discovery for all users")
    session = _get_db_session()

    try:
        users = _get_active_users(session)
        logger.info(f"Found {len(users)} active users for job discovery")

        triggered = 0
        for user in users:
            # Trigger individual user discovery
            discover_jobs_for_user.delay(user_id=str(user["id"]))
            triggered += 1

        logger.info(f"Triggered job discovery for {triggered} users")
        return {"users_triggered": triggered, "total_active": len(users)}

    except Exception as exc:
        logger.error(f"Job discovery for all users failed: {exc}", exc_info=True)
        raise self.retry(exc=exc)
    finally:
        session.close()


@celery_app.task(
    name="worker.tasks.job_discovery.discover_jobs_for_user",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    soft_time_limit=600,
    time_limit=900,
)
def discover_jobs_for_user(self, user_id: str):
    """
    Scrape LinkedIn and Naukri for new jobs matching a user's preferences.
    Stores discovered jobs and triggers matching.
    """
    logger.info(f"Starting job discovery for user {user_id}")
    session = _get_db_session()

    try:
        # Verify user exists and is active
        from sqlalchemy import text
        user_result = session.execute(text("""
            SELECT id, email, full_name FROM users
            WHERE id = :user_id AND is_active = true
        """), {"user_id": user_id})
        user_row = user_result.mappings().first()
        if not user_row:
            logger.warning(f"User {user_id} not found or inactive")
            return {"status": "skipped", "reason": "user_not_found"}

        # Get preferences from job_preferences table
        prefs = _get_user_preferences(user_id, session)

        # Build search parameters from preferences
        search_params = _build_search_params(prefs)

        all_jobs = []

        # Scrape LinkedIn using credentials from platform_credentials
        linkedin_creds = _get_user_credentials(user_id, "linkedin", session)
        if linkedin_creds:
            try:
                linkedin_jobs = asyncio.run(
                    _scrape_linkedin(user_id, linkedin_creds, search_params)
                )
                # If searched with Easy Apply filter, set easy_apply based on
                # scraper detection; default to True only if scraper didn't check
                if search_params.get("easy_apply_only"):
                    for job in linkedin_jobs:
                        if "easy_apply" not in job:
                            job["easy_apply"] = True
                all_jobs.extend(linkedin_jobs)
                logger.info(f"Found {len(linkedin_jobs)} LinkedIn jobs for user {user_id}")
            except Exception as e:
                logger.error(f"LinkedIn scraping failed for user {user_id}: {e}")

        # Scrape Naukri using credentials from platform_credentials
        naukri_creds = _get_user_credentials(user_id, "naukri", session)
        if naukri_creds:
            try:
                naukri_jobs = asyncio.run(
                    _scrape_naukri(user_id, naukri_creds, search_params)
                )
                all_jobs.extend(naukri_jobs)
                logger.info(f"Found {len(naukri_jobs)} Naukri jobs for user {user_id}")
            except Exception as e:
                logger.error(f"Naukri scraping failed for user {user_id}: {e}")

        # Filter jobs by preferred location
        preferred_locations = prefs.get("preferred_locations") or []
        if isinstance(preferred_locations, str):
            preferred_locations = [l.strip() for l in preferred_locations.split(",")]
        remote_only = bool(prefs.get("remote_only"))
        hybrid_ok = bool(prefs.get("hybrid_ok", True))

        before_filter = len(all_jobs)
        all_jobs = _filter_jobs_by_location(all_jobs, preferred_locations, remote_only, hybrid_ok)
        logger.info(
            f"Location filter: {before_filter} -> {len(all_jobs)} jobs "
            f"(preferred: {preferred_locations}, remote_only: {remote_only})"
        )

        # Filter jobs by experience level
        user_experience = _get_user_experience(user_id, session)
        if user_experience is not None:
            before_exp_filter = len(all_jobs)
            all_jobs = _filter_jobs_by_experience(all_jobs, user_experience)
            logger.info(
                f"Experience filter: {before_exp_filter} -> {len(all_jobs)} jobs "
                f"(user experience: {user_experience} years)"
            )

        # Store discovered jobs
        new_jobs_count = _store_discovered_jobs(session, user_id, all_jobs)
        logger.info(f"Stored {new_jobs_count} new jobs for user {user_id}")

        # Trigger job matching
        if new_jobs_count > 0:
            match_jobs_for_user.delay(user_id=user_id)

        return {
            "user_id": user_id,
            "total_discovered": len(all_jobs),
            "new_jobs": new_jobs_count,
        }

    except Exception as exc:
        logger.error(f"Job discovery failed for user {user_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc)
    finally:
        session.close()


# Common city name aliases for fuzzy location matching
_CITY_ALIASES = {
    "bangalore": ["bengaluru", "banglore", "blr"],
    "mumbai": ["bombay"],
    "chennai": ["madras"],
    "kolkata": ["calcutta"],
    "delhi": ["new delhi", "ncr", "noida", "gurgaon", "gurugram", "ghaziabad", "faridabad"],
    "hyderabad": ["hyd"],
    "pune": [],
    "ahmedabad": [],
    "jaipur": [],
    "chandigarh": [],
}


def _expand_location_terms(location: str) -> set:
    """
    Expand a user's preferred location into all equivalent city name forms.

    e.g. "Banglore" -> {"banglore", "bangalore", "bengaluru", "blr"}
         "Mumbai"   -> {"mumbai", "bombay"}
         "Delhi"    -> {"delhi", "new delhi", "ncr", "noida", "gurgaon", ...}
    """
    loc = location.lower().strip()
    terms = {loc}
    for canonical, aliases in _CITY_ALIASES.items():
        all_forms = [canonical] + aliases
        # If the user's input matches any known form of this city
        if any(form in loc or loc in form for form in all_forms):
            terms.add(canonical)
            terms.update(aliases)
    return terms


def _filter_jobs_by_location(
    jobs: List[Dict[str, Any]],
    preferred_locations: List[str],
    remote_only: bool = False,
    hybrid_ok: bool = True,
) -> List[Dict[str, Any]]:
    """
    Filter scraped jobs to only keep those matching preferred locations.

    Rules:
    - If no preferred locations set: keep all jobs
    - If remote_only=True: allow ALL remote jobs regardless of city
    - If remote_only=False: remote jobs must ALSO match a preferred city
    - Non-remote jobs must match a preferred city
    - Broad country names like "India" are NOT used as match terms
      to prevent "Punjab, India" matching when user wants "Bangalore"
    """
    if not preferred_locations:
        return jobs  # No preference = keep all

    # Expand all preferred locations into search terms,
    # but exclude very broad terms like country names
    broad_terms = {"india", "united states", "usa", "uk", "united kingdom",
                   "canada", "australia", "germany", "singapore"}
    search_terms = set()
    for loc in preferred_locations:
        expanded = _expand_location_terms(loc)
        # Only add terms that aren't just country names
        for term in expanded:
            if term not in broad_terms:
                search_terms.add(term)

    # If after filtering broad terms we have nothing, use the originals
    # (user explicitly set a country as preferred location)
    if not search_terms:
        for loc in preferred_locations:
            search_terms.update(_expand_location_terms(loc))

    logger.debug(f"Location search terms (strict): {search_terms}")

    filtered = []
    for job in jobs:
        job_location = (job.get("location") or "").lower()
        is_remote = "remote" in job_location

        # Check if job location matches a preferred city
        location_match = any(term in job_location for term in search_terms)

        if location_match:
            # Location matches a preferred city - always include
            filtered.append(job)
        elif is_remote and remote_only:
            # Pure remote job and user wants remote - include regardless of city
            filtered.append(job)
        else:
            logger.debug(
                f"Filtered out '{job.get('title', '')}' at '{job.get('location', '')}' "
                f"- does not match preferred locations"
            )

    return filtered


def _get_user_experience(user_id: str, session) -> Optional[int]:
    """Fetch user's years of experience from their profile."""
    from sqlalchemy import text

    result = session.execute(text("""
        SELECT years_of_experience FROM user_profiles
        WHERE user_id = :user_id
    """), {"user_id": user_id})

    row = result.fetchone()
    if row and row[0] is not None:
        return int(row[0])
    return None


def _extract_experience_requirement(description: str) -> Optional[int]:
    """
    Extract the minimum years of experience required from a job description.

    Looks for patterns like "5+ years", "3-5 years experience", "minimum 5 years".
    """
    if not description:
        return None

    import re

    patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:relevant\s+|professional\s+|hands[- ]on\s+)?experience",
        r"(?:minimum|at\s+least|min\.?)\s*(\d+)\s*(?:years?|yrs?)",
        r"(\d+)\s*[-to]+\s*\d+\s*(?:years?|yrs?)\s*(?:of\s+)?experience",
        r"experience\s*[:–-]\s*(\d+)\+?\s*(?:years?|yrs?)",
    ]

    min_years = None
    desc_lower = description.lower()

    for pattern in patterns:
        matches = re.findall(pattern, desc_lower)
        for match in matches:
            try:
                years = int(match)
                if 0 < years <= 30:
                    if min_years is None or years < min_years:
                        min_years = years
            except (ValueError, TypeError):
                continue

    return min_years


# Mapping of LinkedIn experience levels to approximate minimum years
_EXPERIENCE_LEVEL_YEARS = {
    "internship": 0,
    "entry_level": 0,
    "associate": 1,
    "mid_senior": 5,
    "director": 10,
    "executive": 15,
}


def _filter_jobs_by_experience(
    jobs: List[Dict[str, Any]],
    user_experience_years: int,
) -> List[Dict[str, Any]]:
    """
    Band filter: keep jobs whose experience requirement falls within
    [user_exp - 1, user_exp + 2].  This filters out jobs that are both
    too senior AND too junior for the candidate.

    Examples:
      1yr user -> 0-3yr jobs only (skip 4+ year jobs)
      4yr user -> 3-6yr jobs only (skip 0-2yr and 7+ year jobs)

    Uses two strategies:
    1. LinkedIn's experience level metadata (entry_level, mid_senior, etc.)
    2. Years extracted from description text ("5+ years experience")

    Jobs without a detectable experience requirement still pass through.
    """
    min_years = max(0, user_experience_years - 1)
    max_years = user_experience_years + 2
    filtered = []

    for job in jobs:
        # Strategy 1: Check LinkedIn's experience level metadata
        exp_level = job.get("experience_level", "")
        if exp_level and exp_level in _EXPERIENCE_LEVEL_YEARS:
            level_years = _EXPERIENCE_LEVEL_YEARS[exp_level]
            if level_years < min_years or level_years > max_years:
                logger.debug(
                    f"Filtered out '{job.get('title', '')}' - level '{exp_level}' "
                    f"requires ~{level_years}yr, user has {user_experience_years}yr "
                    f"(band: {min_years}-{max_years}yr)"
                )
                continue

        # Strategy 2: Check years from description text
        required_years = _extract_experience_requirement(
            job.get("description", "")
        )

        if required_years is None:
            # No explicit requirement found - keep the job
            filtered.append(job)
        elif min_years <= required_years <= max_years:
            filtered.append(job)
        else:
            logger.debug(
                f"Filtered out '{job.get('title', '')}' - requires {required_years}yr, "
                f"user has {user_experience_years}yr (band: {min_years}-{max_years}yr)"
            )

    return filtered


def _build_search_params(prefs: Dict[str, Any]) -> Dict[str, Any]:
    """Build search parameters from user preferences."""
    target_roles = prefs.get("desired_titles") or []
    if isinstance(target_roles, str):
        target_roles = [r.strip() for r in target_roles.split(",")]

    target_locations = prefs.get("preferred_locations") or []
    if isinstance(target_locations, str):
        target_locations = [l.strip() for l in target_locations.split(",")]

    # Derive remote preference from booleans
    remote_pref = "any"
    if prefs.get("remote_only"):
        remote_pref = "remote"

    # Experience levels from preferences
    experience_levels = prefs.get("experience_levels") or []
    if isinstance(experience_levels, str):
        experience_levels = [e.strip() for e in experience_levels.split(",")]

    return {
        "keywords": target_roles,
        # Use specific locations only - no broad "India" fallback
        # If no locations set, search without location filter to let
        # LinkedIn use the user's profile location
        "locations": target_locations if target_locations else [],
        "remote_preference": remote_pref,
        "job_types": prefs.get("job_types") or ["full-time"],
        "experience_levels": experience_levels,
        "date_posted": "past_24_hours",
        "easy_apply_only": True,
        "scrape_recommended": True,  # Also scrape "Jobs for you"
    }


async def _scrape_linkedin(
    user_id: str, credentials: Dict[str, str], search_params: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Scrape LinkedIn for jobs matching user preferences."""
    scraper = LinkedInScraper(user_id=user_id)
    try:
        await scraper.initialize()
        await scraper.login(credentials["email"], credentials["password"])

        all_jobs = []
        seen_ids = set()

        # Determine experience level for search filter
        experience_levels = search_params.get("experience_levels", [])
        experience_level = experience_levels[0] if experience_levels else None

        # Search by keywords and locations
        locations = search_params.get("locations", [])
        if not locations:
            # If no locations, search without location to use LinkedIn's default
            locations = [""]

        for keyword in search_params["keywords"][:3]:  # Limit to 3 keywords
            for location in locations[:2]:  # Limit to 2 locations
                jobs = await scraper.search_jobs(
                    keyword=keyword,
                    location=location,
                    remote=search_params["remote_preference"] == "remote",
                    date_posted=search_params["date_posted"],
                    easy_apply=search_params["easy_apply_only"],
                    experience_level=experience_level,
                    max_pages=3,
                )
                for job in jobs:
                    eid = job.get("external_id", "")
                    if eid and eid not in seen_ids:
                        seen_ids.add(eid)
                        all_jobs.append(job)

        # Also scrape LinkedIn's recommended jobs ("Jobs for you")
        if search_params.get("scrape_recommended", False):
            try:
                recommended = await scraper.scrape_recommended_jobs(max_jobs=10)
                for job in recommended:
                    eid = job.get("external_id", "")
                    if eid and eid not in seen_ids:
                        seen_ids.add(eid)
                        all_jobs.append(job)
                logger.info(f"Added {len(recommended)} recommended jobs from LinkedIn")
            except Exception as e:
                logger.warning(f"Failed to scrape recommended jobs: {e}")

        return all_jobs
    finally:
        await scraper.cleanup()


async def _scrape_naukri(
    user_id: str, credentials: Dict[str, str], search_params: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Scrape Naukri for jobs matching user preferences."""
    scraper = NaukriScraper(user_id=user_id)
    try:
        await scraper.initialize()
        await scraper.login(credentials["email"], credentials["password"])

        all_jobs = []
        for keyword in search_params["keywords"][:3]:
            for location in search_params["locations"][:2]:
                jobs = await scraper.search_jobs(
                    keyword=keyword,
                    location=location,
                    max_pages=3,
                )
                all_jobs.extend(jobs)

        return all_jobs
    finally:
        await scraper.cleanup()


_DESCRIPTION_GARBAGE = [
    "skip to search", "skip to main content", "keyboard shortcuts",
    "search by title", "clear search keywords", "city, state",
    "new feed updates", "compose message", "messaging overlay",
    "reactivate premium", "set job alert", "jump to active",
]


def _clean_description(desc: str) -> str:
    """Strip LinkedIn UI garbage from descriptions before storing."""
    if not desc:
        return desc
    prefix = desc[:300].lower()
    for marker in _DESCRIPTION_GARBAGE:
        if marker in prefix:
            return ""  # Garbage description, store empty rather than noise
    return desc


def _clean_description_html(html) -> str:
    """Strip LinkedIn UI garbage from HTML descriptions before storing."""
    if not html:
        return html
    # If the plain text extracted from the HTML would be garbage, drop it
    # Simple check: look for garbage markers in first 500 chars
    prefix = html[:500].lower()
    for marker in _DESCRIPTION_GARBAGE:
        if marker in prefix:
            return None
    return html


def _dedup_title(title: str) -> str:
    """Fix duplicated titles like 'Software EngineerSoftware Engineer'."""
    if not title:
        return title
    length = len(title)
    if length % 2 == 0:
        half = length // 2
        if title[:half] == title[half:]:
            return title[:half]
    for mid in range(length // 2 - 2, length // 2 + 3):
        if 0 < mid < length:
            left = title[:mid].strip()
            right = title[mid:].strip()
            if left and left == right:
                return left
    return title


def _store_discovered_jobs(
    session, user_id: str, jobs: List[Dict[str, Any]]
) -> int:
    """Store discovered jobs, avoiding duplicates."""
    from sqlalchemy import text

    new_count = 0
    for job in jobs:
        # Check for duplicate by external_id and platform
        platform_job_id = job.get("external_id") or job.get("platform_job_id", "")
        existing = session.execute(text("""
            SELECT id FROM jobs
            WHERE platform_job_id = :platform_job_id AND platform = :platform
        """), {
            "platform_job_id": platform_job_id,
            "platform": job.get("platform", "unknown"),
        }).first()

        if existing:
            # Link existing job to user via job_matches if not already linked
            already_linked = session.execute(text("""
                SELECT id FROM job_matches
                WHERE user_id = :user_id AND job_id = :job_id
                LIMIT 1
            """), {"user_id": user_id, "job_id": existing[0]}).first()

            if not already_linked:
                session.execute(text("""
                    INSERT INTO job_matches (id, user_id, job_id, overall_score, is_bookmarked, is_dismissed, is_applied, status, created_at, updated_at)
                    VALUES (gen_random_uuid(), :user_id, :job_id, 0, false, false, false, 'new', :now, :now)
                """), {
                    "user_id": user_id,
                    "job_id": existing[0],
                    "now": datetime.now(timezone.utc),
                })
        else:
            # Insert new job with correct column names matching DB schema
            import json
            skills_list = job.get("skills", [])
            if isinstance(skills_list, str):
                skills_list = [s.strip() for s in skills_list.split(",") if s.strip()]

            location_str = job.get("location", "")
            is_remote = "remote" in location_str.lower() if location_str else False

            result = session.execute(text("""
                INSERT INTO jobs (
                    id, platform_job_id, platform, title, company, location,
                    description, description_html, salary_min, salary_max, salary_text, job_type,
                    experience_level, work_arrangement,
                    required_skills, source_url, is_easy_apply, is_remote, is_active, posted_at, scraped_at
                ) VALUES (
                    gen_random_uuid(), :platform_job_id, :platform, :title, :company, :location,
                    :description, :description_html, :salary_min, :salary_max, :salary_text, :job_type,
                    :experience_level, :work_arrangement,
                    :skills, :source_url, :is_easy_apply, :is_remote, :is_active, :posted_at, :now
                )
                RETURNING id
            """), {
                "platform_job_id": job.get("external_id") or job.get("platform_job_id", ""),
                "platform": job.get("platform", "unknown"),
                "title": _dedup_title(job.get("title", "")),
                "company": job.get("company", ""),
                "location": location_str,
                "description": _clean_description(job.get("description", "")),
                "description_html": _clean_description_html(job.get("description_html")),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
                "salary_text": job.get("salary_text"),
                "job_type": job.get("job_type", "full-time"),
                "experience_level": job.get("experience_level"),
                "work_arrangement": job.get("work_arrangement"),
                "skills": json.dumps(skills_list) if skills_list else None,
                "source_url": job.get("url") or job.get("source_url", ""),
                "is_easy_apply": job.get("easy_apply", False) or job.get("is_easy_apply", False),
                "is_remote": is_remote,
                "is_active": True,
                "posted_at": job.get("posted_at"),
                "now": datetime.now(timezone.utc),
            })

            new_job_id = result.scalar()

            # Link to user via job_matches
            session.execute(text("""
                INSERT INTO job_matches (id, user_id, job_id, overall_score, is_bookmarked, is_dismissed, is_applied, status, created_at, updated_at)
                VALUES (gen_random_uuid(), :user_id, :job_id, 0, false, false, false, 'new', :now, :now)
            """), {
                "user_id": user_id,
                "job_id": new_job_id,
                "now": datetime.now(timezone.utc),
            })
            new_count += 1

    session.commit()
    return new_count
