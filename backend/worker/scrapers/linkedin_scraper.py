"""
LinkedIn job scraper.

Full-featured scraper with login, session restoration, stealth mode,
search filters, job detail extraction, pagination, and anti-detection.
"""

import asyncio
import logging
import random
import re
from typing import Dict, List, Any, Optional
from urllib.parse import urlencode, quote_plus
from datetime import datetime, timezone

from worker.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class LinkedInScraper(BaseScraper):
    """LinkedIn job scraper with stealth mode and anti-detection."""

    PLATFORM = "linkedin"
    BASE_URL = "https://www.linkedin.com"
    LOGIN_URL = "https://www.linkedin.com/login"
    JOBS_URL = "https://www.linkedin.com/jobs/search/"
    MIN_DELAY = 2.0
    MAX_DELAY = 5.0

    # Date posted filter mappings
    DATE_FILTERS = {
        "past_24_hours": "r86400",
        "past_week": "r604800",
        "past_month": "r2592000",
        "any_time": "",
    }

    # Job type mappings
    JOB_TYPE_FILTERS = {
        "full-time": "F",
        "part-time": "P",
        "contract": "C",
        "temporary": "T",
        "internship": "I",
        "volunteer": "V",
    }

    # Experience level mappings
    EXPERIENCE_FILTERS = {
        "internship": "1",
        "entry_level": "2",
        "associate": "3",
        "mid_senior": "4",
        "director": "5",
        "executive": "6",
    }

    # Strings that indicate the description is LinkedIn UI garbage, not real content
    _GARBAGE_MARKERS = [
        "show more options", "send feedback", "report this job",
        "share\n", "save\n", "repost\n",
        "skip to search", "skip to main content", "keyboard shortcuts",
        "search by title", "clear search keywords", "city, state",
        "new feed updates", "compose message", "messaging overlay",
        "reactivate premium", "for business", "set alert", "set job alert",
        "jump to active", "my network", "notifications",
    ]

    @staticmethod
    def _dedup_title(title: str) -> str:
        """Fix duplicated titles like 'Software EngineerSoftware Engineer'."""
        if not title:
            return title
        length = len(title)
        if length % 2 == 0:
            half = length // 2
            if title[:half] == title[half:]:
                return title[:half]
        # Also handle cases with minor whitespace differences
        for mid in range(length // 2 - 2, length // 2 + 3):
            if 0 < mid < length:
                left = title[:mid].strip()
                right = title[mid:].strip()
                if left and left == right:
                    return left
        return title

    def _is_valid_description(self, text: str) -> bool:
        """Check if extracted description is real content, not LinkedIn UI garbage."""
        if not text or len(text) < 80:
            return False
        text_lower = text.lower()
        # Check the first 300 chars for UI element markers
        prefix = text_lower[:300]
        for marker in self._GARBAGE_MARKERS:
            if prefix.count(marker) > 0:
                return False
        return True

    async def login(self, email: str, password: str) -> bool:
        """
        Login to LinkedIn with session restoration and stealth mode.
        First attempts to use existing cookies, falls back to credential login.
        """
        logger.info(f"Attempting LinkedIn login for user {self.user_id}")

        # Try session restoration first
        if await self._try_session_restore():
            logger.info("LinkedIn session restored from cookies")
            self._is_logged_in = True
            return True

        # Navigate to login page
        await self.page.goto(self.LOGIN_URL, wait_until="domcontentloaded")
        await self.random_delay(1.0, 2.0)

        # Check if already logged in (redirected to feed)
        if "/feed" in self.page.url or "/mynetwork" in self.page.url:
            logger.info("Already logged in to LinkedIn")
            self._is_logged_in = True
            return True

        # Fill login form
        try:
            # Wait for login form
            await self.page.wait_for_selector("#username", timeout=10000)

            # Enter email with human-like typing
            await self.human_type("#username", email)
            await self.random_delay(0.5, 1.0)

            # Enter password
            await self.human_type("#password", password)
            await self.random_delay(0.5, 1.5)

            # Click sign in button
            await self.page.click('button[type="submit"]')
            await self.random_delay(2.0, 4.0)

            # Wait for navigation
            await self.wait_for_navigation()

            # Check for CAPTCHA or security challenge
            if await self.check_for_captcha():
                logger.warning("CAPTCHA detected during LinkedIn login")
                screenshot = await self.take_screenshot("linkedin_captcha")
                return False

            # Check for security verification
            if await self._check_security_challenge():
                logger.warning("Security challenge detected during LinkedIn login")
                screenshot = await self.take_screenshot("linkedin_security_challenge")
                return False

            # Verify login success
            if "/feed" in self.page.url or "/mynetwork" in self.page.url:
                self._is_logged_in = True
                logger.info("LinkedIn login successful")
                return True

            # Check for error messages
            error_el = await self.page.query_selector("#error-for-username, #error-for-password, .form__label--error")
            if error_el:
                error_text = await error_el.text_content()
                logger.error(f"LinkedIn login error: {error_text}")
                return False

            # Give it a moment and check again
            await self.random_delay(2.0, 3.0)
            if "linkedin.com" in self.page.url and "/login" not in self.page.url:
                self._is_logged_in = True
                return True

            logger.error(f"LinkedIn login failed, current URL: {self.page.url}")
            return False

        except Exception as e:
            logger.error(f"LinkedIn login exception: {e}", exc_info=True)
            await self.take_screenshot("linkedin_login_error")
            return False

    async def _try_session_restore(self) -> bool:
        """Try to restore session from saved cookies."""
        try:
            await self.page.goto(f"{self.BASE_URL}/feed", wait_until="domcontentloaded")
            await self.random_delay(2.0, 3.0)

            # Check if we're on the feed (logged in) - not redirected to login
            if "/feed" in self.page.url and "/login" not in self.page.url:
                # Try multiple selectors for profile verification
                profile_el = await self.page.query_selector(
                    ", ".join([
                        ".feed-identity-module",
                        ".global-nav__me-photo",
                        "img.global-nav__me-photo",
                        ".global-nav__primary-link-me-menu-trigger",
                        "nav.global-nav",
                        ".scaffold-layout__main",
                    ])
                )
                if profile_el:
                    return True

                # If we're on /feed and not on /login, session is likely valid
                # even if profile element selectors changed
                logger.info(f"On feed page but no profile element found, URL: {self.page.url}")
                return True

            return False
        except Exception as e:
            logger.debug(f"Session restore failed: {e}")
            return False

    async def _check_security_challenge(self) -> bool:
        """Check if LinkedIn is showing a security challenge."""
        challenge_selectors = [
            "#input__email_verification_pin",
            ".checkpoint-challenge",
            "#captcha-internal",
            'input[name="pin"]',
            ".security-verification",
        ]
        for selector in challenge_selectors:
            if await self.is_element_visible(selector):
                return True
        return False

    async def search_jobs(
        self,
        keyword: str,
        location: str = "",
        remote: bool = False,
        date_posted: str = "past_24_hours",
        easy_apply: bool = True,
        job_type: str = "full-time",
        experience_level: str = None,
        max_pages: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Search LinkedIn for jobs with specified filters.

        Args:
            keyword: Job title or keyword to search
            location: Location filter
            remote: Whether to filter for remote jobs
            date_posted: Time filter (past_24_hours, past_week, past_month, any_time)
            easy_apply: Filter for Easy Apply jobs only
            job_type: Job type filter
            experience_level: Experience level filter
            max_pages: Maximum number of pages to scrape

        Returns:
            List of job dictionaries with extracted details
        """
        if not self._is_logged_in:
            logger.error("Not logged in to LinkedIn")
            return []

        logger.info(f"Searching LinkedIn: keyword='{keyword}', location='{location}'")

        # Build search URL with filters
        search_url = self._build_search_url(
            keyword=keyword,
            location=location,
            remote=remote,
            date_posted=date_posted,
            easy_apply=easy_apply,
            job_type=job_type,
            experience_level=experience_level,
        )

        all_jobs = []
        seen_ids = set()

        for page_num in range(max_pages):
            # Navigate to search results page
            page_url = f"{search_url}&start={page_num * 25}"
            await self.page.goto(page_url, wait_until="domcontentloaded")
            await self.random_delay(3.0, 5.0)

            # Check for captcha
            if await self.check_for_captcha():
                logger.warning("CAPTCHA detected during job search")
                break

            # Wait for job listings to load - try multiple selectors for different LinkedIn layouts
            results_found = False
            results_selectors = [
                ".jobs-search-results-list",
                ".jobs-search__results-list",
                ".scaffold-layout__list",
                "[class*='jobs-search']",
                ".jobs-search-results",
                "ul.scaffold-layout__list-container",
                "li[class*='job-card']",
                "[data-job-id]",
            ]
            for sel in results_selectors:
                try:
                    await self.page.wait_for_selector(sel, timeout=5000)
                    results_found = True
                    logger.info(f"Found results with selector: {sel}")
                    break
                except Exception:
                    continue

            if not results_found:
                logger.warning(f"No job results found on page {page_num + 1}")
                await self.take_screenshot(f"linkedin_no_results_page_{page_num + 1}")
                break

            # Scroll through the results list to load all items
            await self._scroll_job_list()

            # Extract job cards from the page
            job_cards = await self._extract_job_cards()
            if not job_cards:
                logger.info(f"No more jobs found on page {page_num + 1}")
                break

            # Get detailed info for each job
            # Track cards that need full-page navigation separately
            # to avoid breaking the search results page for remaining cards
            cards_needing_full_page = []

            for card in job_cards:
                eid = card.get("external_id", "")
                if eid in seen_ids:
                    continue

                try:
                    job_details = await self._extract_job_details(card)
                    if job_details:
                        seen_ids.add(eid)
                        all_jobs.append(job_details)
                except Exception as e:
                    logger.warning(f"Failed to extract job details for {eid}: {e}")
                    continue

                # If we navigated away from search results, go back
                if "/jobs/view/" in self.page.url:
                    try:
                        await self.page.goto(page_url, wait_until="domcontentloaded")
                        await self.random_delay(2.0, 3.0)
                        await self._scroll_job_list()
                    except Exception:
                        break  # Can't recover, move to next page

                # Rate limiting between job detail extraction
                await self.random_delay(1.0, 2.5)

            logger.info(f"Page {page_num + 1}: extracted {len(job_cards)} jobs")

            # Rate limiting between pages
            await self.random_delay(3.0, 6.0)

            # Check if there's a next page
            has_next = await self.is_element_visible(
                'button[aria-label="Page {page}"]'.format(page=page_num + 2)
            )
            if not has_next and page_num < max_pages - 1:
                # Also check for the pagination container
                pagination = await self.page.query_selector(".artdeco-pagination")
                if not pagination:
                    break

        logger.info(f"Total LinkedIn jobs found: {len(all_jobs)}")
        return all_jobs

    def _build_search_url(
        self,
        keyword: str,
        location: str,
        remote: bool,
        date_posted: str,
        easy_apply: bool,
        job_type: str,
        experience_level: str = None,
    ) -> str:
        """Build LinkedIn job search URL with filters."""
        params = {
            "keywords": keyword,
            "location": location,
            "sortBy": "DD",  # Sort by date
        }

        # Date filter
        date_filter = self.DATE_FILTERS.get(date_posted, "")
        if date_filter:
            params["f_TPR"] = date_filter

        # Easy Apply filter
        if easy_apply:
            params["f_AL"] = "true"

        # Remote filter
        if remote:
            params["f_WT"] = "2"  # Remote

        # Job type filter
        if job_type and job_type in self.JOB_TYPE_FILTERS:
            params["f_JT"] = self.JOB_TYPE_FILTERS[job_type]

        # Experience level filter
        if experience_level and experience_level in self.EXPERIENCE_FILTERS:
            params["f_E"] = self.EXPERIENCE_FILTERS[experience_level]

        return f"{self.JOBS_URL}?{urlencode(params)}"

    async def _scroll_job_list(self):
        """Scroll through the job results list to trigger lazy loading."""
        list_selectors = [
            ".jobs-search-results-list",
            ".jobs-search__results-list",
            ".scaffold-layout__list",
            ".scaffold-layout__list-container",
        ]
        try:
            for list_selector in list_selectors:
                list_el = await self.page.query_selector(list_selector)
                if list_el:
                    for i in range(5):
                        await self.page.evaluate(
                            """(selector) => {
                                const el = document.querySelector(selector);
                                if (el) el.scrollTop += 300;
                            }""",
                            list_selector,
                        )
                        await asyncio.sleep(random.uniform(0.3, 0.7))
                    break
            else:
                # Fallback: scroll the page itself
                for i in range(5):
                    await self.page.evaluate("window.scrollBy(0, 400)")
                    await asyncio.sleep(random.uniform(0.3, 0.7))
        except Exception as e:
            logger.debug(f"Scroll job list error: {e}")

    async def _extract_job_cards(self) -> List[Dict[str, Any]]:
        """Extract basic job card information from the search results page."""
        cards = []

        card_selectors = [
            "[data-job-id]",
            ".jobs-search-results__list-item",
            ".job-card-container",
            "li[class*='job-card']",
            ".scaffold-layout__list-container > li",
            ".jobs-search__results-list li",
            "li.ember-view.occludable-update",
        ]

        job_elements = []
        for selector in card_selectors:
            job_elements = await self.page.query_selector_all(selector)
            if job_elements:
                logger.info(f"Found {len(job_elements)} job cards with selector: {selector}")
                break

        for element in job_elements:
            try:
                card = {}

                # Extract job ID from data attribute or link
                job_id = await element.get_attribute("data-job-id")
                if not job_id:
                    link_el = await element.query_selector("a[href*='/jobs/view/']")
                    if link_el:
                        href = await link_el.get_attribute("href")
                        job_id_match = re.search(r"/jobs/view/(\d+)", href or "")
                        if job_id_match:
                            job_id = job_id_match.group(1)

                if not job_id:
                    logger.debug("Skipped job card with no extractable job ID")
                    continue

                card["external_id"] = job_id
                card["url"] = f"{self.BASE_URL}/jobs/view/{job_id}/"

                # Title
                title_el = await element.query_selector(
                    ".job-card-list__title, .job-card-container__link, "
                    "a.job-card-list__title--link strong, "
                    "[class*='job-card'] a[class*='title'], "
                    "a[class*='job-card-list__title'], "
                    ".artdeco-entity-lockup__title a, "
                    "a[href*='/jobs/view/']"
                )
                if title_el:
                    # Use inner_text() to avoid duplicated accessibility text
                    raw_title = (await title_el.inner_text() or "").strip()
                    card["title"] = self._dedup_title(raw_title)

                # Company
                company_el = await element.query_selector(
                    ".job-card-container__primary-description, "
                    ".job-card-container__company-name, "
                    ".artdeco-entity-lockup__subtitle, "
                    "[class*='company-name'], "
                    "[class*='primary-description']"
                )
                if company_el:
                    card["company"] = (await company_el.inner_text() or "").strip()

                # Location
                location_el = await element.query_selector(
                    ".job-card-container__metadata-item, "
                    ".artdeco-entity-lockup__caption, "
                    "[class*='metadata-item'], "
                    "[class*='job-card-container__metadata']"
                )
                if location_el:
                    card["location"] = (await location_el.inner_text() or "").strip()

                # Easy Apply badge
                easy_apply_el = await element.query_selector(
                    ".job-card-container__apply-method, "
                    "[class*='easy-apply'], "
                    "[class*='apply-method']"
                )
                card["easy_apply"] = easy_apply_el is not None

                cards.append(card)

            except Exception as e:
                logger.debug(f"Failed to extract job card: {e}")
                continue

        return cards

    async def _click_show_more_description(self):
        """Click 'See more' / 'Show more' / '...more' to expand the full job description."""
        # Use JavaScript to find and click any "more" element (button, link, or span)
        try:
            expanded = await self.page.evaluate("""
                () => {
                    // Strategy 1: Click any element containing "more" text that looks like an expander
                    const candidates = document.querySelectorAll(
                        'button, a, span[role="button"], [class*="show-more"], [class*="see-more"], footer button'
                    );
                    for (const el of candidates) {
                        const text = (el.textContent || '').toLowerCase().trim();
                        const label = (el.getAttribute('aria-label') || '').toLowerCase();
                        if (text === 'more' || text === '…more' || text === '... more' ||
                            text.includes('see more') || text.includes('show more') ||
                            label.includes('see more') || label.includes('show more')) {
                            el.click();
                            return 'clicked';
                        }
                    }

                    // Strategy 2: Force-expand by removing CSS overflow/height constraints
                    // on any element that looks like a description container
                    const containers = document.querySelectorAll(
                        '#job-details, .jobs-description__content, .show-more-less-html, ' +
                        '[class*="jobs-description"], [class*="description__text"], ' +
                        'article[class*="job"], [class*="about-the-job"]'
                    );
                    for (const desc of containers) {
                        desc.style.maxHeight = 'none';
                        desc.style.overflow = 'visible';
                        desc.classList.remove('jobs-description__content--hide');
                        const inner = desc.querySelector('[class*="html-content"], [class*="markup"]');
                        if (inner) {
                            inner.style.maxHeight = 'none';
                            inner.style.overflow = 'visible';
                        }
                    }
                    return containers.length > 0 ? 'expanded' : 'none';
                }
            """)
            if expanded and expanded != 'none':
                await self.random_delay(0.5, 1.0)
                logger.debug(f"Description expand result: {expanded}")
                return True
        except Exception as e:
            logger.debug(f"Click show more failed: {e}")

        return False

    async def _extract_full_description(self) -> Dict[str, Any]:
        """
        Extract the full job description, handling collapsed content.
        Returns dict with 'description' and optionally 'description_html'.
        """
        result = {}

        # First, try to expand the description
        await self._click_show_more_description()

        # Wait a moment for content to expand
        await self.random_delay(0.5, 1.0)

        # Use JavaScript to find the description - this is the most reliable approach
        # because LinkedIn's DOM structure changes frequently
        try:
            desc_data = await self.page.evaluate("""
                () => {
                    // Helper: clean description text
                    function cleanDesc(text) {
                        if (!text) return '';
                        text = text.trim();
                        // Remove "About the job" header
                        if (text.toLowerCase().startsWith('about the job')) {
                            text = text.substring('about the job'.length).trim();
                        }
                        return text;
                    }

                    // Helper: check if text looks like real description (not UI elements)
                    function isValid(text) {
                        if (!text || text.length < 80) return false;
                        const lower = text.toLowerCase();
                        const garbage = [
                            'show more options', 'send feedback', 'report this job',
                            'skip to search', 'skip to main content', 'keyboard shortcuts',
                            'search by title', 'clear search', 'set alert', 'set job alert',
                            'jump to active', 'new feed updates', 'compose message',
                            'messaging overlay', 'press enter to open',
                            'reactivate premium', 'for business',
                        ];
                        const prefix = lower.substring(0, 300);
                        for (const g of garbage) {
                            if (prefix.includes(g)) return false;
                        }
                        return true;
                    }

                    // Strategy 1: Known description containers (most specific first)
                    const selectors = [
                        '#job-details',
                        '.jobs-description__content .jobs-box__html-content',
                        '.jobs-description__content',
                        '[aria-label="Job description"]',
                        '.jobs-box__html-content',
                        '.show-more-less-html__markup',
                        '.description__text',
                        '.job-details-about-the-job-module__description',
                    ];
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el) {
                            const text = cleanDesc(el.innerText);
                            if (isValid(text)) {
                                return { text, html: el.innerHTML || '' };
                            }
                        }
                    }

                    // Strategy 2: Find section with "About the job" heading and get its content
                    const headings = document.querySelectorAll('h2, h3, [class*="header"], [class*="heading"]');
                    for (const h of headings) {
                        const hText = (h.textContent || '').trim().toLowerCase();
                        if (hText === 'about the job' || hText.includes('about the job')) {
                            // Get the parent section/card and extract its text content
                            let container = h.parentElement;
                            // Walk up a few levels to find the section container
                            for (let i = 0; i < 3 && container; i++) {
                                const text = cleanDesc(container.innerText);
                                if (isValid(text) && text.length > 100) {
                                    return { text, html: container.innerHTML || '' };
                                }
                                container = container.parentElement;
                            }
                            // Also try the next sibling
                            let sibling = h.nextElementSibling;
                            while (sibling) {
                                const text = cleanDesc(sibling.innerText);
                                if (isValid(text)) {
                                    return { text, html: sibling.innerHTML || '' };
                                }
                                sibling = sibling.nextElementSibling;
                            }
                        }
                    }

                    // Strategy 3: Search ONLY within the job detail panel (right side)
                    // NOT the full page - avoid grabbing nav, search, job list, etc.
                    let bestText = '';
                    let bestHtml = '';
                    // Only search within known job detail containers
                    const detailContainers = [
                        '.jobs-search__job-details',
                        '.job-details-module',
                        '.jobs-details',
                        '.scaffold-layout__detail',
                        '.jobs-unified-top-card',
                        '[class*="job-details"]',
                        '[class*="jobs-description"]',
                    ];
                    let searchRoot = null;
                    for (const sel of detailContainers) {
                        searchRoot = document.querySelector(sel);
                        if (searchRoot) break;
                    }
                    // If no detail container found, don't fall back to full page
                    if (searchRoot) {
                        const allDivs = searchRoot.querySelectorAll('div, article, section');
                        for (const div of allDivs) {
                            const cls = div.className || '';
                            // Skip non-description sections within the detail panel
                            if (cls.includes('nav') || cls.includes('header') || cls.includes('sidebar') ||
                                cls.includes('premium') || cls.includes('similar-jobs') || cls.includes('footer') ||
                                cls.includes('top-card') || cls.includes('apply') || cls.includes('insight') ||
                                cls.includes('skill') || cls.includes('people-also')) continue;

                            const text = (div.innerText || '').trim();
                            if (text.length > 200 && text.length < 15000 &&
                                isValid(text) && text.length > bestText.length) {
                                const lower = text.toLowerCase();
                                if (lower.includes('responsibilit') || lower.includes('qualificat') ||
                                    lower.includes('requirement') || lower.includes('experience') ||
                                    lower.includes('role') || lower.includes('we are') ||
                                    lower.includes('looking for') || lower.includes('job summary')) {
                                    bestText = cleanDesc(text);
                                    bestHtml = div.innerHTML || '';
                                }
                            }
                        }
                    }
                    if (bestText) {
                        return { text: bestText, html: bestHtml };
                    }

                    return { text: '', html: '' };
                }
            """)
            if desc_data:
                text = desc_data.get("text", "")
                if text and self._is_valid_description(text):
                    result["description"] = text
                    if desc_data.get("html") and len(desc_data["html"]) > 80:
                        result["description_html"] = desc_data["html"]
        except Exception as e:
            logger.debug(f"JS description extraction failed: {e}")

        return result

    async def _extract_salary_info(self) -> Dict[str, Any]:
        """Extract salary information from the job detail panel."""
        result = {}

        # Try multiple salary selectors
        salary_selectors = [
            ".jobs-unified-top-card__job-insight--highlight",
            "li.jobs-unified-top-card__job-insight span[class*='salary']",
            # Newer LinkedIn layouts
            ".job-details-preferences-and-skills .job-details-preferences-and-skills__pill",
            "[class*='salary-main-rail']",
            ".compensation__salary",
            # Salary in job insights section
            ".job-details-jobs-unified-top-card__job-insight",
        ]

        for selector in salary_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for el in elements:
                    text = (await el.text_content() or "").strip()
                    # Check if this element contains salary info
                    if any(indicator in text.lower() for indicator in [
                        "$", "₹", "lpa", "lakh", "lakhs", "salary", "yr", "month",
                        "per year", "per annum", "annual", "ctc",
                    ]) or re.search(r'\d+[,.]?\d*\s*[-–to]+\s*\d+', text):
                        salary_info = self._parse_salary(text)
                        if salary_info:
                            result.update(salary_info)
                            result["salary_text"] = text
                            return result
            except Exception:
                continue

        # JavaScript fallback: search for salary patterns in the insights area
        try:
            salary_data = await self.page.evaluate("""
                () => {
                    const insights = document.querySelectorAll(
                        '.jobs-unified-top-card__job-insight, ' +
                        '.job-details-jobs-unified-top-card__job-insight, ' +
                        '[class*="job-insight"], ' +
                        '.job-details-preferences-and-skills__pill'
                    );
                    for (const el of insights) {
                        const text = el.textContent || '';
                        if (/[$₹]|lpa|lakh|salary|\\d+[,.]?\\d*\\s*[-–to]+\\s*\\d+/i.test(text)) {
                            return text.trim();
                        }
                    }
                    return '';
                }
            """)
            if salary_data:
                salary_info = self._parse_salary(salary_data)
                if salary_info:
                    result.update(salary_info)
                    result["salary_text"] = salary_data
        except Exception:
            pass

        return result

    async def _extract_job_metadata(self) -> Dict[str, Any]:
        """Extract job type, experience level, and other metadata from the detail panel."""
        result = {}

        insights = await self.page.query_selector_all(
            ".jobs-unified-top-card__job-insight, "
            "li.jobs-unified-top-card__job-insight, "
            ".job-details-jobs-unified-top-card__job-insight, "
            "li[class*='job-insight'], "
            ".job-details-preferences-and-skills__pill"
        )

        for insight in insights:
            try:
                text = (await insight.text_content() or "").strip().lower()

                # Job type
                if "full-time" in text:
                    result["job_type"] = "full-time"
                elif "part-time" in text:
                    result["job_type"] = "part-time"
                elif "contract" in text:
                    result["job_type"] = "contract"
                elif "internship" in text:
                    result["job_type"] = "internship"
                elif "temporary" in text:
                    result["job_type"] = "temporary"

                # Experience level
                if "entry level" in text or "entry-level" in text:
                    result["experience_level"] = "entry_level"
                elif "associate" in text:
                    result["experience_level"] = "associate"
                elif "mid-senior" in text or "mid senior" in text:
                    result["experience_level"] = "mid_senior"
                elif "director" in text:
                    result["experience_level"] = "director"
                elif "executive" in text:
                    result["experience_level"] = "executive"
                elif "internship" in text:
                    result["experience_level"] = "internship"

                # Employee count / company size
                if "employees" in text:
                    result["company_size"] = text.strip()

            except Exception:
                continue

        # Extract from the skills/preferences section (newer LinkedIn layout)
        try:
            skill_pills = await self.page.query_selector_all(
                ".job-details-preferences-and-skills .job-details-preferences-and-skills__pill, "
                "[class*='how-you-match'] [class*='pill'], "
                "[class*='skill-match'] [class*='skill-name']"
            )
            linkedin_skills = []
            for pill in skill_pills:
                text = (await pill.text_content() or "").strip()
                if text and len(text) < 50:
                    linkedin_skills.append(text)
            if linkedin_skills:
                result["linkedin_skills"] = linkedin_skills
        except Exception:
            pass

        # Extract from the structured job criteria list (bottom of job page)
        # This contains: Seniority level, Employment type, Job function, Industries
        try:
            criteria_items = await self.page.query_selector_all(
                "li.description__job-criteria-item, "
                "li[class*='job-criteria-item']"
            )
            for item in criteria_items:
                header_el = await item.query_selector(
                    "h3.description__job-criteria-subheader, h3[class*='subheader']"
                )
                value_el = await item.query_selector(
                    "span.description__job-criteria-text, span[class*='criteria-text']"
                )
                if header_el and value_el:
                    header = (await header_el.text_content() or "").strip().lower()
                    value = (await value_el.text_content() or "").strip()

                    if "seniority" in header:
                        # Map LinkedIn seniority labels to our experience levels
                        val_lower = value.lower()
                        if "entry" in val_lower:
                            result.setdefault("experience_level", "entry_level")
                        elif "associate" in val_lower:
                            result.setdefault("experience_level", "associate")
                        elif "mid-senior" in val_lower or "mid senior" in val_lower:
                            result.setdefault("experience_level", "mid_senior")
                        elif "director" in val_lower:
                            result.setdefault("experience_level", "director")
                        elif "executive" in val_lower:
                            result.setdefault("experience_level", "executive")
                        elif "internship" in val_lower:
                            result.setdefault("experience_level", "internship")

                    elif "employment" in header or "type" in header:
                        val_lower = value.lower()
                        if "full" in val_lower:
                            result.setdefault("job_type", "full-time")
                        elif "part" in val_lower:
                            result.setdefault("job_type", "part-time")
                        elif "contract" in val_lower:
                            result.setdefault("job_type", "contract")
                        elif "internship" in val_lower:
                            result.setdefault("job_type", "internship")

                    elif "industri" in header:
                        result.setdefault("company_industry", value)

        except Exception:
            pass

        return result

    async def _extract_job_details(self, card: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Click on a job card and extract full details from the side panel.
        """
        job_id = card.get("external_id", "")
        if not job_id:
            return None

        # Click on the job card to load details in side panel
        try:
            card_selector = f'[data-job-id="{job_id}"], a[href*="/jobs/view/{job_id}"]'
            clicked = await self.safe_click(card_selector, timeout=5000)
            if not clicked:
                # Try navigating directly
                return await self._extract_job_from_page(card)

            await self.random_delay(1.5, 3.0)

            # Wait for job details panel to load
            detail_selectors = [
                ".jobs-details", ".job-details", ".jobs-unified-top-card",
                ".scaffold-layout__detail", "[class*='jobs-details']",
                "[class*='job-details']",
                ".job-details-jobs-unified-top-card",
            ]
            detail_found = False
            for sel in detail_selectors:
                try:
                    await self.page.wait_for_selector(sel, timeout=5000)
                    detail_found = True
                    break
                except Exception:
                    continue

            if not detail_found:
                logger.debug(f"Job detail panel not found for {job_id}, trying direct page")
                return await self._extract_job_from_page(card)

        except Exception as e:
            logger.debug(f"Failed to load job details for {job_id}: {e}")
            return card  # Return basic card info

        # Extract full details
        details = {**card, "platform": "linkedin"}

        try:
            # Full title
            title_el = await self.page.query_selector(
                ".jobs-unified-top-card__job-title, "
                ".job-details-jobs-unified-top-card__job-title, "
                "h2.t-24, "
                "h1[class*='job-title'], "
                ".job-details-jobs-unified-top-card__job-title a"
            )
            if title_el:
                # Use inner_text() to avoid duplicated accessibility text
                raw_title = (await title_el.inner_text() or "").strip()
                details["title"] = self._dedup_title(raw_title)

            # Company name (from detail view)
            company_selectors = [
                ".job-details-jobs-unified-top-card__company-name a",
                ".job-details-jobs-unified-top-card__company-name",
                ".jobs-unified-top-card__company-name a",
                ".jobs-unified-top-card__company-name",
                "[class*='company-name'] a",
                "[class*='company-name']",
            ]
            for comp_sel in company_selectors:
                company_el = await self.page.query_selector(comp_sel)
                if company_el:
                    comp_text = (await company_el.inner_text() or "").strip()
                    if comp_text and len(comp_text) > 1:
                        details["company"] = comp_text
                        break

            # Location (from detail view)
            location_el = await self.page.query_selector(
                ".jobs-unified-top-card__bullet, "
                ".job-details-jobs-unified-top-card__bullet, "
                ".jobs-unified-top-card__workplace-type, "
                "[class*='top-card'] [class*='bullet']"
            )
            if location_el:
                details["location"] = (await location_el.inner_text() or "").strip()

            # Full job description (with See More handling)
            desc_data = await self._extract_full_description()
            if desc_data.get("description") and self._is_valid_description(desc_data["description"]):
                details["description"] = desc_data["description"]
                if desc_data.get("description_html"):
                    details["description_html"] = desc_data["description_html"]

            # If we still don't have a proper description, try navigating to the full page
            if not self._is_valid_description(details.get("description", "")):
                logger.info(f"Bad/short description for {job_id}, trying full page extraction")
                full_page_data = await self._extract_job_from_page(details)
                if full_page_data and self._is_valid_description(full_page_data.get("description", "")):
                    details["description"] = full_page_data["description"]
                    if full_page_data.get("description_html"):
                        details["description_html"] = full_page_data["description_html"]

            # Posted time
            time_el = await self.page.query_selector(
                ".jobs-unified-top-card__posted-date, "
                "span[class*='posted-time'], "
                ".job-details-jobs-unified-top-card__posted-date"
            )
            if time_el:
                details["posted_text"] = (await time_el.text_content() or "").strip()

            # Number of applicants
            applicants_el = await self.page.query_selector(
                ".jobs-unified-top-card__applicant-count, "
                "span[class*='applicant-count'], "
                ".job-details-jobs-unified-top-card__applicant-count"
            )
            if applicants_el:
                applicants_text = (await applicants_el.text_content() or "").strip()
                applicant_match = re.search(r"(\d+)", applicants_text.replace(",", ""))
                if applicant_match:
                    details["applicant_count"] = int(applicant_match.group(1))

            # Extract salary
            salary_data = await self._extract_salary_info()
            if salary_data:
                details.update(salary_data)

            # Extract skills from description
            details["skills"] = self._extract_skills(details.get("description", ""))

            # Also merge LinkedIn's own skill pills if available
            metadata = await self._extract_job_metadata()
            if metadata.get("linkedin_skills"):
                existing_skills = set(s.lower() for s in details.get("skills", []))
                for skill in metadata["linkedin_skills"]:
                    if skill.lower() not in existing_skills:
                        details.setdefault("skills", []).append(skill)

            # Merge metadata (job_type, experience_level, company_size)
            for key in ["job_type", "experience_level", "company_size"]:
                if metadata.get(key) and not details.get(key):
                    details[key] = metadata[key]

            # Easy Apply status from detail view
            easy_apply_btn = await self.page.query_selector(
                ".jobs-apply-button--top-card, "
                "button[class*='jobs-apply-button'], "
                "button[aria-label*='Easy Apply']"
            )
            if easy_apply_btn:
                btn_text = (await easy_apply_btn.text_content() or "").lower()
                details["easy_apply"] = "easy apply" in btn_text

            # Extract work arrangement
            location_str = details.get("location", "").lower()
            if "remote" in location_str:
                details["work_arrangement"] = "remote"
                details["is_remote"] = True
            elif "hybrid" in location_str:
                details["work_arrangement"] = "hybrid"
            else:
                details["work_arrangement"] = "on-site"

        except Exception as e:
            logger.warning(f"Error extracting details for job {job_id}: {e}")

        return details

    async def _extract_job_from_page(self, card: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Navigate to job page directly and extract full details."""
        url = card.get("url", "")
        if not url:
            return card

        try:
            await self.page.goto(url, wait_until="domcontentloaded")
            await self.random_delay(2.0, 4.0)

            # Wait for the description to load
            try:
                await self.page.wait_for_selector(
                    "#job-details, .jobs-description__content, .description__text, "
                    ".job-details-about-the-job-module__description",
                    timeout=10000,
                )
            except Exception:
                pass

            details = {**card, "platform": "linkedin"}

            # Take a debug screenshot on first job
            job_id = card.get("external_id", "unknown")
            await self.take_screenshot(f"linkedin_job_page_{job_id}")

            # Extract company from the full page view
            company_selectors = [
                ".job-details-jobs-unified-top-card__company-name a",
                ".job-details-jobs-unified-top-card__company-name",
                ".jobs-unified-top-card__company-name a",
                ".jobs-unified-top-card__company-name",
                ".topcard__org-name-link",
                ".top-card-layout__card a[data-tracking-control-name*='company']",
                "[class*='company-name'] a",
                "[class*='company-name']",
            ]
            for sel in company_selectors:
                try:
                    el = await self.page.query_selector(sel)
                    if el:
                        text = (await el.text_content() or "").strip()
                        if text and len(text) > 1:
                            details["company"] = text
                            break
                except Exception:
                    continue

            # If still no company, try JS extraction
            if not details.get("company"):
                try:
                    company = await self.page.evaluate("""
                        () => {
                            // Strategy 1: Try the structured data (LD+JSON)
                            const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                            for (const ld of scripts) {
                                try {
                                    const data = JSON.parse(ld.textContent);
                                    if (data.hiringOrganization && data.hiringOrganization.name) {
                                        return data.hiringOrganization.name;
                                    }
                                } catch(e) {}
                            }

                            // Strategy 2: Company link near the top of the page
                            const companyLinks = document.querySelectorAll('a[href*="/company/"]');
                            for (const link of companyLinks) {
                                const t = link.textContent.trim();
                                // Company names are short, visible text (not URLs or long text)
                                if (t.length > 1 && t.length < 80 && !t.includes('/')) return t;
                            }

                            // Strategy 3: Look for company name in the job header area
                            // LinkedIn puts it near the job title at the top
                            const topCard = document.querySelector(
                                '[class*="top-card"], [class*="topcard"], [class*="job-details-jobs"]'
                            );
                            if (topCard) {
                                const links = topCard.querySelectorAll('a');
                                for (const a of links) {
                                    const href = a.getAttribute('href') || '';
                                    if (href.includes('/company/')) {
                                        return a.textContent.trim();
                                    }
                                }
                            }
                            return '';
                        }
                    """)
                    if company:
                        details["company"] = company
                except Exception:
                    pass

            # Click "See more" to expand full description
            await self._click_show_more_description()
            await self.random_delay(0.5, 1.0)

            # Extract description
            desc_data = await self._extract_full_description()
            if desc_data.get("description") and self._is_valid_description(desc_data["description"]):
                details["description"] = desc_data["description"]
                if desc_data.get("description_html"):
                    details["description_html"] = desc_data["description_html"]

            # If description still bad, try page's own innerText on specific containers
            if not self._is_valid_description(details.get("description", "")):
                logger.info(f"Full page also failed for {job_id}, trying broader extraction")
                await self.take_screenshot(f"linkedin_no_desc_{job_id}")
                try:
                    desc = await self.page.evaluate("""
                        () => {
                            // Get text from article or main content area only
                            const containers = [
                                document.querySelector('#job-details'),
                                document.querySelector('.jobs-description__content'),
                                document.querySelector('.jobs-box__html-content'),
                                document.querySelector('article'),
                            ];
                            for (const el of containers) {
                                if (el) {
                                    const text = el.innerText.trim();
                                    if (text.length > 80) return text;
                                }
                            }
                            return '';
                        }
                    """)
                    if desc and self._is_valid_description(desc):
                        if desc.lower().startswith("about the job"):
                            desc = desc[len("about the job"):].strip()
                        details["description"] = desc
                except Exception:
                    pass

            # Extract skills from description
            details["skills"] = self._extract_skills(details.get("description", ""))

            # Extract metadata
            metadata = await self._extract_job_metadata()
            for key in ["job_type", "experience_level", "company_size"]:
                if metadata.get(key):
                    details[key] = metadata[key]
            if metadata.get("linkedin_skills"):
                existing = set(s.lower() for s in details.get("skills", []))
                for skill in metadata["linkedin_skills"]:
                    if skill.lower() not in existing:
                        details.setdefault("skills", []).append(skill)

            # Extract salary
            salary_data = await self._extract_salary_info()
            if salary_data:
                details.update(salary_data)

            return details

        except Exception as e:
            logger.debug(f"Failed to extract from page: {e}")
            return card

    def _parse_salary(self, salary_text: str) -> Optional[Dict[str, Any]]:
        """Parse salary text into min/max values."""
        if not salary_text:
            return None

        # Match patterns like "$100,000 - $150,000", "10L - 15L", "10-15 LPA"
        patterns = [
            # USD format: $100,000 - $150,000
            r"\$[\s]*([\d,]+)[\s]*[-to]+[\s]*\$[\s]*([\d,]+)",
            # INR LPA format: 10 - 15 LPA or 10L - 15L
            r"([\d.]+)[\s]*[L]?[\s]*[-to]+[\s]*([\d.]+)[\s]*(?:LPA|L|Lakhs?)",
            # Generic: 100000 - 150000
            r"([\d,]+)[\s]*[-to]+[\s]*([\d,]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, salary_text, re.IGNORECASE)
            if match:
                try:
                    min_val = float(match.group(1).replace(",", ""))
                    max_val = float(match.group(2).replace(",", ""))
                    return {"salary_min": min_val, "salary_max": max_val}
                except (ValueError, IndexError):
                    continue

        return None

    async def scrape_recommended_jobs(self, max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Scrape LinkedIn's 'Jobs for you' / recommended jobs section.
        These are jobs LinkedIn has already matched based on the user's profile.
        """
        if not self._is_logged_in:
            logger.error("Not logged in to LinkedIn")
            return []

        logger.info("Scraping LinkedIn recommended jobs")
        recommended_urls = [
            "https://www.linkedin.com/jobs/collections/recommended/",
            "https://www.linkedin.com/jobs/",
        ]

        all_jobs = []
        seen_ids = set()

        for url in recommended_urls:
            try:
                await self.page.goto(url, wait_until="domcontentloaded")
                await self.random_delay(3.0, 5.0)

                # Scroll to load more recommended jobs
                for _ in range(3):
                    await self.page.evaluate("window.scrollBy(0, 500)")
                    await asyncio.sleep(random.uniform(0.5, 1.0))

                # Extract job cards from the recommended section
                job_cards = await self._extract_job_cards()
                if job_cards:
                    logger.info(f"Found {len(job_cards)} recommended jobs from {url}")
                    for card in job_cards[:max_jobs - len(all_jobs)]:
                        eid = card.get("external_id", "")
                        if eid in seen_ids:
                            continue
                        try:
                            details = await self._extract_job_details(card)
                            if details:
                                seen_ids.add(eid)
                                details["is_recommended"] = True
                                all_jobs.append(details)
                        except Exception as e:
                            logger.debug(f"Failed to extract recommended job {eid}: {e}")

                        # Navigate back if we left the recommended page
                        if "/jobs/view/" in self.page.url:
                            try:
                                await self.page.goto(url, wait_until="domcontentloaded")
                                await self.random_delay(2.0, 3.0)
                            except Exception:
                                break

                        await self.random_delay(1.0, 2.0)

                if len(all_jobs) >= max_jobs:
                    break

            except Exception as e:
                logger.debug(f"Failed to scrape recommended jobs from {url}: {e}")
                continue

        logger.info(f"Total recommended jobs found: {len(all_jobs)}")
        return all_jobs

    def _extract_skills(self, description: str) -> List[str]:
        """Extract skills/technologies from job description as a list."""
        if not description:
            return []

        skill_keywords = [
            "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust",
            "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI",
            "Spring", "Express", "Next.js", "Svelte",
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
            "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
            "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
            "REST API", "GraphQL", "Microservices", "CI/CD",
            "Git", "Linux", "Agile", "Scrum",
            "SQL", "NoSQL", "HTML", "CSS", "SASS",
            "Figma", "Photoshop", "UI/UX",
            "Data Science", "Data Engineering", "ETL",
            "Spark", "Hadoop", "Kafka", "Airflow",
            "Selenium", "Playwright", "Cypress",
            "Jenkins", "GitHub Actions", "CircleCI",
            "Prometheus", "Grafana", "ELK",
            "Swift", "Kotlin", "Flutter", "React Native",
            "Ruby", "Rails", "PHP", "Laravel",
            ".NET", "Unity", "Tableau", "Power BI",
            "Snowflake", "Databricks", "BigQuery",
            "RabbitMQ", "gRPC", "WebSocket",
        ]

        found_skills = []
        desc_lower = description.lower()
        for skill in skill_keywords:
            if skill.lower() in desc_lower:
                found_skills.append(skill)

        return found_skills[:20]
