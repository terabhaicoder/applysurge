"""
Cookie and session persistence using Redis.

Saves and loads browser cookies per platform per user to maintain
login sessions across scraping runs.
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional

import redis

from app.core.encryption import encrypt_value, decrypt_value

logger = logging.getLogger(__name__)

# Redis connection settings
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
SESSION_TTL = 86400 * 7  # 7 days TTL for sessions
SESSION_PREFIX = "jobpilot:session:"


class SessionManager:
    """
    Manages browser session cookies in Redis for persistence across runs.
    Sessions are stored per user per platform with configurable TTL.
    """

    def __init__(self):
        self._redis: Optional[redis.Redis] = None

    def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
        return self._redis

    def _session_key(self, user_id: str, platform: str) -> str:
        """Generate Redis key for a user's platform session."""
        return f"{SESSION_PREFIX}{user_id}:{platform}"

    async def save_cookies(
        self,
        user_id: str,
        platform: str,
        cookies: List[Dict[str, Any]],
    ) -> bool:
        """
        Save browser cookies to Redis for a user's platform session.

        Args:
            user_id: User identifier
            platform: Platform name (linkedin, naukri, etc.)
            cookies: List of cookie dictionaries from Playwright

        Returns:
            True if saved successfully
        """
        try:
            r = self._get_redis()
            key = self._session_key(user_id, platform)

            # Serialize cookies, handling non-serializable fields
            serializable_cookies = []
            for cookie in cookies:
                clean_cookie = {
                    "name": cookie.get("name", ""),
                    "value": cookie.get("value", ""),
                    "domain": cookie.get("domain", ""),
                    "path": cookie.get("path", "/"),
                    "expires": cookie.get("expires", -1),
                    "httpOnly": cookie.get("httpOnly", False),
                    "secure": cookie.get("secure", False),
                    "sameSite": cookie.get("sameSite", "Lax"),
                }
                serializable_cookies.append(clean_cookie)

            cookie_data = json.dumps(serializable_cookies)
            encrypted_data = encrypt_value(cookie_data)
            r.setex(key, SESSION_TTL, encrypted_data)

            logger.info(
                f"Saved {len(serializable_cookies)} cookies for "
                f"user {user_id} on {platform}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
            return False

    async def load_cookies(
        self,
        user_id: str,
        platform: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Load saved cookies from Redis for a user's platform session.

        Args:
            user_id: User identifier
            platform: Platform name

        Returns:
            List of cookie dictionaries or None if not found
        """
        try:
            r = self._get_redis()
            key = self._session_key(user_id, platform)

            encrypted_data = r.get(key)
            if not encrypted_data:
                logger.debug(f"No saved session for user {user_id} on {platform}")
                return None

            cookie_data = decrypt_value(encrypted_data)
            if not cookie_data:
                logger.warning(f"Failed to decrypt cookies for user {user_id} on {platform}")
                await self.delete_session(user_id, platform)
                return None

            cookies = json.loads(cookie_data)

            # Filter out expired cookies
            import time
            current_time = time.time()
            valid_cookies = [
                c for c in cookies
                if c.get("expires", -1) == -1 or c["expires"] > current_time
            ]

            if not valid_cookies:
                logger.debug(f"All cookies expired for user {user_id} on {platform}")
                await self.delete_session(user_id, platform)
                return None

            logger.info(
                f"Loaded {len(valid_cookies)} cookies for "
                f"user {user_id} on {platform}"
            )
            return valid_cookies

        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return None

    async def delete_session(self, user_id: str, platform: str) -> bool:
        """
        Delete a user's platform session from Redis.

        Args:
            user_id: User identifier
            platform: Platform name

        Returns:
            True if deleted successfully
        """
        try:
            r = self._get_redis()
            key = self._session_key(user_id, platform)
            r.delete(key)
            logger.info(f"Deleted session for user {user_id} on {platform}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False

    async def session_exists(self, user_id: str, platform: str) -> bool:
        """Check if a session exists for a user on a platform."""
        try:
            r = self._get_redis()
            key = self._session_key(user_id, platform)
            return r.exists(key) > 0
        except Exception:
            return False

    async def extend_session(self, user_id: str, platform: str) -> bool:
        """Extend the TTL of an existing session."""
        try:
            r = self._get_redis()
            key = self._session_key(user_id, platform)
            if r.exists(key):
                r.expire(key, SESSION_TTL)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to extend session: {e}")
            return False

    async def get_all_sessions(self, user_id: str) -> Dict[str, bool]:
        """Get all platform sessions for a user."""
        platforms = ["linkedin", "naukri"]
        sessions = {}
        for platform in platforms:
            sessions[platform] = await self.session_exists(user_id, platform)
        return sessions

    async def clear_all_sessions(self, user_id: str) -> int:
        """Clear all sessions for a user."""
        try:
            r = self._get_redis()
            pattern = f"{SESSION_PREFIX}{user_id}:*"
            keys = r.keys(pattern)
            if keys:
                r.delete(*keys)
                logger.info(f"Cleared {len(keys)} sessions for user {user_id}")
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to clear sessions: {e}")
            return 0

    def close(self):
        """Close Redis connection."""
        if self._redis:
            self._redis.close()
            self._redis = None
