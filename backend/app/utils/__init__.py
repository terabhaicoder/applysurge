"""
JobPilot utility modules.

Provides email finding, verification, and common helper functions.
"""

from app.utils.email_finder import EmailFinder
from app.utils.email_verifier import EmailVerifier
from app.utils.helpers import (
    slugify,
    extract_domain,
    parse_relative_date,
    truncate_text,
    generate_tracking_id,
    format_salary,
    calculate_match_percentage,
    mask_email,
    clean_job_title,
)

__all__ = [
    "EmailFinder",
    "EmailVerifier",
    "slugify",
    "extract_domain",
    "parse_relative_date",
    "truncate_text",
    "generate_tracking_id",
    "format_salary",
    "calculate_match_percentage",
    "mask_email",
    "clean_job_title",
]
