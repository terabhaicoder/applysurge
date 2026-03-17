"""
AI-powered company research.

Combines web scraping with AI summarization to produce actionable
company insights for personalized applications.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional

import anthropic

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")


class CompanyResearcher:
    """Researches companies using web scraping and AI summarization."""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        self.model = ANTHROPIC_MODEL

    async def research(
        self,
        company_name: str,
        company_url: Optional[str] = None,
        job_title: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Research a company combining web scraping and AI analysis.

        Args:
            company_name: Name of the company
            company_url: Optional company website URL
            job_title: Optional job title for targeted research
            user_id: Optional user ID for browser context

        Returns:
            Dict with structured company research
        """
        logger.info(f"Researching company: {company_name}")

        # Step 1: Scrape company information
        scraped_data = await self._scrape_company_data(
            company_name, company_url, user_id
        )

        # Step 2: AI summarization and analysis
        research = await self._ai_analyze(company_name, scraped_data, job_title)

        return research

    async def _scrape_company_data(
        self,
        company_name: str,
        company_url: Optional[str],
        user_id: Optional[str],
    ) -> Dict[str, Any]:
        """Scrape company data from web sources."""
        try:
            from worker.scrapers.company_scraper import CompanyScraper

            scraper = CompanyScraper(user_id=user_id or "system")
            await scraper.initialize()

            try:
                data = await scraper.scrape_company(
                    company_name=company_name,
                    company_url=company_url,
                )
                return data
            finally:
                await scraper.cleanup()

        except Exception as e:
            logger.warning(f"Company scraping failed for {company_name}: {e}")
            return {
                "name": company_name,
                "url": company_url,
                "description": "",
            }

    async def _ai_analyze(
        self,
        company_name: str,
        scraped_data: Dict[str, Any],
        job_title: Optional[str],
    ) -> Dict[str, Any]:
        """Use AI to analyze and summarize company research."""
        try:
            # Build context from scraped data
            context_parts = []
            if scraped_data.get("description"):
                context_parts.append(f"Description: {scraped_data['description']}")
            if scraped_data.get("mission"):
                context_parts.append(f"Mission: {scraped_data['mission']}")
            if scraped_data.get("values"):
                values = scraped_data["values"]
                if isinstance(values, list):
                    values = ", ".join(values)
                context_parts.append(f"Values: {values}")
            if scraped_data.get("industry"):
                context_parts.append(f"Industry: {scraped_data['industry']}")
            if scraped_data.get("size"):
                context_parts.append(f"Company Size: {scraped_data['size']}")
            if scraped_data.get("headquarters"):
                context_parts.append(f"Headquarters: {scraped_data['headquarters']}")
            if scraped_data.get("founded"):
                context_parts.append(f"Founded: {scraped_data['founded']}")
            if scraped_data.get("products"):
                products = scraped_data["products"]
                if isinstance(products, list):
                    products = ", ".join(products)
                context_parts.append(f"Products/Services: {products}")
            if scraped_data.get("culture_notes"):
                notes = scraped_data["culture_notes"]
                if isinstance(notes, list):
                    notes = "; ".join(notes)
                context_parts.append(f"Culture: {notes}")
            if scraped_data.get("tech_stack"):
                stack = scraped_data["tech_stack"]
                if isinstance(stack, list):
                    stack = ", ".join(stack)
                context_parts.append(f"Tech Stack: {stack}")

            context = "\n".join(context_parts) if context_parts else "Limited information available"

            job_context = f"\nTarget Position: {job_title}" if job_title else ""

            prompt = f"""Analyze the following company information and provide a structured research summary.

COMPANY: {company_name}
{job_context}

RAW DATA:
{context}

Provide a JSON response with these fields:
{{
    "summary": "2-3 sentence company overview",
    "industry": "primary industry/sector",
    "what_they_do": "brief description of products/services",
    "culture_keywords": ["list", "of", "culture", "keywords"],
    "talking_points": ["point relevant for cover letter/interview", "another point"],
    "potential_challenges": ["business challenge they might face"],
    "why_work_here": "compelling reason to work at this company",
    "interview_topics": ["topic to research", "another topic"],
    "competitors": ["competitor1", "competitor2"],
    "recent_focus": "what the company seems focused on currently"
}}

Respond ONLY with the JSON object, no markdown formatting or code blocks."""

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
            )

            response_text = response.content[0].text.strip()

            # Parse JSON response
            import json
            # Remove any markdown code block formatting if present
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1]
                response_text = response_text.rsplit("```", 1)[0]

            research = json.loads(response_text)

            # Merge with scraped data
            research["name"] = company_name
            research["url"] = scraped_data.get("url", "")
            research["tech_stack"] = scraped_data.get("tech_stack", [])
            research["raw_data"] = scraped_data

            logger.info(f"Company research complete for {company_name}")
            return research

        except anthropic.APIError as e:
            logger.error(f"AI analysis failed for {company_name}: {e}")
            return self._fallback_research(company_name, scraped_data)
        except Exception as e:
            logger.error(f"Company research analysis failed: {e}", exc_info=True)
            return self._fallback_research(company_name, scraped_data)

    def _fallback_research(
        self, company_name: str, scraped_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Provide fallback research when AI is unavailable."""
        return {
            "name": company_name,
            "url": scraped_data.get("url", ""),
            "summary": scraped_data.get("description", f"{company_name} - company information unavailable"),
            "industry": scraped_data.get("industry", "Unknown"),
            "what_they_do": scraped_data.get("description", "")[:200],
            "culture_keywords": scraped_data.get("values", []),
            "talking_points": [],
            "potential_challenges": [],
            "why_work_here": "",
            "interview_topics": [],
            "competitors": [],
            "recent_focus": "",
            "tech_stack": scraped_data.get("tech_stack", []),
            "raw_data": scraped_data,
        }

    async def get_quick_summary(self, company_name: str) -> str:
        """Get a quick one-paragraph company summary using AI."""
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"In 2-3 sentences, describe what {company_name} does, "
                            f"their industry, and what they're known for. "
                            f"Be factual and concise."
                        ),
                    }
                ],
                temperature=0.3,
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Quick summary failed for {company_name}: {e}")
            return f"{company_name} - additional research needed"
