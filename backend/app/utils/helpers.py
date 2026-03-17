"""
Common utility functions.

Provides text processing, date parsing, formatting, and other
shared utilities used across the application.
"""

import re
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Any
from urllib.parse import urlparse


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text


def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL, removing www prefix."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        domain = domain.replace("www.", "")
        return domain.split("/")[0]
    except Exception:
        return None


def parse_relative_date(text: str) -> Optional[datetime]:
    """
    Parse relative date strings like '2 days ago', 'Just now', etc.

    Args:
        text: Relative date string

    Returns:
        datetime object or None
    """
    if not text:
        return None

    text = text.lower().strip()
    now = datetime.now(timezone.utc)

    if "just now" in text or "moment" in text:
        return now
    if "today" in text:
        return now
    if "yesterday" in text:
        return now - timedelta(days=1)

    # Match patterns like "2 days ago", "1 week ago", etc.
    match = re.search(r'(\d+)\s*(second|minute|hour|day|week|month)s?\s*ago', text)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)

        deltas = {
            "second": timedelta(seconds=amount),
            "minute": timedelta(minutes=amount),
            "hour": timedelta(hours=amount),
            "day": timedelta(days=amount),
            "week": timedelta(weeks=amount),
            "month": timedelta(days=amount * 30),
        }

        delta = deltas.get(unit)
        if delta:
            return now - delta

    return None


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """Truncate text to max length, preserving word boundaries."""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.8:
        truncated = truncated[:last_space]
    return truncated + suffix


def generate_tracking_id(application_id: str = "", event_type: str = "") -> str:
    """Generate a unique tracking ID for email tracking."""
    if application_id and event_type:
        raw = f"{application_id}:{event_type}:{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
    return uuid.uuid4().hex[:16]


def format_salary(amount: Optional[int], currency: str = "USD") -> str:
    """Format salary amount for display."""
    if not amount:
        return "Not specified"
    if currency == "USD":
        return f"${amount:,}"
    elif currency == "INR":
        if amount >= 10000000:
            return f"{amount / 10000000:.1f} Cr"
        if amount >= 100000:
            return f"{amount / 100000:.1f}L"
        return f"{amount:,}"
    return f"{currency} {amount:,}"


def calculate_match_percentage(user_skills: list, job_skills: list) -> int:
    """
    Calculate basic skill match percentage.

    Args:
        user_skills: List of user's skills
        job_skills: List of required job skills

    Returns:
        Match percentage (0-100)
    """
    if not job_skills:
        return 50  # Default if no skills listed

    user_skills_lower = {s.lower().strip() for s in user_skills if s}
    job_skills_lower = {s.lower().strip() for s in job_skills if s}

    if not job_skills_lower:
        return 50

    matches = user_skills_lower.intersection(job_skills_lower)
    return min(100, int((len(matches) / len(job_skills_lower)) * 100))


def mask_email(email: str) -> str:
    """Mask email for display (e.g., j***@example.com)."""
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    return f"{masked_local}@{domain}"


def clean_job_title(title: str) -> str:
    """Clean and normalize job title."""
    if not title:
        return ""
    # Remove common prefixes/suffixes
    title = re.sub(r'\s*\(.*?\)\s*$', '', title)  # Remove parenthetical suffixes
    title = re.sub(r'^\s*\[.*?\]\s*', '', title)  # Remove bracketed prefixes
    title = title.strip(" -\u2013\u2014|/")
    return title.strip()


def extract_years_of_experience(text: str) -> Optional[int]:
    """
    Extract years of experience from text.

    Args:
        text: Text containing experience information

    Returns:
        Number of years or None
    """
    if not text:
        return None

    # Match patterns like "5+ years", "3-5 years", "minimum 2 years"
    patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)",
        r"(?:minimum|min|at\s*least)\s*(\d+)\s*(?:years?|yrs?)",
        r"(\d+)\s*-\s*\d+\s*(?:years?|yrs?)",
        r"(\d+)\s*(?:years?|yrs?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue

    return None


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe filesystem storage."""
    # Remove path separators and null bytes
    filename = filename.replace("/", "_").replace("\\", "_").replace("\0", "")
    # Remove other unsafe characters
    filename = re.sub(r'[<>:"|?*]', '_', filename)
    # Limit length
    name, ext = (filename.rsplit(".", 1) + [""])[:2]
    name = name[:200]
    if ext:
        return f"{name}.{ext}"
    return name


def normalize_url(url: str) -> str:
    """Normalize a URL by adding protocol and cleaning."""
    if not url:
        return ""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    # Remove trailing slashes
    return url.rstrip("/")


def chunk_list(items: list, chunk_size: int) -> List[list]:
    """Split a list into chunks of specified size."""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def safe_get(obj: Any, *keys, default=None) -> Any:
    """
    Safely get nested values from dicts/objects.

    Usage: safe_get(data, "user", "profile", "name", default="Unknown")
    """
    current = obj
    for key in keys:
        try:
            if isinstance(current, dict):
                current = current.get(key)
            elif hasattr(current, key):
                current = getattr(current, key)
            else:
                return default
            if current is None:
                return default
        except (KeyError, AttributeError, TypeError):
            return default
    return current if current is not None else default


def generate_uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


def hash_string(text: str) -> str:
    """Generate SHA-256 hash of a string."""
    return hashlib.sha256(text.encode()).hexdigest()
