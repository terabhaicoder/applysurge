"""
Email verification utility using ZeroBounce.

Provides single and batch email validation with detailed status reporting.
"""

import logging
import os
from typing import Optional, List, Dict, Any

import httpx

logger = logging.getLogger(__name__)

ZEROBOUNCE_API_KEY = os.environ.get("ZEROBOUNCE_API_KEY", "")


class EmailVerifier:
    """
    Verify email addresses using ZeroBounce API.
    Provides validation status, deliverability info, and suggestions.
    """

    VALID_STATUSES = ["valid", "catch-all"]
    INVALID_STATUSES = ["invalid", "spamtrap", "abuse", "do_not_mail"]
    RISKY_STATUSES = ["catch-all", "unknown"]

    def __init__(self, api_key: str = None):
        self.api_key = api_key or ZEROBOUNCE_API_KEY
        self.base_url = "https://api.zerobounce.net/v2"

    async def verify(self, email: str) -> Dict[str, Any]:
        """
        Verify a single email address.

        Args:
            email: Email address to verify

        Returns:
            Dict with keys: valid, status, sub_status, free_email,
            did_you_mean, domain_age_days, smtp_provider, risk_level
        """
        if not self.api_key:
            return {
                "valid": True,
                "status": "unknown",
                "sub_status": "api_key_not_configured",
                "free_email": None,
                "did_you_mean": None,
                "risk_level": "unknown",
            }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/validate",
                    params={
                        "api_key": self.api_key,
                        "email": email,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "").lower()

                    # Determine risk level
                    risk_level = "low"
                    if status in self.INVALID_STATUSES:
                        risk_level = "high"
                    elif status in self.RISKY_STATUSES:
                        risk_level = "medium"

                    return {
                        "valid": status in self.VALID_STATUSES,
                        "status": status,
                        "sub_status": data.get("sub_status", ""),
                        "free_email": data.get("free_email"),
                        "did_you_mean": data.get("did_you_mean"),
                        "domain_age_days": data.get("domain_age_days"),
                        "smtp_provider": data.get("smtp_provider"),
                        "risk_level": risk_level,
                        "mx_found": data.get("mx_found"),
                        "mx_record": data.get("mx_record"),
                    }

                logger.warning(f"ZeroBounce returned status {response.status_code}")

        except httpx.TimeoutException:
            logger.warning(f"ZeroBounce timeout for {email}")
        except Exception as e:
            logger.error(f"ZeroBounce error for {email}: {e}")

        # Default: assume valid if we can't verify
        return {
            "valid": True,
            "status": "unknown",
            "sub_status": "verification_failed",
            "free_email": None,
            "did_you_mean": None,
            "risk_level": "unknown",
        }

    async def verify_batch(self, emails: List[str]) -> List[Dict[str, Any]]:
        """
        Verify multiple emails sequentially (respects rate limits).

        Args:
            emails: List of email addresses to verify

        Returns:
            List of verification result dicts
        """
        results = []
        for email in emails:
            result = await self.verify(email)
            result["email"] = email
            results.append(result)
        return results

    async def is_valid(self, email: str) -> bool:
        """
        Quick check if an email is valid.

        Args:
            email: Email address to check

        Returns:
            True if email is valid or catch-all
        """
        result = await self.verify(email)
        return result.get("valid", True)

    async def is_safe_to_send(self, email: str) -> bool:
        """
        Check if it's safe to send to an email (not a spamtrap, abuse, etc.).

        Args:
            email: Email address to check

        Returns:
            True if safe to send
        """
        result = await self.verify(email)
        status = result.get("status", "unknown")
        return status not in self.INVALID_STATUSES

    async def get_credits(self) -> Optional[int]:
        """
        Check remaining ZeroBounce API credits.

        Returns:
            Number of remaining credits or None on error
        """
        if not self.api_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/getcredits",
                    params={"api_key": self.api_key},
                )

                if response.status_code == 200:
                    data = response.json()
                    return int(data.get("Credits", 0))
        except Exception as e:
            logger.error(f"ZeroBounce credits check error: {e}")

        return None

    async def get_api_usage(self) -> Optional[Dict[str, Any]]:
        """
        Get API usage statistics for the current billing period.

        Returns:
            Dict with usage stats or None
        """
        if not self.api_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/getapiusage",
                    params={
                        "api_key": self.api_key,
                        "start_date": "2024-01-01",
                        "end_date": "2030-12-31",
                    },
                )

                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"ZeroBounce usage check error: {e}")

        return None
