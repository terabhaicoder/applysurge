"""
Company information scraper.

Scrapes company websites and public pages to gather information
for personalized cover letters and cold emails.
"""

import asyncio
import logging
import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse, urljoin

from worker.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class CompanyScraper(BaseScraper):
    """Scrapes company information from websites and public pages."""

    PLATFORM = "company"
    MIN_DELAY = 1.0
    MAX_DELAY = 2.5

    async def login(self, email: str, password: str) -> bool:
        """No login needed for company scraping."""
        return True

    async def search_jobs(self, **kwargs):
        """Not applicable for company scraper."""
        raise NotImplementedError("Use dedicated scrapers for job search")

    async def scrape_company(
        self,
        company_name: str,
        company_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Scrape company information from their website and public sources.

        Args:
            company_name: Name of the company
            company_url: Optional company website URL

        Returns:
            Dict with company information
        """
        logger.info(f"Scraping company info: {company_name}")

        info = {
            "name": company_name,
            "url": company_url,
            "description": "",
            "mission": "",
            "values": [],
            "products": [],
            "industry": "",
            "size": "",
            "founded": "",
            "headquarters": "",
            "culture_notes": [],
            "recent_news": [],
            "tech_stack": [],
        }

        # Scrape company website if URL available
        if company_url:
            website_info = await self._scrape_website(company_url)
            info.update({k: v for k, v in website_info.items() if v})

        # Scrape LinkedIn company page
        linkedin_info = await self._scrape_linkedin_company(company_name)
        info.update({k: v for k, v in linkedin_info.items() if v and not info.get(k)})

        return info

    async def _scrape_website(self, url: str) -> Dict[str, Any]:
        """Scrape the company's main website."""
        info = {}

        try:
            await self.page.goto(url, wait_until="networkidle", timeout=20000)
            await self.random_delay(1.0, 2.0)

            # Get main page content
            main_text = await self.get_page_text()
            info["description"] = self._extract_description(main_text)

            # Try to find About page
            about_info = await self._scrape_about_page(url)
            if about_info:
                info.update({k: v for k, v in about_info.items() if v})

            # Try to find Careers page
            careers_info = await self._scrape_careers_page(url)
            if careers_info:
                info["culture_notes"] = careers_info.get("culture_notes", [])
                info["tech_stack"] = careers_info.get("tech_stack", [])

            # Extract meta information
            meta_info = await self._extract_meta_info()
            info.update({k: v for k, v in meta_info.items() if v and not info.get(k)})

        except Exception as e:
            logger.warning(f"Failed to scrape website {url}: {e}")

        return info

    async def _scrape_about_page(self, base_url: str) -> Optional[Dict[str, Any]]:
        """Find and scrape the company's About page."""
        about_paths = ["/about", "/about-us", "/company", "/about/", "/company/about"]
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        # Try to find about link on the page first
        about_link = await self.page.query_selector(
            'a[href*="about"], a[href*="company"], '
            'a:has-text("About"), a:has-text("Company")'
        )
        if about_link:
            href = await about_link.get_attribute("href")
            if href:
                about_paths.insert(0, href)

        for path in about_paths:
            try:
                about_url = path if path.startswith("http") else urljoin(base, path)
                response = await self.page.goto(about_url, wait_until="networkidle", timeout=10000)
                if response and response.status == 200:
                    text = await self.get_page_text()
                    if len(text) > 100:
                        return self._parse_about_content(text)
            except Exception:
                continue

        return None

    async def _scrape_careers_page(self, base_url: str) -> Optional[Dict[str, Any]]:
        """Find and scrape the company's Careers page for culture info."""
        careers_paths = ["/careers", "/jobs", "/careers/", "/join-us", "/work-with-us"]
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        for path in careers_paths:
            try:
                careers_url = urljoin(base, path)
                response = await self.page.goto(careers_url, wait_until="networkidle", timeout=10000)
                if response and response.status == 200:
                    text = await self.get_page_text()
                    if len(text) > 100:
                        return self._parse_careers_content(text)
            except Exception:
                continue

        return None

    async def _scrape_linkedin_company(self, company_name: str) -> Dict[str, Any]:
        """Scrape company info from LinkedIn."""
        info = {}

        try:
            # Search for company on LinkedIn
            search_url = (
                f"https://www.linkedin.com/company/{company_name.lower().replace(' ', '-')}/"
            )
            await self.page.goto(search_url, wait_until="networkidle", timeout=15000)
            await self.random_delay(1.5, 2.5)

            # Check if page loaded successfully
            if "Page not found" in (await self.get_page_text()):
                return info

            # Extract company details
            description_el = await self.page.query_selector(
                ".org-top-card-summary-info-list, .org-about-us-organization-description"
            )
            if description_el:
                info["description"] = (await description_el.text_content() or "").strip()

            # Industry
            industry_el = await self.page.query_selector(
                ".org-top-card-summary-info-list__info-item, "
                "[class*='industry']"
            )
            if industry_el:
                info["industry"] = (await industry_el.text_content() or "").strip()

            # Company size
            size_el = await self.page.query_selector(
                "[class*='company-size'], [class*='staffCount']"
            )
            if size_el:
                info["size"] = (await size_el.text_content() or "").strip()

            # Headquarters
            hq_el = await self.page.query_selector(
                "[class*='headquarters'], [class*='location']"
            )
            if hq_el:
                info["headquarters"] = (await hq_el.text_content() or "").strip()

        except Exception as e:
            logger.debug(f"LinkedIn company scrape failed for {company_name}: {e}")

        return info

    async def _extract_meta_info(self) -> Dict[str, Any]:
        """Extract meta description and structured data from page."""
        info = {}

        try:
            # Meta description
            meta_desc = await self.page.query_selector('meta[name="description"]')
            if meta_desc:
                content = await meta_desc.get_attribute("content")
                if content:
                    info["description"] = content.strip()

            # OG description
            og_desc = await self.page.query_selector('meta[property="og:description"]')
            if og_desc:
                content = await og_desc.get_attribute("content")
                if content and not info.get("description"):
                    info["description"] = content.strip()

            # JSON-LD structured data
            ld_scripts = await self.page.query_selector_all('script[type="application/ld+json"]')
            for script in ld_scripts:
                try:
                    import json
                    content = await script.text_content()
                    if content:
                        data = json.loads(content)
                        if isinstance(data, dict):
                            if data.get("@type") == "Organization":
                                info["founded"] = str(data.get("foundingDate", ""))
                                info["headquarters"] = data.get("address", {}).get(
                                    "addressLocality", ""
                                )
                except (json.JSONDecodeError, Exception):
                    continue

        except Exception as e:
            logger.debug(f"Meta extraction error: {e}")

        return info

    def _extract_description(self, text: str) -> str:
        """Extract a meaningful description from page text."""
        if not text:
            return ""

        # Take first meaningful paragraph (not too short, not too long)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:20]:
            if 50 < len(line) < 500:
                return line

        # Fallback: first 500 chars
        clean_text = " ".join(lines[:10])
        return clean_text[:500] if clean_text else ""

    def _parse_about_content(self, text: str) -> Dict[str, Any]:
        """Parse about page content for company information."""
        info = {}

        # Extract mission statement
        mission_patterns = [
            r"(?:our\s+)?mission[:\s]+(.{50,300})",
            r"(?:we\s+)?(?:aim|strive|believe)[:\s]+(.{50,300})",
        ]
        for pattern in mission_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info["mission"] = match.group(1).strip()
                break

        # Extract values
        values_section = re.search(
            r"(?:our\s+)?values[:\s]*(.*?)(?:\n\n|\Z)", text, re.IGNORECASE | re.DOTALL
        )
        if values_section:
            values_text = values_section.group(1)
            values = [v.strip() for v in re.split(r"[•\-\n]", values_text) if v.strip() and len(v.strip()) < 100]
            info["values"] = values[:10]

        # Extract founding info
        founded_match = re.search(r"(?:founded|established|started)\s+(?:in\s+)?(\d{4})", text, re.IGNORECASE)
        if founded_match:
            info["founded"] = founded_match.group(1)

        return info

    def _parse_careers_content(self, text: str) -> Dict[str, Any]:
        """Parse careers page for culture and tech stack info."""
        info = {"culture_notes": [], "tech_stack": []}

        # Extract culture-related phrases
        culture_patterns = [
            r"(work-life balance[^.]*\.)",
            r"(remote[^.]*flexible[^.]*\.)",
            r"(diversity[^.]*inclusion[^.]*\.)",
            r"(learning[^.]*growth[^.]*\.)",
            r"(team[^.]*collaborative[^.]*\.)",
        ]
        for pattern in culture_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info["culture_notes"].append(match.group(1).strip())

        # Extract tech stack mentions
        tech_keywords = [
            "Python", "JavaScript", "TypeScript", "React", "Angular", "Vue",
            "Node.js", "Django", "Flask", "FastAPI", "Spring", "Go", "Rust",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes",
            "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
            "Kafka", "Spark", "Terraform", "GraphQL",
        ]
        text_lower = text.lower()
        for tech in tech_keywords:
            if tech.lower() in text_lower:
                info["tech_stack"].append(tech)

        return info
