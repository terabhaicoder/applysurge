"""Scraper utility unit tests."""

import pytest
from datetime import datetime, timezone, timedelta

from app.utils.helpers import (
    slugify,
    extract_domain,
    parse_relative_date,
    truncate_text,
    clean_job_title,
    extract_years_of_experience,
    sanitize_filename,
    normalize_url,
    calculate_match_percentage,
    mask_email,
)


def test_slugify():
    """Test slugify converts text to URL-safe slugs."""
    assert slugify("Hello World") == "hello-world"
    assert slugify("  Multiple   Spaces  ") == "multiple-spaces"
    assert slugify("Special! @#$ Characters") == "special-characters"
    assert slugify("Under_scores and-dashes") == "under-scores-and-dashes"
    assert slugify("---Leading and Trailing---") == "leading-and-trailing"
    assert slugify("UPPERCASE TEXT") == "uppercase-text"
    assert slugify("already-a-slug") == "already-a-slug"


def test_extract_domain():
    """Test extract_domain pulls domain from various URL formats."""
    assert extract_domain("https://www.example.com/path") == "example.com"
    assert extract_domain("http://jobs.linkedin.com/posting/123") == "jobs.linkedin.com"
    assert extract_domain("https://example.com") == "example.com"
    assert extract_domain("https://www.indeed.com/jobs?q=python") == "indeed.com"
    assert extract_domain("invalid-url") is None or extract_domain("invalid-url") == "invalid-url"
    assert extract_domain("") is None or extract_domain("") == ""


def test_parse_relative_date():
    """Test parse_relative_date handles various relative date strings."""
    now = datetime.now(timezone.utc)

    # "Just now" should return approximately now
    result = parse_relative_date("Just now")
    assert result is not None
    assert abs((now - result).total_seconds()) < 5

    # "today" should return approximately now
    result = parse_relative_date("today")
    assert result is not None
    assert abs((now - result).total_seconds()) < 5

    # "yesterday" should be about 1 day ago
    result = parse_relative_date("yesterday")
    assert result is not None
    assert abs((now - result).total_seconds() - 86400) < 5

    # "2 days ago"
    result = parse_relative_date("2 days ago")
    assert result is not None
    expected = now - timedelta(days=2)
    assert abs((expected - result).total_seconds()) < 5

    # "3 hours ago"
    result = parse_relative_date("3 hours ago")
    assert result is not None
    expected = now - timedelta(hours=3)
    assert abs((expected - result).total_seconds()) < 5

    # "1 week ago"
    result = parse_relative_date("1 week ago")
    assert result is not None
    expected = now - timedelta(weeks=1)
    assert abs((expected - result).total_seconds()) < 5

    # Empty or invalid input
    assert parse_relative_date("") is None
    assert parse_relative_date("no date here") is None


def test_truncate_text():
    """Test truncate_text handles various lengths and word boundaries."""
    short_text = "Short text"
    assert truncate_text(short_text, max_length=500) == short_text

    long_text = "This is a much longer text that should be truncated at some point " * 20
    result = truncate_text(long_text, max_length=50)
    assert len(result) <= 50
    assert result.endswith("...")

    # Custom suffix
    result = truncate_text(long_text, max_length=50, suffix="[more]")
    assert result.endswith("[more]")
    assert len(result) <= 50

    # Exact length should not be truncated
    exact_text = "x" * 500
    assert truncate_text(exact_text, max_length=500) == exact_text


def test_clean_job_title():
    """Test clean_job_title removes noise from job titles."""
    assert clean_job_title("Software Engineer (Remote)") == "Software Engineer"
    assert clean_job_title("[Urgent] Backend Developer") == "Backend Developer"
    assert clean_job_title("  Data Scientist  ") == "Data Scientist"
    assert clean_job_title("- Senior Engineer -") == "Senior Engineer"
    assert clean_job_title("") == ""
    assert clean_job_title("Product Manager (Contract) ") == "Product Manager"


def test_extract_years_of_experience():
    """Test extract_years_of_experience from various text formats."""
    assert extract_years_of_experience("5+ years of experience") == 5
    assert extract_years_of_experience("Minimum 3 years") == 3
    assert extract_years_of_experience("3-5 years experience") == 3
    assert extract_years_of_experience("7 yrs of exp") == 7
    assert extract_years_of_experience("at least 2 years") == 2
    assert extract_years_of_experience("No experience mentioned") is None
    assert extract_years_of_experience("") is None
    assert extract_years_of_experience("10 years of experience required") == 10


def test_sanitize_filename():
    """Test sanitize_filename removes unsafe characters."""
    assert sanitize_filename("normal_file.txt") == "normal_file.txt"
    assert sanitize_filename("path/to/file.pdf") == "path_to_file.pdf"
    assert sanitize_filename('bad<>:"|?*.doc') == "bad_______.doc"
    assert sanitize_filename("file\\with\\backslashes.txt") == "file_with_backslashes.txt"
    assert sanitize_filename("no_extension") == "no_extension"

    # Long filenames should be truncated
    long_name = "a" * 300 + ".pdf"
    result = sanitize_filename(long_name)
    assert result.endswith(".pdf")
    assert len(result) <= 204  # 200 for name + 1 for dot + 3 for ext


def test_normalize_url():
    """Test normalize_url adds protocol and cleans URLs."""
    assert normalize_url("example.com") == "https://example.com"
    assert normalize_url("http://example.com/") == "http://example.com"
    assert normalize_url("https://example.com///") == "https://example.com"
    assert normalize_url("  example.com  ") == "https://example.com"
    assert normalize_url("") == ""
    assert normalize_url("https://already-valid.com") == "https://already-valid.com"


def test_calculate_match_percentage():
    """Test calculate_match_percentage computes skill overlap correctly."""
    # Perfect match
    assert calculate_match_percentage(
        ["Python", "SQL", "Docker"],
        ["Python", "SQL", "Docker"],
    ) == 100

    # Partial match
    assert calculate_match_percentage(
        ["Python", "SQL"],
        ["Python", "SQL", "Docker", "K8s"],
    ) == 50

    # No match
    assert calculate_match_percentage(
        ["Java", "C++"],
        ["Python", "SQL"],
    ) == 0

    # Empty job skills returns default 50
    assert calculate_match_percentage(["Python"], []) == 50

    # Case insensitive matching
    assert calculate_match_percentage(
        ["python", "SQL"],
        ["Python", "sql"],
    ) == 100

    # Empty user skills
    assert calculate_match_percentage(
        [],
        ["Python", "SQL"],
    ) == 0


def test_mask_email():
    """Test mask_email hides the local part of email addresses."""
    assert mask_email("john@example.com") == "j***n@example.com"
    assert mask_email("ab@example.com") == "a***@example.com"
    assert mask_email("a@example.com") == "a***@example.com"
    assert mask_email("no-at-sign") == "no-at-sign"
    assert mask_email("longname@domain.org") == "l***e@domain.org"
