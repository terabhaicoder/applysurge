"""
CAPTCHA detection and notification handler.

Detects common CAPTCHA types (reCAPTCHA, hCaptcha, image challenges)
and notifies the user when manual intervention is needed.
"""

import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CaptchaHandler:
    """
    Detects CAPTCHAs on web pages and notifies users.
    Does not attempt to solve CAPTCHAs automatically.
    """

    # Known CAPTCHA indicators
    CAPTCHA_SELECTORS = [
        # Google reCAPTCHA
        'iframe[src*="recaptcha"]',
        'iframe[title*="reCAPTCHA"]',
        ".g-recaptcha",
        "#recaptcha",
        'div[class*="recaptcha"]',
        # hCaptcha
        'iframe[src*="hcaptcha"]',
        ".h-captcha",
        'div[class*="hcaptcha"]',
        # General CAPTCHA patterns
        'img[alt*="captcha" i]',
        'img[src*="captcha" i]',
        'input[name*="captcha" i]',
        'div[id*="captcha" i]',
        'div[class*="captcha" i]',
        # LinkedIn specific
        "#captcha-internal",
        ".checkpoint-challenge",
        'iframe[id*="captcha"]',
        # Naukri specific
        ".captcha-container",
        "#captchaV2",
    ]

    # Text patterns indicating CAPTCHA presence
    CAPTCHA_TEXT_PATTERNS = [
        "verify you are human",
        "prove you're not a robot",
        "security check",
        "unusual activity",
        "complete the challenge",
        "verify your identity",
        "confirm you are not a bot",
        "please verify",
    ]

    async def detect_captcha(self, page) -> bool:
        """
        Detect if a CAPTCHA is present on the page.

        Args:
            page: Playwright page instance

        Returns:
            True if a CAPTCHA is detected
        """
        # Check DOM selectors
        for selector in self.CAPTCHA_SELECTORS:
            try:
                element = await page.query_selector(selector)
                if element:
                    is_visible = await element.is_visible()
                    if is_visible:
                        logger.warning(f"CAPTCHA detected via selector: {selector}")
                        return True
            except Exception:
                continue

        # Check page text for CAPTCHA indicators
        try:
            body_text = await page.evaluate("() => document.body.innerText.toLowerCase()")
            for pattern in self.CAPTCHA_TEXT_PATTERNS:
                if pattern in body_text:
                    logger.warning(f"CAPTCHA detected via text pattern: '{pattern}'")
                    return True
        except Exception as e:
            logger.debug(f"Error checking page text for CAPTCHA: {e}")

        # Check for challenge iframes
        try:
            frames = page.frames
            for frame in frames:
                frame_url = frame.url
                if any(indicator in frame_url.lower() for indicator in [
                    "recaptcha", "hcaptcha", "captcha", "challenge"
                ]):
                    logger.warning(f"CAPTCHA detected via iframe: {frame_url}")
                    return True
        except Exception:
            pass

        return False

    async def get_captcha_type(self, page) -> Optional[str]:
        """
        Identify the type of CAPTCHA present.

        Returns:
            String indicating CAPTCHA type or None
        """
        # Check for reCAPTCHA
        recaptcha_selectors = [
            'iframe[src*="recaptcha"]',
            ".g-recaptcha",
            "#recaptcha",
        ]
        for selector in recaptcha_selectors:
            el = await page.query_selector(selector)
            if el:
                return "recaptcha"

        # Check for hCaptcha
        hcaptcha_selectors = [
            'iframe[src*="hcaptcha"]',
            ".h-captcha",
        ]
        for selector in hcaptcha_selectors:
            el = await page.query_selector(selector)
            if el:
                return "hcaptcha"

        # Check for image CAPTCHA
        img_captcha = await page.query_selector(
            'img[alt*="captcha" i], img[src*="captcha" i]'
        )
        if img_captcha:
            return "image"

        # Check for text CAPTCHA
        text_captcha = await page.query_selector(
            'input[name*="captcha" i]'
        )
        if text_captcha:
            return "text"

        return "unknown"

    async def notify_user(
        self,
        user_id: str,
        platform: str,
        captcha_type: str,
        screenshot_url: Optional[str] = None,
    ):
        """
        Notify the user that a CAPTCHA requires manual intervention.

        Args:
            user_id: User identifier
            platform: Platform where CAPTCHA appeared
            captcha_type: Type of CAPTCHA detected
            screenshot_url: Screenshot of the CAPTCHA page
        """
        import redis
        import json
        from datetime import datetime, timezone

        try:
            r = redis.from_url(
                os.environ.get("REDIS_URL", "redis://redis:6379/0"),
                decode_responses=True,
            )

            notification = {
                "type": "captcha_detected",
                "user_id": user_id,
                "platform": platform,
                "captcha_type": captcha_type,
                "screenshot_url": screenshot_url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": (
                    f"A {captcha_type} CAPTCHA was detected on {platform}. "
                    f"Please log in manually to resolve it."
                ),
            }

            # Publish to user's notification channel
            channel = f"notifications:{user_id}"
            r.publish(channel, json.dumps(notification))

            # Also store as persistent notification
            notification_key = f"jobpilot:notifications:{user_id}"
            r.lpush(notification_key, json.dumps(notification))
            r.ltrim(notification_key, 0, 99)  # Keep last 100 notifications
            r.expire(notification_key, 86400 * 7)  # 7 day TTL

            logger.info(
                f"Notified user {user_id} about {captcha_type} CAPTCHA on {platform}"
            )

        except Exception as e:
            logger.error(f"Failed to notify user about CAPTCHA: {e}")

    async def handle_captcha(
        self,
        page,
        user_id: str,
        platform: str,
    ) -> Dict[str, Any]:
        """
        Handle a detected CAPTCHA by identifying it and notifying the user.

        Args:
            page: Playwright page instance
            user_id: User identifier
            platform: Platform name

        Returns:
            Dict with CAPTCHA details and status
        """
        captcha_type = await self.get_captcha_type(page)

        # Take screenshot of CAPTCHA
        from worker.automation.screenshot_manager import ScreenshotManager
        ss_manager = ScreenshotManager()
        screenshot_url = await ss_manager.capture_and_upload(
            page=page,
            user_id=user_id,
            name=f"captcha_{platform}_{captcha_type}",
        )

        # Notify user
        await self.notify_user(
            user_id=user_id,
            platform=platform,
            captcha_type=captcha_type,
            screenshot_url=screenshot_url,
        )

        return {
            "captcha_detected": True,
            "captcha_type": captcha_type,
            "screenshot_url": screenshot_url,
            "action": "user_notification_sent",
        }
