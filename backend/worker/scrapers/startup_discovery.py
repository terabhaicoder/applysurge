"""
Startup discovery scraper that finds startups from multiple sources.

Sources:
- Y Combinator startup directory
- Product Hunt recently launched startups
- LinkedIn company pages
- AngelList/Wellfound startup listings

Uses Playwright with stealth mode and human-like delays.
"""

import asyncio
import hashlib
import json
import logging
import random
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredStartup:
    """Represents a discovered startup from any source."""
    company_name: str
    company_website: Optional[str] = None
    company_industry: Optional[str] = None
    company_description: Optional[str] = None
    company_size: Optional[str] = None
    company_location: Optional[str] = None
    company_tech_stack: Optional[List[str]] = None
    funding_stage: Optional[str] = None
    funding_amount: Optional[str] = None
    discovery_source: Optional[str] = None
    discovery_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    @property
    def unique_key(self) -> str:
        """Generate a unique key for deduplication."""
        name_clean = self.company_name.lower().strip()
        domain = ""
        if self.company_website:
            parsed = urlparse(self.company_website)
            domain = parsed.netloc or parsed.path
        return hashlib.md5(f"{name_clean}:{domain}".encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DiscoveryFilters:
    """Filters for startup discovery."""
    industries: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    company_sizes: Optional[List[str]] = None
    funding_stages: Optional[List[str]] = None
    tech_stacks: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    excluded_companies: Optional[List[str]] = None
    max_results: int = 50


class StartupDiscoveryScraper:
    """
    Discovers startups from multiple sources using Playwright.
    Implements stealth browsing with human-like delays.
    """

    STEALTH_JS = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    window.chrome = {runtime: {}};
    Object.defineProperty(navigator, 'permissions', {
        get: () => ({query: (params) => Promise.resolve({state: 'granted'})}),
    });
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    def __init__(self, filters: Optional[DiscoveryFilters] = None):
        self.filters = filters or DiscoveryFilters()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.discovered: List[DiscoveredStartup] = []
        self.seen_keys: Set[str] = set()

    async def _random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0) -> None:
        """Human-like random delay between actions."""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    async def _setup_browser(self) -> None:
        """Initialize Playwright browser with stealth settings."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        user_agent = random.choice(self.USER_AGENTS)
        self.context = await self.browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
            java_script_enabled=True,
        )
        await self.context.add_init_script(self.STEALTH_JS)

    async def _teardown_browser(self) -> None:
        """Close browser and cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    def _matches_filters(self, startup: DiscoveredStartup) -> bool:
        """Check if a discovered startup matches the configured filters."""
        if self.filters.excluded_companies:
            excluded_lower = [c.lower() for c in self.filters.excluded_companies]
            if startup.company_name.lower() in excluded_lower:
                return False

        if self.filters.industries and startup.company_industry:
            industry_lower = startup.company_industry.lower()
            if not any(ind.lower() in industry_lower for ind in self.filters.industries):
                return False

        if self.filters.locations and startup.company_location:
            location_lower = startup.company_location.lower()
            if not any(loc.lower() in location_lower for loc in self.filters.locations):
                return False

        if self.filters.company_sizes and startup.company_size:
            if startup.company_size not in self.filters.company_sizes:
                return False

        if self.filters.funding_stages and startup.funding_stage:
            if startup.funding_stage not in self.filters.funding_stages:
                return False

        if self.filters.tech_stacks and startup.company_tech_stack:
            stack_lower = [t.lower() for t in startup.company_tech_stack]
            if not any(tech.lower() in stack_lower for tech in self.filters.tech_stacks):
                return False

        if self.filters.keywords:
            search_text = f"{startup.company_name} {startup.company_description or ''} {startup.company_industry or ''}".lower()
            if not any(kw.lower() in search_text for kw in self.filters.keywords):
                return False

        return True

    def _add_startup(self, startup: DiscoveredStartup) -> bool:
        """Add a startup to results if it passes filters and dedup."""
        if len(self.discovered) >= self.filters.max_results:
            return False

        key = startup.unique_key
        if key in self.seen_keys:
            return False

        if not self._matches_filters(startup):
            return False

        self.seen_keys.add(key)
        self.discovered.append(startup)
        logger.info(f"Discovered startup: {startup.company_name} from {startup.discovery_source}")
        return True

    async def scrape_yc_directory(self) -> List[DiscoveredStartup]:
        """
        Scrape Y Combinator's startup directory.
        URL: https://www.ycombinator.com/companies
        """
        results: List[DiscoveredStartup] = []
        page: Optional[Page] = None

        try:
            page = await self.context.new_page()
            base_url = "https://www.ycombinator.com/companies"

            # Build query params based on filters
            params = []
            if self.filters.industries:
                for industry in self.filters.industries:
                    params.append(f"industry={industry.replace(' ', '+')}")
            if self.filters.locations:
                for location in self.filters.locations:
                    params.append(f"regions={location.replace(' ', '+')}")

            url = base_url
            if params:
                url += "?" + "&".join(params)

            logger.info(f"Scraping YC directory: {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await self._random_delay(2.0, 4.0)

            # Scroll to load more companies
            for _ in range(5):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self._random_delay(1.5, 3.0)

            # Extract company cards
            company_links = await page.query_selector_all("a[class*='company']")
            if not company_links:
                # Try alternative selectors
                company_links = await page.query_selector_all("[class*='CompanyCard'], [class*='company-card']")

            for link in company_links[:self.filters.max_results]:
                try:
                    name_el = await link.query_selector("span[class*='name'], h4, .company-name")
                    name = await name_el.inner_text() if name_el else None
                    if not name:
                        name = await link.get_attribute("aria-label") or ""
                        name = name.replace("Company: ", "").strip()

                    if not name:
                        continue

                    desc_el = await link.query_selector("span[class*='description'], .company-description, p")
                    description = await desc_el.inner_text() if desc_el else None

                    location_el = await link.query_selector("span[class*='location'], .company-location")
                    location = await location_el.inner_text() if location_el else None

                    industry_el = await link.query_selector("span[class*='industry'], .pill, .tag")
                    industry = await industry_el.inner_text() if industry_el else None

                    size_el = await link.query_selector("span[class*='size'], span[class*='team']")
                    size = await size_el.inner_text() if size_el else None

                    href = await link.get_attribute("href")
                    company_url = urljoin("https://www.ycombinator.com", href) if href else None

                    startup = DiscoveredStartup(
                        company_name=name.strip(),
                        company_website=None,  # Will be resolved from company page
                        company_industry=industry.strip() if industry else None,
                        company_description=description.strip() if description else None,
                        company_size=size.strip() if size else None,
                        company_location=location.strip() if location else None,
                        discovery_source="yc_directory",
                        discovery_url=company_url,
                        tags=["yc"],
                    )

                    # Visit company page to get website URL
                    if company_url and len(results) < 30:
                        try:
                            detail_page = await self.context.new_page()
                            await detail_page.goto(company_url, wait_until="domcontentloaded", timeout=15000)
                            await self._random_delay(1.0, 2.0)

                            # Extract website link
                            website_link = await detail_page.query_selector("a[href*='://'][target='_blank'], a[class*='website']")
                            if website_link:
                                website_href = await website_link.get_attribute("href")
                                if website_href and "ycombinator.com" not in website_href:
                                    startup.company_website = website_href

                            # Extract batch/funding info
                            batch_el = await detail_page.query_selector("span[class*='batch'], .yc-batch")
                            if batch_el:
                                batch_text = await batch_el.inner_text()
                                startup.funding_stage = f"yc_{batch_text.strip().lower()}"

                            # Extract tech stack from description
                            full_desc_el = await detail_page.query_selector("[class*='prose'], [class*='description']")
                            if full_desc_el:
                                full_desc = await full_desc_el.inner_text()
                                startup.company_description = full_desc.strip()[:500]
                                startup.company_tech_stack = self._extract_tech_stack(full_desc)

                            await detail_page.close()
                        except Exception as detail_err:
                            logger.debug(f"Could not load YC detail page: {detail_err}")
                            if detail_page:
                                await detail_page.close()

                    if self._add_startup(startup):
                        results.append(startup)

                except Exception as card_err:
                    logger.debug(f"Error parsing YC company card: {card_err}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping YC directory: {e}")
        finally:
            if page:
                await page.close()

        logger.info(f"YC directory: discovered {len(results)} startups")
        return results

    async def scrape_product_hunt(self) -> List[DiscoveredStartup]:
        """
        Scrape Product Hunt for recently launched startups.
        Focuses on startups with significant upvotes.
        """
        results: List[DiscoveredStartup] = []
        page: Optional[Page] = None

        try:
            page = await self.context.new_page()
            url = "https://www.producthunt.com/leaderboard/daily"

            logger.info(f"Scraping Product Hunt: {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await self._random_delay(2.0, 4.0)

            # Scroll to load more products
            for _ in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self._random_delay(1.5, 2.5)

            # Extract product listings
            product_items = await page.query_selector_all("[data-test*='post'], [class*='post-item'], section[class*='styles_item']")
            if not product_items:
                product_items = await page.query_selector_all("main a[href*='/posts/']")

            for item in product_items[:self.filters.max_results]:
                try:
                    # Extract product name
                    name_el = await item.query_selector("h3, [class*='title'], [data-test*='name']")
                    name = await name_el.inner_text() if name_el else None
                    if not name:
                        continue

                    # Extract tagline/description
                    desc_el = await item.query_selector("p, [class*='tagline'], [data-test*='tagline']")
                    description = await desc_el.inner_text() if desc_el else None

                    # Extract topics/categories
                    topic_els = await item.query_selector_all("[class*='topic'], [class*='tag'], [class*='category']")
                    topics = []
                    for t_el in topic_els:
                        topic = await t_el.inner_text()
                        if topic:
                            topics.append(topic.strip())

                    # Extract product link
                    link_el = await item.query_selector("a[href*='/posts/']")
                    product_url = None
                    if link_el:
                        href = await link_el.get_attribute("href")
                        product_url = urljoin("https://www.producthunt.com", href) if href else None

                    # Determine industry from topics
                    industry = topics[0] if topics else "Technology"

                    startup = DiscoveredStartup(
                        company_name=name.strip(),
                        company_industry=industry,
                        company_description=description.strip() if description else None,
                        discovery_source="product_hunt",
                        discovery_url=product_url,
                        tags=["product_hunt"] + topics[:3],
                    )

                    # Visit product page to get website
                    if product_url and len(results) < 25:
                        try:
                            detail_page = await self.context.new_page()
                            await detail_page.goto(product_url, wait_until="domcontentloaded", timeout=15000)
                            await self._random_delay(1.0, 2.5)

                            # Find external website link
                            visit_btn = await detail_page.query_selector("a[href*='://'][rel*='nofollow'], a[class*='visit'], a[data-test*='visit']")
                            if visit_btn:
                                website = await visit_btn.get_attribute("href")
                                if website and "producthunt.com" not in website:
                                    startup.company_website = website

                            # Get more details from the page
                            full_desc_el = await detail_page.query_selector("[class*='description'], [class*='about']")
                            if full_desc_el:
                                full_desc = await full_desc_el.inner_text()
                                startup.company_description = full_desc.strip()[:500]

                            await detail_page.close()
                        except Exception as detail_err:
                            logger.debug(f"Could not load PH detail page: {detail_err}")
                            if detail_page:
                                await detail_page.close()

                    if self._add_startup(startup):
                        results.append(startup)

                except Exception as item_err:
                    logger.debug(f"Error parsing Product Hunt item: {item_err}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping Product Hunt: {e}")
        finally:
            if page:
                await page.close()

        logger.info(f"Product Hunt: discovered {len(results)} startups")
        return results

    async def scrape_linkedin_companies(self) -> List[DiscoveredStartup]:
        """
        Scrape LinkedIn for startup companies in user's industry.
        Searches for companies with startup indicators.
        """
        results: List[DiscoveredStartup] = []
        page: Optional[Page] = None

        try:
            page = await self.context.new_page()

            # Build search queries based on filters
            search_terms = []
            if self.filters.industries:
                search_terms.extend(self.filters.industries)
            if self.filters.keywords:
                search_terms.extend(self.filters.keywords)
            if not search_terms:
                search_terms = ["startup", "technology"]

            for term in search_terms[:3]:  # Limit to 3 searches
                search_query = f"{term} startup"
                url = f"https://www.linkedin.com/search/results/companies/?keywords={search_query.replace(' ', '%20')}&companySize=B,C,D"

                logger.info(f"Scraping LinkedIn companies: {search_query}")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await self._random_delay(3.0, 5.0)

                # Check if logged in, handle auth wall
                login_wall = await page.query_selector("[class*='join-form'], [class*='auth-wall']")
                if login_wall:
                    logger.warning("LinkedIn requires authentication, skipping")
                    break

                # Extract company results
                company_cards = await page.query_selector_all("[class*='entity-result'], [class*='search-result']")

                for card in company_cards[:15]:
                    try:
                        name_el = await card.query_selector("[class*='entity-result__title'] span, h3 span")
                        name = await name_el.inner_text() if name_el else None
                        if not name:
                            continue

                        # Clean up name
                        name = name.strip()
                        if not name or name == "LinkedIn Member":
                            continue

                        desc_el = await card.query_selector("[class*='entity-result__summary'], p[class*='snippet']")
                        description = await desc_el.inner_text() if desc_el else None

                        industry_el = await card.query_selector("[class*='entity-result__primary-subtitle'], [class*='subline']")
                        industry = await industry_el.inner_text() if industry_el else None

                        location_el = await card.query_selector("[class*='entity-result__secondary-subtitle']")
                        location = await location_el.inner_text() if location_el else None

                        link_el = await card.query_selector("a[href*='/company/']")
                        linkedin_url = None
                        if link_el:
                            linkedin_url = await link_el.get_attribute("href")

                        size_el = await card.query_selector("[class*='company-size'], [class*='members']")
                        size = await size_el.inner_text() if size_el else None

                        startup = DiscoveredStartup(
                            company_name=name,
                            company_industry=industry.strip() if industry else term,
                            company_description=description.strip() if description else None,
                            company_size=self._normalize_company_size(size) if size else None,
                            company_location=location.strip() if location else None,
                            discovery_source="linkedin",
                            discovery_url=linkedin_url,
                            tags=["linkedin", term],
                        )

                        if self._add_startup(startup):
                            results.append(startup)

                    except Exception as card_err:
                        logger.debug(f"Error parsing LinkedIn company card: {card_err}")
                        continue

                await self._random_delay(2.0, 4.0)

        except Exception as e:
            logger.error(f"Error scraping LinkedIn: {e}")
        finally:
            if page:
                await page.close()

        logger.info(f"LinkedIn: discovered {len(results)} startups")
        return results

    async def scrape_angellist(self) -> List[DiscoveredStartup]:
        """
        Scrape AngelList/Wellfound for startups that are hiring.
        """
        results: List[DiscoveredStartup] = []
        page: Optional[Page] = None

        try:
            page = await self.context.new_page()

            # Build URL with filters
            base_url = "https://wellfound.com/role/l/software-engineer"
            params = []
            if self.filters.locations:
                location = self.filters.locations[0].replace(" ", "-").lower()
                base_url = f"https://wellfound.com/role/l/software-engineer/{location}"

            url = base_url
            logger.info(f"Scraping Wellfound/AngelList: {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await self._random_delay(2.0, 4.0)

            # Scroll to load more
            for _ in range(4):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self._random_delay(1.5, 3.0)

            # Extract startup job listings
            job_cards = await page.query_selector_all("[class*='styles_component'], [class*='job-listing'], [data-test*='startup']")
            if not job_cards:
                job_cards = await page.query_selector_all("[class*='StartupResult'], div[class*='styles_result']")

            for card in job_cards[:self.filters.max_results]:
                try:
                    # Extract company name
                    name_el = await card.query_selector("h2, [class*='company-name'], a[class*='startup-link']")
                    name = await name_el.inner_text() if name_el else None
                    if not name:
                        continue

                    # Extract company details
                    desc_el = await card.query_selector("[class*='pitch'], [class*='tagline'], p")
                    description = await desc_el.inner_text() if desc_el else None

                    size_el = await card.query_selector("[class*='company-size'], [class*='size']")
                    size = await size_el.inner_text() if size_el else None

                    stage_el = await card.query_selector("[class*='stage'], [class*='funding']")
                    stage = await stage_el.inner_text() if stage_el else None

                    location_el = await card.query_selector("[class*='location']")
                    location = await location_el.inner_text() if location_el else None

                    # Extract company URL from the card
                    link_el = await card.query_selector("a[href*='/company/'], a[href*='wellfound.com']")
                    company_page_url = None
                    if link_el:
                        href = await link_el.get_attribute("href")
                        company_page_url = urljoin("https://wellfound.com", href) if href else None

                    # Extract tech stack tags
                    tech_els = await card.query_selector_all("[class*='skill'], [class*='technology'], [class*='tag']")
                    tech_stack = []
                    for t_el in tech_els:
                        tech = await t_el.inner_text()
                        if tech:
                            tech_stack.append(tech.strip())

                    startup = DiscoveredStartup(
                        company_name=name.strip(),
                        company_industry=self._determine_industry_from_tags(tech_stack),
                        company_description=description.strip() if description else None,
                        company_size=self._normalize_company_size(size) if size else None,
                        company_location=location.strip() if location else None,
                        company_tech_stack=tech_stack if tech_stack else None,
                        funding_stage=self._normalize_funding_stage(stage) if stage else None,
                        discovery_source="angellist",
                        discovery_url=company_page_url,
                        tags=["angellist", "hiring"],
                    )

                    # Visit company page for more details
                    if company_page_url and len(results) < 20:
                        try:
                            detail_page = await self.context.new_page()
                            await detail_page.goto(company_page_url, wait_until="domcontentloaded", timeout=15000)
                            await self._random_delay(1.0, 2.0)

                            # Get website URL
                            website_el = await detail_page.query_selector("a[href*='://'][class*='website'], a[class*='company-url']")
                            if website_el:
                                website = await website_el.get_attribute("href")
                                if website and "wellfound.com" not in website and "angel.co" not in website:
                                    startup.company_website = website

                            # Get more details
                            full_desc = await detail_page.query_selector("[class*='product-description'], [class*='about']")
                            if full_desc:
                                desc_text = await full_desc.inner_text()
                                startup.company_description = desc_text.strip()[:500]

                            await detail_page.close()
                        except Exception as detail_err:
                            logger.debug(f"Could not load Wellfound detail page: {detail_err}")
                            if detail_page:
                                await detail_page.close()

                    if self._add_startup(startup):
                        results.append(startup)

                except Exception as card_err:
                    logger.debug(f"Error parsing Wellfound card: {card_err}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping Wellfound/AngelList: {e}")
        finally:
            if page:
                await page.close()

        logger.info(f"Wellfound/AngelList: discovered {len(results)} startups")
        return results

    def _extract_tech_stack(self, text: str) -> Optional[List[str]]:
        """Extract technology stack mentions from text."""
        known_techs = [
            "Python", "JavaScript", "TypeScript", "React", "Node.js", "Go", "Rust",
            "Java", "Ruby", "PHP", "Swift", "Kotlin", "C++", "C#", "Scala",
            "Django", "Flask", "FastAPI", "Express", "Next.js", "Vue.js", "Angular",
            "PostgreSQL", "MongoDB", "Redis", "Elasticsearch", "MySQL",
            "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform",
            "GraphQL", "REST", "gRPC", "Kafka", "RabbitMQ",
            "TensorFlow", "PyTorch", "Machine Learning", "AI", "LLM",
            "React Native", "Flutter", "iOS", "Android",
        ]
        found = []
        text_lower = text.lower()
        for tech in known_techs:
            if tech.lower() in text_lower:
                found.append(tech)
        return found if found else None

    def _normalize_company_size(self, size_text: Optional[str]) -> Optional[str]:
        """Normalize company size to standard categories."""
        if not size_text:
            return None
        size_text = size_text.lower().strip()

        if any(x in size_text for x in ["1-10", "1 - 10", "< 10", "micro"]):
            return "1-10"
        elif any(x in size_text for x in ["11-50", "11 - 50", "10-50"]):
            return "11-50"
        elif any(x in size_text for x in ["51-200", "51 - 200", "50-200"]):
            return "51-200"
        elif any(x in size_text for x in ["201-500", "201 - 500", "200-500"]):
            return "201-500"
        elif any(x in size_text for x in ["501-1000", "500-1000", "501+"]):
            return "501-1000"
        elif any(x in size_text for x in ["1000+", "1001+"]):
            return "1000+"

        # Try to extract number
        numbers = re.findall(r"\d+", size_text)
        if numbers:
            n = int(numbers[0])
            if n <= 10:
                return "1-10"
            elif n <= 50:
                return "11-50"
            elif n <= 200:
                return "51-200"
            elif n <= 500:
                return "201-500"
            elif n <= 1000:
                return "501-1000"
            else:
                return "1000+"

        return size_text

    def _normalize_funding_stage(self, stage_text: Optional[str]) -> Optional[str]:
        """Normalize funding stage to standard categories."""
        if not stage_text:
            return None
        stage_lower = stage_text.lower().strip()

        stage_map = {
            "pre-seed": "pre_seed",
            "pre seed": "pre_seed",
            "seed": "seed",
            "series a": "series_a",
            "series b": "series_b",
            "series c": "series_c",
            "series d": "series_d",
            "series e": "series_e",
            "growth": "growth",
            "ipo": "ipo",
            "public": "public",
            "bootstrapped": "bootstrapped",
            "acquired": "acquired",
        }

        for key, value in stage_map.items():
            if key in stage_lower:
                return value

        return stage_text.replace(" ", "_").lower()

    def _determine_industry_from_tags(self, tags: List[str]) -> Optional[str]:
        """Determine industry from technology/skill tags."""
        industry_signals = {
            "fintech": ["finance", "banking", "payments", "fintech", "crypto", "blockchain"],
            "healthtech": ["health", "medical", "healthcare", "biotech", "pharma"],
            "edtech": ["education", "learning", "edtech", "e-learning"],
            "saas": ["saas", "b2b", "enterprise"],
            "e-commerce": ["ecommerce", "e-commerce", "retail", "marketplace"],
            "ai_ml": ["machine learning", "ai", "artificial intelligence", "nlp", "deep learning"],
            "devtools": ["developer tools", "devops", "infrastructure", "api"],
            "cybersecurity": ["security", "cybersecurity", "infosec"],
            "climate": ["climate", "cleantech", "sustainability", "energy"],
            "social": ["social", "community", "messaging", "communication"],
        }

        tags_lower = [t.lower() for t in tags]
        for industry, signals in industry_signals.items():
            for signal in signals:
                if any(signal in tag for tag in tags_lower):
                    return industry

        return "technology"

    async def discover_all(
        self,
        sources: Optional[List[str]] = None,
    ) -> List[DiscoveredStartup]:
        """
        Run discovery across all specified sources.

        Args:
            sources: List of sources to use. Options: yc, product_hunt, linkedin, angellist
                     If None, uses all sources.

        Returns:
            List of discovered startups matching filters.
        """
        if sources is None:
            sources = ["yc", "product_hunt", "linkedin", "angellist"]

        try:
            await self._setup_browser()

            tasks = []
            if "yc" in sources:
                tasks.append(("yc", self.scrape_yc_directory))
            if "product_hunt" in sources:
                tasks.append(("product_hunt", self.scrape_product_hunt))
            if "linkedin" in sources:
                tasks.append(("linkedin", self.scrape_linkedin_companies))
            if "angellist" in sources:
                tasks.append(("angellist", self.scrape_angellist))

            # Run scrapers sequentially to avoid detection
            for source_name, scraper_func in tasks:
                if len(self.discovered) >= self.filters.max_results:
                    break
                try:
                    logger.info(f"Starting discovery from: {source_name}")
                    await scraper_func()
                    await self._random_delay(3.0, 6.0)  # Delay between sources
                except Exception as e:
                    logger.error(f"Error in {source_name} scraper: {e}")
                    continue

        finally:
            await self._teardown_browser()

        logger.info(f"Total startups discovered: {len(self.discovered)}")
        return self.discovered


async def discover_startups(
    filters: Optional[DiscoveryFilters] = None,
    sources: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    High-level function to discover startups.

    Args:
        filters: Discovery filters to apply.
        sources: Sources to search.

    Returns:
        List of startup dictionaries.
    """
    scraper = StartupDiscoveryScraper(filters=filters)
    startups = await scraper.discover_all(sources=sources)
    return [s.to_dict() for s in startups]
