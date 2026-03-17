"""
JobPilot scrapers module.

Platform-specific web scrapers for job discovery and application automation.
"""

from worker.scrapers.linkedin_scraper import LinkedInScraper
from worker.scrapers.naukri_scraper import NaukriScraper
from worker.scrapers.company_scraper import CompanyScraper

__all__ = [
    "LinkedInScraper",
    "NaukriScraper",
    "CompanyScraper",
]
