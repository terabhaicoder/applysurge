"""
Abstract base class for all scrapers.

Provides common functionality including browser management, session persistence,
rate limiting, and anti-detection measures.
"""

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from worker.automation.browser_manager import BrowserManager
from worker.automation.session_manager import SessionManager

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base scraper with common browser automation functionality."""

    PLATFORM: str = "unknown"
    BASE_URL: str = ""
    MIN_DELAY: float = 1.0
    MAX_DELAY: float = 3.0
    PAGE_LOAD_TIMEOUT: int = 60000  # 60 seconds (headless Docker needs more time)

    def __init__(self, user_id: str, context=None, page=None):
        self.user_id = user_id
        self.browser_manager = BrowserManager()
        self.session_manager = SessionManager()
        self.context = context
        self.page = page
        self._is_logged_in = context is not None and page is not None
        self._owns_context = context is None  # Track if we created it

    async def initialize(self):
        """Initialize browser context with stealth configuration."""
        if self.context and self.page:
            return  # Using externally provided context

        self.context = await self.browser_manager.get_context(
            user_id=self.user_id,
            platform=self.PLATFORM,
        )
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.PAGE_LOAD_TIMEOUT)

        # Restore session cookies if available
        cookies = await self.session_manager.load_cookies(
            user_id=self.user_id,
            platform=self.PLATFORM,
        )
        if cookies:
            await self.context.add_cookies(cookies)
            logger.info(f"Restored {len(cookies)} cookies for {self.PLATFORM}")

    async def cleanup(self):
        """Save session and close browser context."""
        if not self._owns_context:
            return  # Caller owns the context, they handle cleanup

        if self._is_logged_in and self.context:
            # Save cookies for next session
            cookies = await self.context.cookies()
            await self.session_manager.save_cookies(
                user_id=self.user_id,
                platform=self.PLATFORM,
                cookies=cookies,
            )

        if self.page:
            await self.page.close()
        if self.context:
            await self.browser_manager.release_context(
                user_id=self.user_id,
                platform=self.PLATFORM,
            )

    async def random_delay(self, min_sec: float = None, max_sec: float = None):
        """Human-like random delay between actions."""
        min_val = min_sec if min_sec is not None else self.MIN_DELAY
        max_val = max_sec if max_sec is not None else self.MAX_DELAY
        delay = random.uniform(min_val, max_val)
        await asyncio.sleep(delay)

    async def human_type(self, selector: str, text: str, clear: bool = True):
        """Type text with human-like random delays between keystrokes."""
        element = await self.page.wait_for_selector(selector, timeout=10000)
        if clear:
            await element.click(click_count=3)
            await self.page.keyboard.press("Backspace")
            await asyncio.sleep(random.uniform(0.1, 0.3))

        for char in text:
            await element.type(char, delay=random.randint(50, 150))
            # Occasional longer pause (simulates thinking)
            if random.random() < 0.05:
                await asyncio.sleep(random.uniform(0.3, 0.8))

    async def safe_click(self, selector: str, timeout: int = 10000):
        """Click an element with error handling and wait."""
        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            await asyncio.sleep(random.uniform(0.1, 0.5))
            await element.click()
            await self.random_delay(0.5, 1.5)
            return True
        except Exception as e:
            logger.warning(f"Failed to click {selector}: {e}")
            return False

    async def scroll_page(self, distance: int = None):
        """Scroll the page with human-like behavior."""
        if distance is None:
            distance = random.randint(300, 700)

        # Smooth scroll in steps
        steps = random.randint(3, 6)
        step_distance = distance // steps
        for _ in range(steps):
            await self.page.mouse.wheel(0, step_distance)
            await asyncio.sleep(random.uniform(0.05, 0.15))

        await self.random_delay(0.3, 0.8)

    async def wait_for_navigation(self, timeout: int = None):
        """Wait for page navigation with custom timeout."""
        timeout = timeout or self.PAGE_LOAD_TIMEOUT
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
        except Exception:
            # Fall back to load state
            try:
                await self.page.wait_for_load_state("load", timeout=5000)
            except Exception:
                pass

    async def check_for_captcha(self) -> bool:
        """Check if a CAPTCHA is present on the page."""
        from worker.automation.captcha_handler import CaptchaHandler
        handler = CaptchaHandler()
        return await handler.detect_captcha(self.page)

    async def take_screenshot(self, name: str) -> Optional[str]:
        """Take a screenshot, upload to storage, and publish to live view."""
        from worker.automation.screenshot_manager import ScreenshotManager
        manager = ScreenshotManager()
        url = await manager.capture_and_upload(
            page=self.page,
            user_id=self.user_id,
            name=name,
        )
        # Also publish a live screenshot for the Live View
        await self._publish_live_screenshot()
        return url

    async def _publish_live_screenshot(self):
        """Capture a viewport screenshot and store in Redis for live view polling."""
        try:
            import base64
            import os
            import redis as redis_lib

            screenshot_bytes = await self.page.screenshot(type="jpeg", quality=50)
            if not screenshot_bytes:
                return

            b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            data_url = f"data:image/jpeg;base64,{b64}"

            redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
            r = redis_lib.from_url(redis_url, decode_responses=True)
            r.set(
                f"jobpilot:agent:live_screenshot:{self.user_id}",
                data_url,
                ex=120,  # 2 min TTL
            )
            r.close()
        except Exception as e:
            logger.debug(f"Live screenshot publish failed: {e}")

    async def get_page_text(self) -> str:
        """Get all visible text content from the page."""
        return await self.page.evaluate("() => document.body.innerText")

    async def is_element_visible(self, selector: str) -> bool:
        """Check if an element is visible on the page."""
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.is_visible()
            return False
        except Exception:
            return False

    @abstractmethod
    async def login(self, email: str, password: str) -> bool:
        """Login to the platform. Must be implemented by subclasses."""
        pass

    @abstractmethod
    async def search_jobs(self, **kwargs) -> List[Dict[str, Any]]:
        """Search for jobs. Must be implemented by subclasses."""
        pass
