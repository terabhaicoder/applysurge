"""
Email finder utility.

Finds professional email addresses using Hunter.io API, pattern guessing,
and ZeroBounce verification.
"""

import asyncio
import logging
import os
import re
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY", "")
ZEROBOUNCE_API_KEY = os.environ.get("ZEROBOUNCE_API_KEY", "")


class EmailFinder:
    """
    Find email addresses using Hunter.io and pattern guessing.
    Supports finding by name+domain or by company+role.
    """

    def __init__(
        self,
        hunter_api_key: str = None,
        zerobounce_api_key: str = None,
    ):
        self.hunter_api_key = hunter_api_key or HUNTER_API_KEY
        self.zerobounce_api_key = zerobounce_api_key or ZEROBOUNCE_API_KEY

    async def find_email(
        self,
        company: str = "",
        domain: Optional[str] = None,
        role: str = "hiring manager",
        first_name: str = "",
        last_name: str = "",
    ) -> Optional[str]:
        """
        Find an email address for a role at a company.

        Tries multiple strategies:
        1. Hunter.io email finder (if name provided)
        2. Hunter.io domain search (to find relevant person)
        3. Pattern guessing with verification

        Args:
            company: Company name
            domain: Company domain (will be guessed if not provided)
            role: Target role (e.g., "hiring manager", "recruiter", "HR")
            first_name: Optional first name of target
            last_name: Optional last name of target

        Returns:
            Email address string or None
        """
        # Determine domain
        if not domain:
            domain = self._guess_domain(company)
            if not domain:
                logger.warning(f"Could not determine domain for company: {company}")
                return None

        # Strategy 1: Direct name-based lookup
        if first_name and last_name:
            result = await self._find_by_name(first_name, last_name, domain)
            if result:
                return result

        # Strategy 2: Domain search for relevant person
        role_email = await self._find_by_role(domain, role)
        if role_email:
            return role_email

        # Strategy 3: Generic patterns for common roles
        generic_email = self._get_generic_role_email(domain, role)
        if generic_email:
            is_valid = await self._verify_email(generic_email)
            if is_valid:
                return generic_email

        # Strategy 4: Try common generic addresses
        generic_addresses = [
            f"hiring@{domain}",
            f"careers@{domain}",
            f"jobs@{domain}",
            f"hr@{domain}",
            f"recruit@{domain}",
            f"talent@{domain}",
            f"people@{domain}",
        ]

        for addr in generic_addresses:
            is_valid = await self._verify_email(addr)
            if is_valid:
                return addr

        # Last resort: info@ address
        return f"info@{domain}"

    async def find_person_email(
        self,
        first_name: str,
        last_name: str,
        company_domain: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Find email address for a specific person at a company.

        Args:
            first_name: Person's first name
            last_name: Person's last name
            company_domain: Company domain

        Returns:
            Dict with email, confidence, source, verified keys or None
        """
        # Try Hunter.io first
        hunter_result = await self._hunter_find(first_name, last_name, company_domain)
        if hunter_result and hunter_result.get("email"):
            is_valid = await self._verify_email(hunter_result["email"])
            if is_valid:
                return {
                    "email": hunter_result["email"],
                    "confidence": hunter_result.get("confidence", 0),
                    "source": "hunter",
                    "verified": True,
                }

        # Fallback: pattern guessing
        pattern = await self._get_company_pattern(company_domain)
        guessed_emails = self._generate_email_variations(
            first_name, last_name, company_domain, pattern
        )

        # Verify each guess
        for email_addr in guessed_emails:
            is_valid = await self._verify_email(email_addr)
            if is_valid:
                return {
                    "email": email_addr,
                    "confidence": 70,
                    "source": "pattern_guess",
                    "verified": True,
                }

        # Return best guess unverified
        if guessed_emails:
            return {
                "email": guessed_emails[0],
                "confidence": 30,
                "source": "pattern_guess",
                "verified": False,
            }

        return None

    async def _find_by_name(
        self, first_name: str, last_name: str, domain: str
    ) -> Optional[str]:
        """Find email by name using Hunter.io."""
        result = await self._hunter_find(first_name, last_name, domain)
        if result and result.get("email"):
            is_valid = await self._verify_email(result["email"])
            if is_valid:
                return result["email"]
        return None

    async def _find_by_role(self, domain: str, role: str) -> Optional[str]:
        """Find email for a specific role at a company using domain search."""
        if not self.hunter_api_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.hunter.io/v2/domain-search",
                    params={
                        "domain": domain,
                        "api_key": self.hunter_api_key,
                        "limit": 20,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    emails = data.get("data", {}).get("emails", [])

                    # Score emails by role relevance
                    role_lower = role.lower()
                    role_keywords = self._get_role_keywords(role_lower)

                    best_match = None
                    best_score = 0

                    for email_info in emails:
                        position = (email_info.get("position") or "").lower()
                        department = (email_info.get("department") or "").lower()

                        score = 0
                        for keyword in role_keywords:
                            if keyword in position:
                                score += 3
                            if keyword in department:
                                score += 2

                        if score > best_score and email_info.get("value"):
                            best_score = score
                            best_match = email_info["value"]

                    if best_match:
                        is_valid = await self._verify_email(best_match)
                        if is_valid:
                            return best_match

        except Exception as e:
            logger.error(f"Hunter.io domain search error: {e}")

        return None

    async def _hunter_find(
        self, first_name: str, last_name: str, domain: str
    ) -> Optional[dict]:
        """Use Hunter.io email finder API."""
        if not self.hunter_api_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.hunter.io/v2/email-finder",
                    params={
                        "domain": domain,
                        "first_name": first_name,
                        "last_name": last_name,
                        "api_key": self.hunter_api_key,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    email_data = data.get("data", {})
                    if email_data.get("email"):
                        return {
                            "email": email_data["email"],
                            "confidence": email_data.get("score", 0),
                        }
        except Exception as e:
            logger.error(f"Hunter.io finder error: {e}")

        return None

    async def _get_company_pattern(self, domain: str) -> Optional[str]:
        """Get email pattern for a company from Hunter.io."""
        if not self.hunter_api_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.hunter.io/v2/domain-search",
                    params={
                        "domain": domain,
                        "api_key": self.hunter_api_key,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", {}).get("pattern")
        except Exception as e:
            logger.error(f"Hunter.io pattern error: {e}")

        return None

    def _generate_email_variations(
        self,
        first_name: str,
        last_name: str,
        domain: str,
        pattern: Optional[str] = None,
    ) -> List[str]:
        """Generate possible email variations for a person."""
        first = first_name.lower().strip()
        last = last_name.lower().strip()

        if not first or not last:
            return []

        variations = []

        # If we have a known pattern, use it first
        if pattern:
            try:
                pattern_email = pattern.replace("{first}", first)
                pattern_email = pattern_email.replace("{last}", last)
                pattern_email = pattern_email.replace("{f}", first[0])
                pattern_email = pattern_email.replace("{l}", last[0])
                if "@" not in pattern_email:
                    pattern_email = f"{pattern_email}@{domain}"
                variations.append(pattern_email)
            except (IndexError, KeyError):
                pass

        # Common patterns (ordered by popularity)
        common = [
            f"{first}.{last}@{domain}",
            f"{first}@{domain}",
            f"{first[0]}{last}@{domain}",
            f"{first}{last}@{domain}",
            f"{first}_{last}@{domain}",
            f"{first[0]}.{last}@{domain}",
            f"{first}{last[0]}@{domain}",
            f"{last}.{first}@{domain}",
            f"{first}-{last}@{domain}",
        ]

        for email_addr in common:
            if email_addr not in variations:
                variations.append(email_addr)

        return variations[:6]  # Limit API calls

    async def _verify_email(self, email_addr: str) -> bool:
        """Verify if email is valid using ZeroBounce."""
        if not self.zerobounce_api_key:
            return True  # Can't verify, assume valid

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.zerobounce.net/v2/validate",
                    params={
                        "api_key": self.zerobounce_api_key,
                        "email": email_addr,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "").lower()
                    return status in ["valid", "catch-all"]
        except Exception as e:
            logger.error(f"ZeroBounce verification error: {e}")

        # If verification fails, assume valid to not miss opportunities
        return True

    def _guess_domain(self, company: str) -> Optional[str]:
        """Guess a company's domain from their name."""
        if not company:
            return None

        # Clean company name
        company_clean = company.lower().strip()

        # Remove common suffixes
        suffixes = [
            " inc", " inc.", " ltd", " ltd.", " llc", " corp",
            " corporation", " co", " co.", " pvt", " private",
            " limited", " technologies", " tech", " solutions",
            " services", " group", " holdings",
        ]
        for suffix in suffixes:
            if company_clean.endswith(suffix):
                company_clean = company_clean[:-len(suffix)]

        # Remove special characters and spaces
        domain_name = re.sub(r"[^a-z0-9]", "", company_clean)

        if domain_name:
            return f"{domain_name}.com"

        return None

    def _get_role_keywords(self, role: str) -> List[str]:
        """Get keywords associated with a role for matching."""
        role_keyword_map = {
            "hiring manager": ["hiring", "manager", "engineering", "lead", "director", "head"],
            "recruiter": ["recruiter", "talent", "acquisition", "sourcer", "hr"],
            "hr": ["hr", "human resources", "people", "personnel"],
            "cto": ["cto", "chief technology", "vp engineering", "engineering"],
            "founder": ["founder", "ceo", "co-founder", "chief executive"],
        }

        keywords = role_keyword_map.get(role.lower(), [])
        if not keywords:
            keywords = role.lower().split()

        return keywords

    def _get_generic_role_email(self, domain: str, role: str) -> Optional[str]:
        """Get a generic email address for a role."""
        role_lower = role.lower()

        if "recruiter" in role_lower or "talent" in role_lower:
            return f"talent@{domain}"
        if "hr" in role_lower or "human" in role_lower:
            return f"hr@{domain}"
        if "hiring" in role_lower:
            return f"hiring@{domain}"
        if "founder" in role_lower or "ceo" in role_lower:
            return None  # Can't guess founder emails
        if "engineer" in role_lower or "tech" in role_lower:
            return f"engineering@{domain}"

        return None

    async def find_company_emails(self, domain: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find all known emails for a company domain."""
        if not self.hunter_api_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.hunter.io/v2/domain-search",
                    params={
                        "domain": domain,
                        "api_key": self.hunter_api_key,
                        "limit": limit,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    emails = data.get("data", {}).get("emails", [])
                    return [
                        {
                            "email": e.get("value"),
                            "first_name": e.get("first_name"),
                            "last_name": e.get("last_name"),
                            "position": e.get("position"),
                            "department": e.get("department"),
                            "confidence": e.get("confidence", 0),
                        }
                        for e in emails
                        if e.get("value")
                    ]
        except Exception as e:
            logger.error(f"Hunter.io domain search error: {e}")

        return []
