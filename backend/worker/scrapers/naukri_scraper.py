"""
Naukri.com job scraper.

Handles login, job search with filters, and extraction of job details
specific to Naukri's DOM structure.
"""

import asyncio
import logging
import random
import re
from typing import Dict, List, Any, Optional
from urllib.parse import urlencode, quote_plus

from worker.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class NaukriScraper(BaseScraper):
    """Naukri.com job scraper with stealth mode."""

    PLATFORM = "naukri"
    BASE_URL = "https://www.naukri.com"
    LOGIN_URL = "https://www.naukri.com/nlogin/login"
    SEARCH_URL = "https://www.naukri.com/jobapi/v3/search"
    MIN_DELAY = 1.5
    MAX_DELAY = 3.5

    async def login(self, email: str, password: str) -> bool:
        """
        Login to Naukri.com with session restoration.
        """
        logger.info(f"Attempting Naukri login for user {self.user_id}")

        # Try session restoration
        if await self._try_session_restore():
            logger.info("Naukri session restored from cookies")
            self._is_logged_in = True
            return True

        # Navigate to login page
        await self.page.goto(self.LOGIN_URL, wait_until="networkidle")
        await self.random_delay(1.5, 3.0)

        try:
            # Wait for login form
            await self.page.wait_for_selector(
                'input[type="text"][placeholder*="Email"], '
                'input[id="usernameField"]',
                timeout=15000,
            )

            # Enter email
            email_selector = (
                'input[type="text"][placeholder*="Email"], '
                'input[id="usernameField"], '
                'input[placeholder*="email"]'
            )
            await self.human_type(email_selector, email)
            await self.random_delay(0.5, 1.0)

            # Enter password
            password_selector = (
                'input[type="password"], '
                'input[id="passwordField"], '
                'input[placeholder*="password" i]'
            )
            await self.human_type(password_selector, password)
            await self.random_delay(0.5, 1.5)

            # Click login button
            login_btn_selectors = [
                'button[type="submit"]',
                'button:has-text("Login")',
                ".login-btn",
                'button[class*="loginButton"]',
            ]

            for selector in login_btn_selectors:
                btn = await self.page.query_selector(selector)
                if btn and await btn.is_visible():
                    await btn.click()
                    break

            await self.random_delay(3.0, 5.0)
            await self.wait_for_navigation()

            # Check for CAPTCHA
            if await self.check_for_captcha():
                logger.warning("CAPTCHA detected during Naukri login")
                await self.take_screenshot("naukri_captcha")
                return False

            # Verify login success
            if await self._verify_login():
                self._is_logged_in = True
                logger.info("Naukri login successful")
                return True

            # Check for error messages
            error_el = await self.page.query_selector(
                ".error-msg, .errMsg, [class*='error']"
            )
            if error_el:
                error_text = await error_el.text_content()
                logger.error(f"Naukri login error: {error_text}")

            return False

        except Exception as e:
            logger.error(f"Naukri login exception: {e}", exc_info=True)
            await self.take_screenshot("naukri_login_error")
            return False

    async def _try_session_restore(self) -> bool:
        """Try to restore Naukri session from cookies."""
        try:
            await self.page.goto(f"{self.BASE_URL}/mnjuser/profile", wait_until="networkidle")
            await self.random_delay(1.0, 2.0)

            if "/nlogin" not in self.page.url:
                return await self._verify_login()
            return False
        except Exception:
            return False

    async def _verify_login(self) -> bool:
        """Verify that we're logged into Naukri."""
        login_indicators = [
            ".nI-gNb-drawer__icon",
            ".nI-gNb-header__avatar",
            'a[href*="/mnjuser/profile"]',
            ".user-info",
            "#login_Layer",
        ]

        for selector in login_indicators:
            if await self.is_element_visible(selector):
                return True

        # Check URL
        current_url = self.page.url
        if "/nlogin" not in current_url and "naukri.com" in current_url:
            # Try accessing profile
            try:
                response = await self.page.goto(
                    f"{self.BASE_URL}/mnjuser/profile",
                    wait_until="domcontentloaded",
                )
                if response and response.status == 200 and "/nlogin" not in self.page.url:
                    return True
            except Exception:
                pass

        return False

    async def search_jobs(
        self,
        keyword: str,
        location: str = "",
        experience: int = 0,
        salary_min: int = None,
        job_type: str = None,
        max_pages: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Search Naukri for jobs matching criteria.

        Args:
            keyword: Job title or keyword
            location: City/location filter
            experience: Years of experience
            salary_min: Minimum salary in lakhs
            job_type: Job type filter
            max_pages: Maximum pages to scrape

        Returns:
            List of job dictionaries
        """
        if not self._is_logged_in:
            logger.error("Not logged in to Naukri")
            return []

        logger.info(f"Searching Naukri: keyword='{keyword}', location='{location}'")

        all_jobs = []

        for page_num in range(1, max_pages + 1):
            # Build search URL
            search_url = self._build_search_url(
                keyword=keyword,
                location=location,
                experience=experience,
                salary_min=salary_min,
                page=page_num,
            )

            await self.page.goto(search_url, wait_until="networkidle")
            await self.random_delay(2.0, 4.0)

            # Check for CAPTCHA
            if await self.check_for_captcha():
                logger.warning("CAPTCHA detected during Naukri search")
                break

            # Wait for results
            try:
                await self.page.wait_for_selector(
                    ".srp-jobtuple-wrapper, .jobTuple, .list, article.jobTuple",
                    timeout=15000,
                )
            except Exception:
                logger.info(f"No results on page {page_num}")
                break

            # Scroll to load all results
            await self._scroll_results()

            # Extract job listings
            jobs = await self._extract_jobs()
            if not jobs:
                break

            all_jobs.extend(jobs)
            logger.info(f"Naukri page {page_num}: found {len(jobs)} jobs")

            # Rate limiting
            await self.random_delay(2.0, 5.0)

        logger.info(f"Total Naukri jobs found: {len(all_jobs)}")
        return all_jobs

    def _build_search_url(
        self,
        keyword: str,
        location: str,
        experience: int = 0,
        salary_min: int = None,
        page: int = 1,
    ) -> str:
        """Build Naukri job search URL."""
        # Naukri uses dash-separated keywords in URL
        keyword_slug = keyword.lower().replace(" ", "-")
        base = f"{self.BASE_URL}/{keyword_slug}-jobs"

        if location:
            location_slug = location.lower().replace(" ", "-")
            base += f"-in-{location_slug}"

        params = {}
        if experience:
            params["experience"] = str(experience)
        if salary_min:
            params["salary"] = str(salary_min)
        if page > 1:
            params["pageNo"] = str(page)

        # Add freshness filter (last 1 day)
        params["jobAge"] = "1"

        if params:
            return f"{base}?{urlencode(params)}"
        return base

    async def _scroll_results(self):
        """Scroll through results to trigger lazy loading."""
        for _ in range(4):
            await self.scroll_page(random.randint(400, 800))
            await asyncio.sleep(random.uniform(0.5, 1.0))

    async def _extract_jobs(self) -> List[Dict[str, Any]]:
        """Extract job listings from the current Naukri page."""
        jobs = []

        # Multiple selector patterns for Naukri's varying DOM
        card_selectors = [
            "article.jobTuple",
            ".srp-jobtuple-wrapper",
            ".jobTuple",
            '[class*="jobTuple"]',
            ".list .cardWithSalary, .list .jobTupleCard",
        ]

        job_elements = []
        for selector in card_selectors:
            job_elements = await self.page.query_selector_all(selector)
            if job_elements:
                break

        for element in job_elements:
            try:
                job = await self._extract_single_job(element)
                if job and job.get("title"):
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"Failed to extract Naukri job: {e}")
                continue

        return jobs

    async def _extract_single_job(self, element) -> Optional[Dict[str, Any]]:
        """Extract details from a single Naukri job card."""
        job = {"platform": "naukri"}

        # Job title
        title_el = await element.query_selector(
            '.title, .jobTitle, a.title, [class*="jobTitle"], '
            'a[class*="title"]'
        )
        if title_el:
            job["title"] = (await title_el.text_content() or "").strip()
            href = await title_el.get_attribute("href")
            if href:
                job["url"] = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                # Extract job ID from URL
                id_match = re.search(r"-(\d+)\??", href)
                if id_match:
                    job["external_id"] = id_match.group(1)

        # Company name
        company_el = await element.query_selector(
            '.companyInfo .subTitle, .comp-name, [class*="companyName"], '
            'a[class*="subTitle"]'
        )
        if company_el:
            job["company"] = (await company_el.text_content() or "").strip()

        # Location
        location_el = await element.query_selector(
            '.locWdth, .location, [class*="location"], '
            'span[class*="loc"], .ellipsis.fleft'
        )
        if location_el:
            job["location"] = (await location_el.text_content() or "").strip()

        # Experience
        exp_el = await element.query_selector(
            '.expwdth, .experience, [class*="experience"], '
            'span[class*="exp"]'
        )
        if exp_el:
            job["experience_text"] = (await exp_el.text_content() or "").strip()

        # Salary
        salary_el = await element.query_selector(
            '.salary, [class*="salary"], span[class*="sal"]'
        )
        if salary_el:
            salary_text = (await salary_el.text_content() or "").strip()
            if salary_text and salary_text != "Not disclosed":
                salary_info = self._parse_salary(salary_text)
                if salary_info:
                    job.update(salary_info)

        # Description/snippet
        desc_el = await element.query_selector(
            '.job-description, .ellipsis.job-description, '
            '[class*="jobDescription"], .job-desc'
        )
        if desc_el:
            job["description"] = (await desc_el.text_content() or "").strip()

        # Skills/tags
        skills_els = await element.query_selector_all(
            '.tag-li, .tags-gt li, [class*="tag"], .skill-tag'
        )
        skills = []
        for skill_el in skills_els:
            skill_text = (await skill_el.text_content() or "").strip()
            if skill_text:
                skills.append(skill_text)
        job["skills"] = ", ".join(skills)

        # Posted date
        date_el = await element.query_selector(
            '.job-post-day, [class*="posted"], .freshness'
        )
        if date_el:
            job["posted_text"] = (await date_el.text_content() or "").strip()

        # Easy apply indicator
        easy_el = await element.query_selector(
            '[class*="easyApply"], .easy-apply'
        )
        job["easy_apply"] = easy_el is not None

        # Set job type
        job["job_type"] = "full-time"  # Default for Naukri

        return job

    def _parse_salary(self, salary_text: str) -> Optional[Dict[str, Any]]:
        """Parse Naukri salary format (e.g., '10-15 Lacs PA')."""
        if not salary_text or "not disclosed" in salary_text.lower():
            return None

        # Pattern: "10-15 Lacs PA" or "10 - 15 Lacs P.A." or "10L - 15L"
        patterns = [
            r"([\d.]+)\s*[-to]+\s*([\d.]+)\s*(?:Lacs?|Lakhs?|L)\s*(?:PA|P\.A\.)?",
            r"([\d.]+)\s*[-to]+\s*([\d.]+)\s*(?:Cr|Crore)",
            r"([\d,]+)\s*[-to]+\s*([\d,]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, salary_text, re.IGNORECASE)
            if match:
                try:
                    min_val = float(match.group(1).replace(",", ""))
                    max_val = float(match.group(2).replace(",", ""))
                    # Convert to absolute if in lakhs
                    if "lac" in salary_text.lower() or "lakh" in salary_text.lower():
                        min_val *= 100000
                        max_val *= 100000
                    elif "cr" in salary_text.lower():
                        min_val *= 10000000
                        max_val *= 10000000
                    return {"salary_min": min_val, "salary_max": max_val}
                except (ValueError, IndexError):
                    continue

        return None
