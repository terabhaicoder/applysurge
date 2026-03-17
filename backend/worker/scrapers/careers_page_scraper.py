"""
Careers page scraper that finds and extracts job listings from company websites.

Capabilities:
- Finds careers page URL (tries multiple common paths)
- Extracts open positions listed on the page
- Checks if positions match user's skills/preferences
- Identifies which team the user would fit in
- Extracts application instructions if available

Uses Playwright with stealth mode for browser automation.
"""

import asyncio
import logging
import random
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)


@dataclass
class OpenRole:
    """Represents an open position found on a careers page."""
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None  # full-time, part-time, contract
    experience_level: Optional[str] = None  # junior, mid, senior, lead
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    url: Optional[str] = None
    is_remote: bool = False
    salary_range: Optional[str] = None
    match_score: float = 0.0
    matched_skills: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CareersPageResult:
    """Result from scraping a company's careers page."""
    company_name: str
    company_website: str
    careers_page_url: Optional[str] = None
    careers_page_found: bool = False
    open_roles: List[OpenRole] = field(default_factory=list)
    matched_roles: List[OpenRole] = field(default_factory=list)
    suggested_team: Optional[str] = None
    application_instructions: Optional[str] = None
    application_email: Optional[str] = None
    has_general_application: bool = False
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "company_name": self.company_name,
            "company_website": self.company_website,
            "careers_page_url": self.careers_page_url,
            "careers_page_found": self.careers_page_found,
            "open_roles": [r.to_dict() for r in self.open_roles],
            "matched_roles": [r.to_dict() for r in self.matched_roles],
            "suggested_team": self.suggested_team,
            "application_instructions": self.application_instructions,
            "application_email": self.application_email,
            "has_general_application": self.has_general_application,
            "errors": self.errors,
        }
        return result


@dataclass
class UserSkillProfile:
    """User's skills and preferences for matching."""
    skills: List[str] = field(default_factory=list)
    desired_titles: List[str] = field(default_factory=list)
    experience_years: int = 0
    preferred_locations: List[str] = field(default_factory=list)
    remote_preferred: bool = False
    industries: List[str] = field(default_factory=list)


class CareersPageScraper:
    """
    Scrapes company careers/jobs pages to find open positions
    and match them against user skills.
    """

    CAREERS_PATHS = [
        "/careers",
        "/jobs",
        "/join-us",
        "/join",
        "/work-with-us",
        "/hiring",
        "/opportunities",
        "/open-positions",
        "/career",
        "/job-openings",
        "/vacancies",
        "/positions",
        "/work",
        "/company/careers",
        "/about/careers",
        "/team/join",
    ]

    # Common ATS platforms and their URL patterns
    ATS_PATTERNS = [
        "greenhouse.io",
        "lever.co",
        "ashbyhq.com",
        "jobs.lever.co",
        "boards.greenhouse.io",
        "apply.workable.com",
        "bamboohr.com",
        "workday.com",
        "icims.com",
        "smartrecruiters.com",
        "breezy.hr",
        "recruitee.com",
    ]

    STEALTH_JS = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    window.chrome = {runtime: {}};
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    # Department/team classification keywords
    TEAM_KEYWORDS = {
        "engineering": ["engineer", "developer", "software", "backend", "frontend", "full-stack", "fullstack", "devops", "sre", "infrastructure", "platform"],
        "product": ["product manager", "product designer", "product", "pm"],
        "design": ["designer", "ux", "ui", "design", "creative"],
        "data": ["data scientist", "data engineer", "data analyst", "machine learning", "ml", "ai"],
        "marketing": ["marketing", "growth", "seo", "content", "brand"],
        "sales": ["sales", "account executive", "business development", "bdm", "sdr"],
        "operations": ["operations", "ops", "project manager", "program manager"],
        "support": ["support", "customer success", "customer service"],
        "hr": ["hr", "people", "talent", "recruiter", "recruiting"],
        "finance": ["finance", "accounting", "controller", "cfo"],
    }

    # Experience level keywords
    EXPERIENCE_KEYWORDS = {
        "intern": ["intern", "internship", "co-op"],
        "junior": ["junior", "entry level", "entry-level", "associate", "jr", "i "],
        "mid": ["mid-level", "mid level", "intermediate", "ii "],
        "senior": ["senior", "sr", "lead", "principal", "staff", "iii"],
        "director": ["director", "vp", "vice president", "head of"],
        "executive": ["chief", "c-level", "cto", "ceo", "coo", "cfo"],
    }

    def __init__(self, user_profile: Optional[UserSkillProfile] = None):
        self.user_profile = user_profile or UserSkillProfile()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def _random_delay(self, min_sec: float = 0.5, max_sec: float = 2.0) -> None:
        """Human-like random delay."""
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    async def _setup_browser(self) -> None:
        """Initialize Playwright browser with stealth settings."""
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
        """Close browser and cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    async def _find_careers_page(self, page: Page, base_url: str) -> Optional[str]:
        """
        Find the careers page URL by trying common paths and looking for links.
        """
        # Strategy 1: Try common paths directly
        for path in self.CAREERS_PATHS:
            url = urljoin(base_url, path)
            try:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=10000)
                if response and response.status == 200:
                    # Verify it's actually a careers page
                    content = await page.content()
                    content_lower = content.lower()
                    if any(kw in content_lower for kw in ["career", "job", "position", "hiring", "join us", "open role", "we're hiring"]):
                        logger.info(f"Found careers page at: {url}")
                        return url
            except Exception:
                continue
            await self._random_delay(0.3, 0.8)

        # Strategy 2: Look for careers link on the homepage
        try:
            await page.goto(base_url, wait_until="domcontentloaded", timeout=15000)
            await self._random_delay(1.0, 2.0)

            # Find links with careers-related text
            links = await page.query_selector_all("a")
            for link in links:
                try:
                    text = await link.inner_text()
                    href = await link.get_attribute("href")
                    if not text or not href:
                        continue
                    text_lower = text.lower().strip()
                    if any(kw in text_lower for kw in ["career", "jobs", "join us", "we're hiring", "work with us", "open positions"]):
                        careers_url = urljoin(base_url, href)
                        logger.info(f"Found careers link on homepage: {careers_url}")
                        return careers_url
                except Exception:
                    continue

            # Strategy 3: Check for ATS platform links
            all_links = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href]'))
                    .map(a => a.href)
                    .filter(href => href.includes('greenhouse') || href.includes('lever') ||
                                   href.includes('ashby') || href.includes('workable') ||
                                   href.includes('bamboo') || href.includes('breezy'))
            """)
            if all_links:
                logger.info(f"Found ATS link: {all_links[0]}")
                return all_links[0]

        except Exception as e:
            logger.debug(f"Error finding careers link on homepage: {e}")

        # Strategy 4: Check the footer
        try:
            footer_links = await page.query_selector_all("footer a, [class*='footer'] a")
            for link in footer_links:
                try:
                    text = await link.inner_text()
                    href = await link.get_attribute("href")
                    if text and href:
                        if any(kw in text.lower() for kw in ["career", "jobs", "hiring"]):
                            return urljoin(base_url, href)
                except Exception:
                    continue
        except Exception:
            pass

        return None

    async def _extract_roles_from_page(self, page: Page, careers_url: str) -> List[OpenRole]:
        """Extract job listings from a careers page."""
        roles: List[OpenRole] = []

        try:
            await page.goto(careers_url, wait_until="networkidle", timeout=20000)
            await self._random_delay(1.0, 2.5)

            # Scroll to load dynamic content
            for _ in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self._random_delay(0.5, 1.0)

            # Strategy 1: Look for structured job listings (common patterns)
            job_selectors = [
                "[class*='job-listing']",
                "[class*='job-post']",
                "[class*='position']",
                "[class*='opening']",
                "[class*='vacancy']",
                "[class*='career-item']",
                "[class*='role-item']",
                "[data-testid*='job']",
                "li[class*='job']",
                "div[class*='job']",
                "[class*='JobPost']",
                "[class*='job_post']",
            ]

            job_elements = []
            for selector in job_selectors:
                elements = await page.query_selector_all(selector)
                if elements and len(elements) > 1:
                    job_elements = elements
                    break

            if job_elements:
                for el in job_elements[:50]:  # Limit to 50 roles
                    role = await self._parse_job_element(el, careers_url)
                    if role:
                        roles.append(role)
            else:
                # Strategy 2: Parse links that look like job postings
                links = await page.query_selector_all("a[href]")
                seen_titles: Set[str] = set()

                for link in links:
                    try:
                        text = await link.inner_text()
                        href = await link.get_attribute("href")
                        if not text or not href or len(text.strip()) < 5:
                            continue

                        text = text.strip()
                        if len(text) > 100:
                            continue

                        # Check if it looks like a job title
                        if self._looks_like_job_title(text) and text.lower() not in seen_titles:
                            seen_titles.add(text.lower())
                            role = OpenRole(
                                title=text,
                                url=urljoin(careers_url, href),
                            )
                            roles.append(role)
                    except Exception:
                        continue

            # Strategy 3: Check for Greenhouse/Lever embeds
            if not roles:
                iframes = await page.query_selector_all("iframe[src*='greenhouse'], iframe[src*='lever'], iframe[src*='ashby']")
                for iframe in iframes:
                    src = await iframe.get_attribute("src")
                    if src:
                        try:
                            frame_page = await self.context.new_page()
                            await frame_page.goto(src, wait_until="domcontentloaded", timeout=15000)
                            await self._random_delay(1.0, 2.0)

                            frame_roles = await self._extract_ats_roles(frame_page, src)
                            roles.extend(frame_roles)
                            await frame_page.close()
                        except Exception as frame_err:
                            logger.debug(f"Error loading ATS iframe: {frame_err}")

            # Enrich roles with details if we have few enough
            if roles and len(roles) <= 20:
                for role in roles[:10]:
                    if role.url:
                        await self._enrich_role_details(page, role)
                        await self._random_delay(0.5, 1.5)

        except Exception as e:
            logger.error(f"Error extracting roles from {careers_url}: {e}")

        return roles

    async def _parse_job_element(self, element, base_url: str) -> Optional[OpenRole]:
        """Parse a job listing element into an OpenRole."""
        try:
            # Extract title
            title_el = await element.query_selector("h2, h3, h4, a, [class*='title'], [class*='name']")
            title = await title_el.inner_text() if title_el else None
            if not title or len(title.strip()) < 3:
                return None
            title = title.strip()

            # Extract link
            link_el = await element.query_selector("a[href]")
            url = None
            if link_el:
                href = await link_el.get_attribute("href")
                url = urljoin(base_url, href) if href else None

            # Extract department
            dept_el = await element.query_selector("[class*='department'], [class*='team'], [class*='category']")
            department = await dept_el.inner_text() if dept_el else None

            # Extract location
            loc_el = await element.query_selector("[class*='location'], [class*='place']")
            location = await loc_el.inner_text() if loc_el else None

            # Extract employment type
            type_el = await element.query_selector("[class*='type'], [class*='commitment']")
            emp_type = await type_el.inner_text() if type_el else None

            # Determine experience level
            experience_level = self._determine_experience_level(title)

            # Check remote
            is_remote = False
            if location:
                is_remote = any(kw in location.lower() for kw in ["remote", "anywhere", "distributed"])
            if "remote" in title.lower():
                is_remote = True

            # Normalize employment type
            if emp_type:
                emp_type = self._normalize_employment_type(emp_type)

            return OpenRole(
                title=title,
                department=department.strip() if department else self._determine_department(title),
                location=location.strip() if location else None,
                employment_type=emp_type,
                experience_level=experience_level,
                url=url,
                is_remote=is_remote,
            )

        except Exception as e:
            logger.debug(f"Error parsing job element: {e}")
            return None

    async def _extract_ats_roles(self, page: Page, ats_url: str) -> List[OpenRole]:
        """Extract roles from a common ATS platform page."""
        roles: List[OpenRole] = []

        try:
            # Greenhouse format
            if "greenhouse" in ats_url:
                sections = await page.query_selector_all("section.level-0, [class*='opening']")
                for section in sections:
                    department_el = await section.query_selector("h2, h3")
                    department = await department_el.inner_text() if department_el else None

                    job_links = await section.query_selector_all("a[data-mapped='true'], a.opening-title, div.opening a")
                    for link in job_links:
                        title = await link.inner_text()
                        href = await link.get_attribute("href")
                        if title and title.strip():
                            roles.append(OpenRole(
                                title=title.strip(),
                                department=department.strip() if department else None,
                                url=urljoin(ats_url, href) if href else None,
                                experience_level=self._determine_experience_level(title),
                            ))

            # Lever format
            elif "lever" in ats_url:
                postings = await page.query_selector_all("[class*='posting'], .posting")
                for posting in postings:
                    title_el = await posting.query_selector("h5, [data-qa='posting-name'], .posting-title")
                    title = await title_el.inner_text() if title_el else None
                    if not title:
                        continue

                    loc_el = await posting.query_selector("[class*='location'], .posting-categories .location")
                    location = await loc_el.inner_text() if loc_el else None

                    dept_el = await posting.query_selector("[class*='department'], .posting-categories .department")
                    department = await dept_el.inner_text() if dept_el else None

                    link_el = await posting.query_selector("a[href]")
                    href = await link_el.get_attribute("href") if link_el else None

                    roles.append(OpenRole(
                        title=title.strip(),
                        department=department.strip() if department else None,
                        location=location.strip() if location else None,
                        url=urljoin(ats_url, href) if href else None,
                        experience_level=self._determine_experience_level(title),
                    ))

            # Ashby format
            elif "ashby" in ats_url:
                job_cards = await page.query_selector_all("[class*='ashby-job'], [class*='job-posting']")
                for card in job_cards:
                    title_el = await card.query_selector("h3, [class*='title']")
                    title = await title_el.inner_text() if title_el else None
                    if not title:
                        continue

                    loc_el = await card.query_selector("[class*='location']")
                    location = await loc_el.inner_text() if loc_el else None

                    link_el = await card.query_selector("a[href]")
                    href = await link_el.get_attribute("href") if link_el else None

                    roles.append(OpenRole(
                        title=title.strip(),
                        location=location.strip() if location else None,
                        url=urljoin(ats_url, href) if href else None,
                        experience_level=self._determine_experience_level(title),
                    ))

        except Exception as e:
            logger.error(f"Error extracting roles from ATS: {e}")

        return roles

    async def _enrich_role_details(self, page: Page, role: OpenRole) -> None:
        """Visit a role's detail page to extract more information."""
        if not role.url:
            return

        try:
            detail_page = await self.context.new_page()
            await detail_page.goto(role.url, wait_until="domcontentloaded", timeout=15000)
            await self._random_delay(0.5, 1.5)

            # Extract description
            desc_el = await detail_page.query_selector(
                "[class*='description'], [class*='content'], [class*='body'], article, main"
            )
            if desc_el:
                desc_text = await desc_el.inner_text()
                role.description = desc_text.strip()[:1000]

                # Extract requirements from description
                role.requirements = self._extract_requirements(desc_text)

                # Extract salary if mentioned
                role.salary_range = self._extract_salary(desc_text)

                # Determine employment type if not set
                if not role.employment_type:
                    role.employment_type = self._extract_employment_type(desc_text)

                # Check for remote
                if not role.is_remote:
                    role.is_remote = any(kw in desc_text.lower() for kw in ["remote", "work from home", "distributed team"])

            await detail_page.close()

        except Exception as e:
            logger.debug(f"Error enriching role details for {role.url}: {e}")

    def _extract_requirements(self, text: str) -> Optional[List[str]]:
        """Extract requirements/qualifications from job description."""
        requirements = []
        lines = text.split("\n")
        in_requirements = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if we're in a requirements section
            if any(kw in line.lower() for kw in ["requirement", "qualification", "what you'll need", "you have", "must have", "you bring"]):
                in_requirements = True
                continue

            if in_requirements:
                # Check for section end
                if any(kw in line.lower() for kw in ["nice to have", "bonus", "benefit", "what we offer", "perks", "about us"]):
                    break

                # Extract bullet points
                if line.startswith(("-", "*", "•", "·")) or re.match(r"^\d+\.", line):
                    req = re.sub(r"^[-*•·\d.]\s*", "", line).strip()
                    if len(req) > 10:
                        requirements.append(req)

        return requirements if requirements else None

    def _extract_salary(self, text: str) -> Optional[str]:
        """Extract salary range from job description text."""
        salary_patterns = [
            r"\$[\d,]+\s*[-–]\s*\$[\d,]+",
            r"\$[\d,]+k?\s*[-–]\s*\$[\d,]+k?",
            r"[\d,]+\s*[-–]\s*[\d,]+\s*(?:USD|EUR|GBP)",
            r"salary[:\s]+\$?[\d,]+\s*[-–]\s*\$?[\d,]+",
        ]
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def _extract_employment_type(self, text: str) -> Optional[str]:
        """Extract employment type from text."""
        text_lower = text.lower()
        if "full-time" in text_lower or "full time" in text_lower:
            return "full-time"
        elif "part-time" in text_lower or "part time" in text_lower:
            return "part-time"
        elif "contract" in text_lower:
            return "contract"
        elif "freelance" in text_lower:
            return "freelance"
        elif "intern" in text_lower:
            return "internship"
        return None

    def _looks_like_job_title(self, text: str) -> bool:
        """Determine if text looks like a job title."""
        text_lower = text.lower().strip()

        # Too short or too long
        if len(text_lower) < 5 or len(text_lower) > 80:
            return False

        # Contains job-related keywords
        job_keywords = [
            "engineer", "developer", "designer", "manager", "director",
            "analyst", "specialist", "coordinator", "lead", "head",
            "architect", "scientist", "researcher", "consultant",
            "administrator", "associate", "intern", "officer",
            "strategist", "writer", "marketer", "recruiter",
        ]
        return any(kw in text_lower for kw in job_keywords)

    def _determine_experience_level(self, title: str) -> Optional[str]:
        """Determine experience level from job title."""
        title_lower = title.lower()
        for level, keywords in self.EXPERIENCE_KEYWORDS.items():
            if any(kw in title_lower for kw in keywords):
                return level
        return "mid"  # Default to mid-level

    def _determine_department(self, title: str) -> Optional[str]:
        """Determine department from job title."""
        title_lower = title.lower()
        for dept, keywords in self.TEAM_KEYWORDS.items():
            if any(kw in title_lower for kw in keywords):
                return dept
        return None

    def _normalize_employment_type(self, type_text: str) -> str:
        """Normalize employment type text."""
        type_lower = type_text.lower().strip()
        if "full" in type_lower:
            return "full-time"
        elif "part" in type_lower:
            return "part-time"
        elif "contract" in type_lower:
            return "contract"
        elif "freelance" in type_lower:
            return "freelance"
        elif "intern" in type_lower:
            return "internship"
        return type_text.strip()

    def _calculate_match_score(self, role: OpenRole) -> float:
        """
        Calculate how well a role matches the user's profile.
        Returns a score from 0.0 to 1.0.
        """
        if not self.user_profile:
            return 0.0

        score = 0.0
        total_weight = 0.0

        # Title match (weight: 0.3)
        if self.user_profile.desired_titles and role.title:
            title_lower = role.title.lower()
            for desired in self.user_profile.desired_titles:
                if desired.lower() in title_lower or title_lower in desired.lower():
                    score += 0.3
                    break
                # Partial match
                desired_words = set(desired.lower().split())
                title_words = set(title_lower.split())
                overlap = desired_words & title_words
                if overlap:
                    score += 0.3 * (len(overlap) / max(len(desired_words), len(title_words)))
                    break
            total_weight += 0.3

        # Skills match (weight: 0.35)
        if self.user_profile.skills and role.requirements:
            matched_skills = []
            for skill in self.user_profile.skills:
                for req in role.requirements:
                    if skill.lower() in req.lower():
                        matched_skills.append(skill)
                        break
            if matched_skills:
                score += 0.35 * (len(matched_skills) / len(self.user_profile.skills))
                role.matched_skills = matched_skills
            total_weight += 0.35
        elif self.user_profile.skills and role.description:
            matched_skills = []
            desc_lower = role.description.lower()
            for skill in self.user_profile.skills:
                if skill.lower() in desc_lower:
                    matched_skills.append(skill)
            if matched_skills:
                score += 0.35 * (len(matched_skills) / len(self.user_profile.skills))
                role.matched_skills = matched_skills
            total_weight += 0.35

        # Location match (weight: 0.15)
        if self.user_profile.preferred_locations and role.location:
            loc_lower = role.location.lower()
            for pref_loc in self.user_profile.preferred_locations:
                if pref_loc.lower() in loc_lower:
                    score += 0.15
                    break
            total_weight += 0.15

        # Remote preference (weight: 0.1)
        if self.user_profile.remote_preferred and role.is_remote:
            score += 0.1
        total_weight += 0.1

        # Experience level match (weight: 0.1)
        if role.experience_level:
            expected_level = self._expected_experience_level()
            if role.experience_level == expected_level:
                score += 0.1
            elif abs(self._level_to_num(role.experience_level) - self._level_to_num(expected_level)) <= 1:
                score += 0.05
            total_weight += 0.1

        return min(score / max(total_weight, 0.01), 1.0)

    def _expected_experience_level(self) -> str:
        """Determine expected experience level from years of experience."""
        years = self.user_profile.experience_years
        if years <= 1:
            return "junior"
        elif years <= 4:
            return "mid"
        elif years <= 8:
            return "senior"
        else:
            return "director"

    def _level_to_num(self, level: str) -> int:
        """Convert experience level to numeric value."""
        levels = {"intern": 0, "junior": 1, "mid": 2, "senior": 3, "director": 4, "executive": 5}
        return levels.get(level, 2)

    def _determine_suggested_team(self, roles: List[OpenRole]) -> Optional[str]:
        """
        Based on matched roles and user skills, suggest which team
        the user would best fit in.
        """
        if not self.user_profile.skills:
            return None

        # Count department occurrences in matched roles
        dept_scores: Dict[str, float] = {}
        for role in roles:
            dept = role.department or self._determine_department(role.title)
            if dept:
                dept_scores[dept] = dept_scores.get(dept, 0) + role.match_score

        # Also check user skills against team keywords
        for dept, keywords in self.TEAM_KEYWORDS.items():
            for skill in self.user_profile.skills:
                if skill.lower() in keywords or any(kw in skill.lower() for kw in keywords):
                    dept_scores[dept] = dept_scores.get(dept, 0) + 0.5

        if dept_scores:
            best_dept = max(dept_scores, key=dept_scores.get)
            return best_dept

        return None

    def _extract_application_instructions(self, page_content: str) -> Optional[str]:
        """Extract application instructions from page content."""
        instruction_keywords = [
            "how to apply",
            "to apply",
            "application process",
            "apply by",
            "send your resume",
            "send your cv",
            "submit your",
            "apply now",
            "interested? ",
        ]

        lines = page_content.split("\n")
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            if any(kw in line_lower for kw in instruction_keywords):
                # Capture this line and the next few
                instructions = []
                for j in range(i, min(i + 5, len(lines))):
                    if lines[j].strip():
                        instructions.append(lines[j].strip())
                if instructions:
                    return "\n".join(instructions)

        return None

    async def scrape_careers_page(
        self,
        company_name: str,
        company_website: str,
        user_profile: Optional[UserSkillProfile] = None,
    ) -> CareersPageResult:
        """
        Scrape a company's careers page for open positions.

        Args:
            company_name: Company name.
            company_website: Company website URL.
            user_profile: Optional user skill profile for matching.

        Returns:
            CareersPageResult with open roles and match information.
        """
        if user_profile:
            self.user_profile = user_profile

        result = CareersPageResult(
            company_name=company_name,
            company_website=company_website,
        )

        # Normalize URL
        if not company_website.startswith("http"):
            company_website = f"https://{company_website}"

        try:
            await self._setup_browser()
            page = await self.context.new_page()

            # Step 1: Find the careers page
            careers_url = await self._find_careers_page(page, company_website)
            if careers_url:
                result.careers_page_url = careers_url
                result.careers_page_found = True
            else:
                logger.info(f"No careers page found for {company_name}")
                result.careers_page_found = False
                await page.close()
                return result

            # Step 2: Extract open roles
            roles = await self._extract_roles_from_page(page, careers_url)
            result.open_roles = roles
            logger.info(f"Found {len(roles)} open roles at {company_name}")

            # Step 3: Calculate match scores and find matched roles
            for role in roles:
                role.match_score = self._calculate_match_score(role)

            result.matched_roles = [r for r in roles if r.match_score >= 0.3]
            result.matched_roles.sort(key=lambda r: r.match_score, reverse=True)

            # Step 4: Suggest team
            result.suggested_team = self._determine_suggested_team(roles)

            # Step 5: Extract application instructions
            careers_content = await page.evaluate("() => document.body.innerText")
            result.application_instructions = self._extract_application_instructions(careers_content)

            # Check for general application form
            general_apply = await page.query_selector(
                "a[href*='general'], a[href*='spontaneous'], [class*='general-application']"
            )
            if general_apply:
                result.has_general_application = True

            # Check for application email
            email_pattern = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
            email_matches = email_pattern.findall(careers_content)
            for email in email_matches:
                if any(kw in email.lower() for kw in ["career", "job", "hiring", "recruit", "talent", "apply"]):
                    result.application_email = email
                    break

            await page.close()

        except Exception as e:
            error_msg = f"Error scraping careers page for {company_name}: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
        finally:
            await self._teardown_browser()

        return result


async def scrape_careers_page(
    company_name: str,
    company_website: str,
    user_skills: Optional[List[str]] = None,
    desired_titles: Optional[List[str]] = None,
    experience_years: int = 0,
    preferred_locations: Optional[List[str]] = None,
    remote_preferred: bool = False,
) -> Dict[str, Any]:
    """
    High-level function to scrape a company's careers page.

    Args:
        company_name: Company name.
        company_website: Company website URL.
        user_skills: List of user's skills.
        desired_titles: List of desired job titles.
        experience_years: Years of experience.
        preferred_locations: Preferred work locations.
        remote_preferred: Whether remote work is preferred.

    Returns:
        Dictionary with careers page results.
    """
    user_profile = UserSkillProfile(
        skills=user_skills or [],
        desired_titles=desired_titles or [],
        experience_years=experience_years,
        preferred_locations=preferred_locations or [],
        remote_preferred=remote_preferred,
    )

    scraper = CareersPageScraper(user_profile=user_profile)
    result = await scraper.scrape_careers_page(
        company_name=company_name,
        company_website=company_website,
    )
    return result.to_dict()
