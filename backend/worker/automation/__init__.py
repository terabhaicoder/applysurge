"""
JobPilot automation module.

Provides browser management, session persistence, form filling,
CAPTCHA handling, and screenshot management.
"""

from worker.automation.browser_manager import BrowserManager
from worker.automation.session_manager import SessionManager
from worker.automation.captcha_handler import CaptchaHandler
from worker.automation.form_filler import FormFiller
from worker.automation.screenshot_manager import ScreenshotManager

__all__ = [
    "BrowserManager",
    "SessionManager",
    "CaptchaHandler",
    "FormFiller",
    "ScreenshotManager",
]
