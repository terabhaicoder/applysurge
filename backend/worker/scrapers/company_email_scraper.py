"""
Company email scraper that finds contact information from company websites.

Strategies:
1. Crawl /about, /team, /careers, /contact pages for emails
2. Extract team member names and titles from team pages
3. Cross-reference with LinkedIn for hiring managers/founders/CTOs
4. Use Hunter.io domain search as fallback
5. Prioritize: hiring manager > CTO > founder > HR

Returns structured contact data with confidence scores.
"""

import asyncio
import hashlib
import logging
import os
import random
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)


@dataclass
class ContactInfo:
    """Represents a discovered contact at a company."""
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    source: str = "unknown"  # team_page, about_page, hunter, linkedin, contact_page
    confidence_score: float = 0.0
    is_primary: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CompanyEmailResult:
    """Result from scraping a company for contacts."""
    company_name: str
    company_website: str
    contacts: List[ContactInfo] = field(default_factory=list)
    generic_emails: List[str] = field(default_factory=list)  # info@, careers@, etc.
    best_contact: Optional[ContactInfo] = None
    pages_crawled: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["best_contact"] = self.best_contact.to_dict() if self.best_contact else None
        return result


class CompanyEmailScraper:
    """
    Scrapes company websites and external sources to find contact emails.
    Uses Playwright with stealth mode for web scraping.
    """

    # Pages to crawl on company websites
    TEAM_PATHS = [
        "/about", "/about-us", "/team", "/our-team", "/people",
        "/leadership", "/about/team", "/company/team", "/who-we-are",
    ]
    CONTACT_PATHS = [
        "/contact", "/contact-us", "/get-in-touch", "/reach-out",
    ]
    CAREERS_PATHS = [
        "/careers", "/jobs", "/join-us", "/join", "/work-with-us",
        "/hiring", "/opportunities", "/open-positions",
    ]

    # Title priority for outreach (higher = better)
    TITLE_PRIORITY = {
        "hiring manager": 100,
        "head of talent": 95,
        "talent acquisition": 90,
        "recruiter": 85,
        "head of people": 80,
        "vp of engineering": 78,
        "cto": 75,
        "chief technology officer": 75,
        "engineering manager": 72,
        "head of engineering": 70,
        "co-founder": 65,
        "founder": 65,
        "ceo": 60,
        "chief executive": 60,
        "coo": 55,
        "vp": 50,
        "director of engineering": 50,
        "head of product": 45,
        "hr": 40,
        "human resources": 40,
        "people operations": 40,
    }

    # Email patterns to avoid
    GENERIC_EMAIL_PREFIXES = [
        "info", "hello", "contact", "support", "help", "sales",
        "admin", "team", "careers", "jobs", "hr", "press",
        "media", "partnerships", "legal", "privacy", "noreply",
        "no-reply", "newsletter", "subscribe", "feedback",
    ]

    EMAIL_REGEX = re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
        re.IGNORECASE,
    )

    STEALTH_JS = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    window.chrome = {runtime: {}};
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    ]

    def __init__(self, hunter_api_key: Optional[str] = None):
        self.hunter_api_key = hunter_api_key or os.environ.get("HUNTER_API_KEY", "")
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def _random_delay(self, min_sec: float = 0.5, max_sec: float = 2.0) -> None:
        """Human-like random delay."""
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    async def _setup_browser(self) -> None:
        """Initialize Playwright with stealth configuration."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        self.context = await self.browser.new_context(
            user_agent=random.choice(self.USER_AGENTS),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            java_script_enabled=True,
        )
        await self.context.add_init_script(self.STEALTH_JS)

    async def _teardown_browser(self) -> None:
        """Close browser and cleanup resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    def _extract_emails_from_text(self, text: str, domain: str) -> List[str]:
        """Extract email addresses from text, prioritizing company domain emails."""
        emails = self.EMAIL_REGEX.findall(text)
        # Filter out obviously fake/example emails
        filtered = []
        for email in emails:
            email_lower = email.lower()
            if any(x in email_lower for x in ["example.com", "test.com", "placeholder", "email.com", "domain.com"]):
                continue
            if len(email) > 254:  # RFC 5321 max length
                continue
            filtered.append(email.lower())
        return list(set(filtered))

    def _is_generic_email(self, email: str) -> bool:
        """Check if an email is a generic/team address."""
        local_part = email.split("@")[0].lower()
        return any(local_part.startswith(prefix) for prefix in self.GENERIC_EMAIL_PREFIXES)

    def _calculate_title_priority(self, title: str) -> int:
        """Calculate priority score based on job title."""
        title_lower = title.lower().strip()
        for pattern, score in self.TITLE_PRIORITY.items():
            if pattern in title_lower:
                return score
        return 10  # Default low priority

    def _extract_name_title_pairs(self, text: str) -> List[Tuple[str, str]]:
        """Extract name and title pairs from text content."""
        pairs = []

        # Common patterns for team pages
        # Pattern: "Name - Title" or "Name | Title" or "Name, Title"
        name_title_pattern = re.compile(
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s*[-|,]\s*"
            r"([A-Za-z\s&/]+(?:Officer|Manager|Director|Lead|Head|VP|Engineer|Designer|Founder|CEO|CTO|COO|CFO|CMO|CRO|HR|Recruiter|Talent)[A-Za-z\s]*)",
            re.MULTILINE,
        )

        for match in name_title_pattern.finditer(text):
            name = match.group(1).strip()
            title = match.group(2).strip()
            if len(name) > 3 and len(title) > 2:
                pairs.append((name, title))

        return pairs

    def _guess_email_from_name(self, name: str, domain: str) -> List[str]:
        """Generate possible email addresses from a name and domain."""
        parts = name.lower().strip().split()
        if len(parts) < 2:
            return []

        first = parts[0]
        last = parts[-1]

        # Remove non-alpha chars
        first = re.sub(r"[^a-z]", "", first)
        last = re.sub(r"[^a-z]", "", last)

        if not first or not last:
            return []

        patterns = [
            f"{first}@{domain}",
            f"{first}.{last}@{domain}",
            f"{first}{last}@{domain}",
            f"{first[0]}{last}@{domain}",
            f"{first}_{last}@{domain}",
            f"{first[0]}.{last}@{domain}",
            f"{last}@{domain}",
        ]
        return patterns

    async def _crawl_page(self, page: Page, url: str) -> Optional[str]:
        """Crawl a single page and return its text content."""
        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            if not response or response.status >= 400:
                return None
            await self._random_delay(0.5, 1.5)
            content = await page.content()
            # Also get visible text
            text = await page.evaluate("() => document.body.innerText")
            return f"{content}\n{text}"
        except Exception as e:
            logger.debug(f"Error crawling {url}: {e}")
            return None

    async def _crawl_company_pages(
        self, company_website: str
    ) -> Dict[str, str]:
        """Crawl key pages on the company website."""
        results: Dict[str, str] = {}
        page: Optional[Page] = None

        try:
            page = await self.context.new_page()

            # First, crawl the homepage
            homepage_content = await self._crawl_page(page, company_website)
            if homepage_content:
                results["homepage"] = homepage_content

            # Crawl team/about pages
            all_paths = self.TEAM_PATHS + self.CONTACT_PATHS + self.CAREERS_PATHS
            for path in all_paths:
                url = urljoin(company_website, path)
                content = await self._crawl_page(page, url)
                if content and len(content) > 200:
                    results[path] = content
                    await self._random_delay(0.5, 1.5)

                # Stop if we have enough pages
                if len(results) >= 8:
                    break

        except Exception as e:
            logger.error(f"Error crawling company pages for {company_website}: {e}")
        finally:
            if page:
                await page.close()

        return results

    async def _search_hunter_io(self, domain: str) -> List[ContactInfo]:
        """
        Search Hunter.io for email addresses at a domain.
        Requires HUNTER_API_KEY environment variable.
        """
        contacts: List[ContactInfo] = []

        if not self.hunter_api_key:
            logger.debug("Hunter.io API key not configured, skipping")
            return contacts

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://api.hunter.io/v2/domain-search",
                    params={
                        "domain": domain,
                        "api_key": self.hunter_api_key,
                        "limit": 10,
                        "type": "personal",
                    },
                )

                if response.status_code != 200:
                    logger.warning(f"Hunter.io API returned {response.status_code}")
                    return contacts

                data = response.json()
                emails_data = data.get("data", {}).get("emails", [])

                for email_entry in emails_data:
                    email = email_entry.get("value", "")
                    if not email or self._is_generic_email(email):
                        continue

                    first_name = email_entry.get("first_name", "")
                    last_name = email_entry.get("last_name", "")
                    name = f"{first_name} {last_name}".strip() if first_name or last_name else None
                    position = email_entry.get("position", "")
                    confidence = email_entry.get("confidence", 50) / 100.0
                    linkedin = email_entry.get("linkedin", "")

                    contact = ContactInfo(
                        name=name,
                        title=position if position else None,
                        email=email,
                        linkedin_url=linkedin if linkedin else None,
                        source="hunter",
                        confidence_score=confidence,
                    )
                    contacts.append(contact)

        except Exception as e:
            logger.error(f"Error querying Hunter.io for {domain}: {e}")

        return contacts

    async def _search_linkedin_for_contacts(
        self, company_name: str, target_titles: Optional[List[str]] = None
    ) -> List[ContactInfo]:
        """
        Search LinkedIn for people at the company with relevant titles.
        """
        contacts: List[ContactInfo] = []
        page: Optional[Page] = None

        if target_titles is None:
            target_titles = ["CTO", "Founder", "Engineering Manager", "Head of Engineering", "Hiring Manager"]

        try:
            page = await self.context.new_page()

            for title in target_titles[:3]:
                search_query = f"{title} {company_name}"
                url = f"https://www.linkedin.com/search/results/people/?keywords={search_query.replace(' ', '%20')}"

                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                await self._random_delay(2.0, 4.0)

                # Check for auth wall
                auth_wall = await page.query_selector("[class*='join-form'], [class*='auth-wall'], [class*='login']")
                if auth_wall:
                    logger.warning("LinkedIn requires authentication for people search")
                    break

                # Extract results
                result_cards = await page.query_selector_all("[class*='entity-result'], [class*='search-result']")

                for card in result_cards[:3]:
                    try:
                        name_el = await card.query_selector("[class*='title'] span, h3 span")
                        name = await name_el.inner_text() if name_el else None
                        if not name or name == "LinkedIn Member":
                            continue

                        title_el = await card.query_selector("[class*='subtitle'], [class*='headline']")
                        person_title = await title_el.inner_text() if title_el else None

                        # Verify this person is at the right company
                        if person_title and company_name.lower() not in person_title.lower():
                            # Check secondary subtitle
                            company_el = await card.query_selector("[class*='secondary-subtitle']")
                            company_text = await company_el.inner_text() if company_el else ""
                            if company_name.lower() not in company_text.lower():
                                continue

                        link_el = await card.query_selector("a[href*='/in/']")
                        linkedin_url = None
                        if link_el:
                            linkedin_url = await link_el.get_attribute("href")

                        contact = ContactInfo(
                            name=name.strip(),
                            title=person_title.strip() if person_title else title,
                            linkedin_url=linkedin_url,
                            source="linkedin",
                            confidence_score=0.6,
                        )
                        contacts.append(contact)

                    except Exception as card_err:
                        logger.debug(f"Error parsing LinkedIn result: {card_err}")
                        continue

                await self._random_delay(2.0, 4.0)

        except Exception as e:
            logger.error(f"Error searching LinkedIn for {company_name}: {e}")
        finally:
            if page:
                await page.close()

        return contacts

    def _select_best_contact(self, contacts: List[ContactInfo]) -> Optional[ContactInfo]:
        """
        Select the best contact to reach out to based on:
        1. Title priority (hiring manager > CTO > founder > HR)
        2. Has email address
        3. Confidence score
        """
        if not contacts:
            return None

        scored_contacts = []
        for contact in contacts:
            score = 0.0

            # Title priority
            if contact.title:
                title_score = self._calculate_title_priority(contact.title) / 100.0
                score += title_score * 0.5

            # Has email
            if contact.email:
                score += 0.3

            # Confidence
            score += contact.confidence_score * 0.2

            scored_contacts.append((score, contact))

        # Sort by score descending
        scored_contacts.sort(key=lambda x: x[0], reverse=True)
        best = scored_contacts[0][1]
        best.is_primary = True
        return best

    async def scrape_company_contacts(
        self,
        company_name: str,
        company_website: str,
        search_linkedin: bool = True,
        use_hunter: bool = True,
    ) -> CompanyEmailResult:
        """
        Comprehensive scraping of a company's website and external sources
        to find the best contact for outreach.

        Args:
            company_name: Name of the company.
            company_website: Company website URL.
            search_linkedin: Whether to search LinkedIn for contacts.
            use_hunter: Whether to use Hunter.io as fallback.

        Returns:
            CompanyEmailResult with all discovered contacts and best contact.
        """
        result = CompanyEmailResult(
            company_name=company_name,
            company_website=company_website,
        )

        # Normalize website URL
        if not company_website.startswith("http"):
            company_website = f"https://{company_website}"

        parsed_url = urlparse(company_website)
        domain = parsed_url.netloc
        if domain.startswith("www."):
            domain = domain[4:]

        try:
            await self._setup_browser()

            # Step 1: Crawl company website pages
            logger.info(f"Crawling company website: {company_website}")
            page_contents = await self._crawl_company_pages(company_website)
            result.pages_crawled = list(page_contents.keys())

            all_emails: Set[str] = set()
            name_title_pairs: List[Tuple[str, str]] = []

            for page_path, content in page_contents.items():
                # Extract emails
                emails = self._extract_emails_from_text(content, domain)
                all_emails.update(emails)

                # Extract name-title pairs
                pairs = self._extract_name_title_pairs(content)
                name_title_pairs.extend(pairs)

            # Classify emails as generic or personal
            for email in all_emails:
                if self._is_generic_email(email):
                    result.generic_emails.append(email)
                else:
                    # Try to match with name-title pairs
                    email_local = email.split("@")[0]
                    matched = False
                    for name, title in name_title_pairs:
                        name_parts = name.lower().split()
                        if any(part in email_local.lower() for part in name_parts if len(part) > 2):
                            contact = ContactInfo(
                                name=name,
                                title=title,
                                email=email,
                                source="team_page",
                                confidence_score=0.85,
                            )
                            result.contacts.append(contact)
                            matched = True
                            break

                    if not matched:
                        contact = ContactInfo(
                            email=email,
                            source="website",
                            confidence_score=0.5,
                        )
                        result.contacts.append(contact)

            # Step 2: Create contacts from name-title pairs without emails
            for name, title in name_title_pairs:
                # Check if already found with email
                already_found = any(
                    c.name and c.name.lower() == name.lower()
                    for c in result.contacts
                )
                if not already_found:
                    # Generate guessed emails
                    guessed_emails = self._guess_email_from_name(name, domain)
                    contact = ContactInfo(
                        name=name,
                        title=title,
                        email=guessed_emails[0] if guessed_emails else None,
                        source="team_page",
                        confidence_score=0.4,  # Lower confidence for guessed emails
                    )
                    result.contacts.append(contact)

            # Step 3: Hunter.io fallback
            if use_hunter and (not result.contacts or all(c.confidence_score < 0.7 for c in result.contacts)):
                logger.info(f"Using Hunter.io for domain: {domain}")
                hunter_contacts = await self._search_hunter_io(domain)
                for hc in hunter_contacts:
                    # Check for duplicates
                    is_dup = any(
                        c.email and c.email == hc.email
                        for c in result.contacts
                    )
                    if not is_dup:
                        result.contacts.append(hc)

            # Step 4: LinkedIn search
            if search_linkedin:
                logger.info(f"Searching LinkedIn for contacts at {company_name}")
                linkedin_contacts = await self._search_linkedin_for_contacts(company_name)
                for lc in linkedin_contacts:
                    # Try to merge with existing contacts
                    merged = False
                    for existing in result.contacts:
                        if existing.name and lc.name and existing.name.lower() == lc.name.lower():
                            if not existing.linkedin_url:
                                existing.linkedin_url = lc.linkedin_url
                            if not existing.title and lc.title:
                                existing.title = lc.title
                            existing.confidence_score = max(existing.confidence_score, lc.confidence_score)
                            merged = True
                            break
                    if not merged:
                        result.contacts.append(lc)

            # Step 5: Select best contact
            result.best_contact = self._select_best_contact(result.contacts)

            if result.best_contact:
                logger.info(
                    f"Best contact for {company_name}: "
                    f"{result.best_contact.name} ({result.best_contact.title}) "
                    f"- {result.best_contact.email} "
                    f"[confidence: {result.best_contact.confidence_score:.2f}]"
                )
            else:
                logger.warning(f"No suitable contact found for {company_name}")

        except Exception as e:
            error_msg = f"Error scraping contacts for {company_name}: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
        finally:
            await self._teardown_browser()

        return result


async def scrape_company_emails(
    company_name: str,
    company_website: str,
    search_linkedin: bool = True,
    use_hunter: bool = True,
    hunter_api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    High-level function to scrape a company for contact emails.

    Args:
        company_name: Company name.
        company_website: Company website URL.
        search_linkedin: Whether to search LinkedIn.
        use_hunter: Whether to use Hunter.io.
        hunter_api_key: Optional Hunter.io API key override.

    Returns:
        Dictionary with contacts and best contact information.
    """
    scraper = CompanyEmailScraper(hunter_api_key=hunter_api_key)
    result = await scraper.scrape_company_contacts(
        company_name=company_name,
        company_website=company_website,
        search_linkedin=search_linkedin,
        use_hunter=use_hunter,
    )
    return result.to_dict()
