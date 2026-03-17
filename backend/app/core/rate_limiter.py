"""
Redis-based rate limiting middleware and utilities.
Implements a sliding window rate limiter using Redis sorted sets.
"""

import time
from typing import Optional

import redis.asyncio as redis
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings


class RateLimiter:
    """
    Redis-based sliding window rate limiter.
    Uses sorted sets with timestamps for precise windowing.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        max_requests: int = 100,
        window_seconds: int = 60,
        prefix: str = "rate_limit",
    ):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.prefix = prefix

    async def is_allowed(self, identifier: str) -> tuple[bool, dict]:
        """
        Check if a request is allowed under the rate limit.

        Args:
            identifier: Unique identifier for the client (IP, user ID, API key).

        Returns:
            Tuple of (is_allowed, info_dict with remaining, reset, limit).
        """
        key = f"{self.prefix}:{identifier}"
        now = time.time()
        window_start = now - self.window_seconds

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {f"{now}": now})
        pipe.zcard(key)
        pipe.expire(key, self.window_seconds + 1)
        results = await pipe.execute()

        current_count = results[2]
        is_allowed = current_count <= self.max_requests

        if not is_allowed:
            await self.redis.zrem(key, f"{now}")
            current_count -= 1

        remaining = max(0, self.max_requests - current_count)
        reset_time = int(now + self.window_seconds)

        info = {
            "limit": self.max_requests,
            "remaining": remaining,
            "reset": reset_time,
            "window": self.window_seconds,
        }

        return is_allowed, info

    async def reset(self, identifier: str) -> None:
        """Reset the rate limit counter for an identifier."""
        key = f"{self.prefix}:{identifier}"
        await self.redis.delete(key)

    async def get_usage(self, identifier: str) -> int:
        """Get current request count for an identifier."""
        key = f"{self.prefix}:{identifier}"
        now = time.time()
        window_start = now - self.window_seconds
        await self.redis.zremrangebyscore(key, 0, window_start)
        return await self.redis.zcard(key)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that applies rate limiting to all requests.
    Rate limits are applied per IP address for unauthenticated requests,
    and per user ID for authenticated requests.
    """

    def __init__(
        self,
        app,
        redis_url: str = None,
        max_requests: int = None,
        window_seconds: int = None,
        exclude_paths: Optional[list[str]] = None,
    ):
        super().__init__(app)
        self.redis_url = redis_url or settings.REDIS_URL
        self.max_requests = max_requests or settings.RATE_LIMIT_REQUESTS
        self.window_seconds = window_seconds or settings.RATE_LIMIT_WINDOW_SECONDS
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        self._redis: Optional[redis.Redis] = None
        self._limiter: Optional[RateLimiter] = None

    async def _get_limiter(self) -> RateLimiter:
        """Lazily initialize the Redis connection and rate limiter."""
        if self._limiter is None:
            self._redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
            )
            self._limiter = RateLimiter(
                redis_client=self._redis,
                max_requests=self.max_requests,
                window_seconds=self.window_seconds,
            )
        return self._limiter

    def _get_client_identifier(self, request: Request) -> str:
        """
        Extract a client identifier from the request.
        Uses user ID if authenticated, otherwise falls back to IP.
        """
        user = getattr(request.state, "user", None)
        if user and hasattr(user, "id"):
            return f"user:{user.id}"

        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return f"ip:{real_ip}"

        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to the request."""
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        try:
            limiter = await self._get_limiter()
            identifier = self._get_client_identifier(request)
            is_allowed, info = await limiter.is_allowed(identifier)

            if not is_allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": True,
                        "message": "Rate limit exceeded",
                        "detail": {
                            "retry_after": info["window"],
                            "limit": info["limit"],
                        },
                    },
                    headers={
                        "Retry-After": str(info["window"]),
                        "X-RateLimit-Limit": str(info["limit"]),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(info["reset"]),
                    },
                )

            response = await call_next(request)

            response.headers["X-RateLimit-Limit"] = str(info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(info["reset"])

            return response

        except redis.ConnectionError:
            return await call_next(request)
        except Exception:
            return await call_next(request)


def create_rate_limiter(
    redis_client: redis.Redis,
    max_requests: int = 100,
    window_seconds: int = 60,
    prefix: str = "rate_limit",
) -> RateLimiter:
    """Factory function for creating a rate limiter instance."""
    return RateLimiter(
        redis_client=redis_client,
        max_requests=max_requests,
        window_seconds=window_seconds,
        prefix=prefix,
    )
