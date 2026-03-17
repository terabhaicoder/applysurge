"""
Playwright browser pool management.

Manages browser contexts with stealth configuration, connection pooling,
and concurrent session limits for automated job applications.
"""

import asyncio
import logging
import os
import random
from typing import Dict, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright

logger = logging.getLogger(__name__)

# Maximum concurrent browser contexts
MAX_CONCURRENT_CONTEXTS = int(os.environ.get("MAX_BROWSER_CONTEXTS", 5))

# Updated user agents (Chrome 124-127 as of mid-2025)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
]

# Viewport sizes for rotation
VIEWPORT_SIZES = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1680, "height": 1050},
]


class BrowserManager:
    """
    Manages Playwright browser instances and contexts with stealth mode.
    Provides connection pooling and concurrent session management.
    """

    _instance: Optional["BrowserManager"] = None
    _playwright: Optional[Playwright] = None
    _browser: Optional[Browser] = None
    _contexts: Dict[str, BrowserContext] = {}
    _lock = asyncio.Lock()
    _semaphore = asyncio.Semaphore(MAX_CONCURRENT_CONTEXTS)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def _ensure_browser(self):
        """Ensure the browser instance is running."""
        if self._browser is None or not self._browser.is_connected():
            async with self._lock:
                if self._browser is None or not self._browser.is_connected():
                    self._playwright = await async_playwright().start()
                    headless = os.environ.get("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
                    launch_args = [
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-accelerated-2d-canvas",
                        "--disable-gpu",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-infobars",
                        "--window-size=1920,1080",
                        "--start-maximized",
                    ]

                    # Try launching with real Chrome channel first for better anti-detection
                    try:
                        self._browser = await self._playwright.chromium.launch(
                            headless=headless,
                            channel="chrome",
                            args=launch_args,
                        )
                        logger.info("Browser launched with Chrome channel")
                    except Exception:
                        # Fall back to bundled Chromium
                        self._browser = await self._playwright.chromium.launch(
                            headless=headless,
                            args=launch_args,
                        )
                        logger.info("Browser launched with bundled Chromium")

    async def get_context(
        self,
        user_id: str,
        platform: str,
        locale: str = "en-US",
        timezone_id: str = "Asia/Kolkata",
    ) -> BrowserContext:
        """
        Get or create a browser context for a user+platform combination.
        Applies stealth mode configuration to avoid detection.

        Args:
            user_id: User identifier
            platform: Platform name (linkedin, naukri, etc.)
            locale: Browser locale
            timezone_id: Timezone for the browser context

        Returns:
            Configured BrowserContext with stealth mode
        """
        context_key = f"{user_id}_{platform}"

        # Check for existing context
        if context_key in self._contexts:
            context = self._contexts[context_key]
            try:
                # Verify context is still valid
                pages = context.pages
                return context
            except Exception:
                # Context is stale, remove it
                del self._contexts[context_key]

        # Acquire semaphore to limit concurrent contexts
        await self._semaphore.acquire()

        try:
            await self._ensure_browser()

            # Randomize browser fingerprint
            user_agent = random.choice(USER_AGENTS)
            viewport = random.choice(VIEWPORT_SIZES)

            context = await self._browser.new_context(
                user_agent=user_agent,
                viewport=viewport,
                locale=locale,
                timezone_id=timezone_id,
                color_scheme="light",
                has_touch=False,
                is_mobile=False,
                java_script_enabled=True,
                permissions=["geolocation"],
                geolocation={"latitude": 28.6139, "longitude": 77.2090},  # Delhi
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "DNT": "1",
                    "Upgrade-Insecure-Requests": "1",
                },
            )

            # Apply stealth mode scripts
            await self._apply_stealth_scripts(context)

            self._contexts[context_key] = context
            logger.info(f"Created browser context for {context_key}")
            return context

        except Exception as e:
            self._semaphore.release()
            logger.error(f"Failed to create browser context: {e}")
            raise

    async def release_context(self, user_id: str, platform: str):
        """Release a browser context back to the pool."""
        context_key = f"{user_id}_{platform}"

        if context_key in self._contexts:
            context = self._contexts.pop(context_key)
            try:
                await context.close()
            except Exception as e:
                logger.debug(f"Error closing context {context_key}: {e}")
            finally:
                self._semaphore.release()
                logger.info(f"Released browser context for {context_key}")

    async def _apply_stealth_scripts(self, context: BrowserContext):
        """Apply stealth mode scripts to avoid bot detection."""
        stealth_scripts = [
            # Override navigator.webdriver
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """,
            # Override chrome detection
            """
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {},
            };
            """,
            # Override permissions
            """
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            """,
            # Override plugins
            """
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            """,
            # Override languages
            """
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            """,
            # Override platform
            """
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32',
            });
            """,
            # Override hardware concurrency
            """
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8,
            });
            """,
            # Override device memory
            """
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8,
            });
            """,
            # Canvas fingerprint randomization
            """
            const toDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                if (type === 'image/png' && this.width === 16 && this.height === 16) {
                    return toDataURL.apply(this, arguments);
                }
                const context = this.getContext('2d');
                if (context) {
                    const shift = {r: Math.floor(Math.random() * 10) - 5,
                                   g: Math.floor(Math.random() * 10) - 5,
                                   b: Math.floor(Math.random() * 10) - 5};
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += shift.r;
                        imageData.data[i+1] += shift.g;
                        imageData.data[i+2] += shift.b;
                    }
                    context.putImageData(imageData, 0, 0);
                }
                return toDataURL.apply(this, arguments);
            };
            """,
            # WebGL vendor/renderer override
            """
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.';
                if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                return getParameter.apply(this, arguments);
            };
            """,
        ]

        # Add initialization script to all new pages
        for script in stealth_scripts:
            await context.add_init_script(script)

    async def close_all(self):
        """Close all contexts and the browser."""
        for key in list(self._contexts.keys()):
            try:
                await self._contexts[key].close()
            except Exception:
                pass
        self._contexts.clear()

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        logger.info("All browser resources closed")
