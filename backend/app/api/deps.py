"""
FastAPI dependency injection utilities.
Provides database sessions, authentication, rate limiting, and subscription checks.
"""

from typing import AsyncGenerator, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, RateLimitError, QuotaExceededError
from app.core.security import verify_access_token
from app.db import async_session_factory
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an async database session.
    Commits on success, rolls back on error, always closes.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate JWT from Authorization header, then look up the user.
    Raises 401 if token is missing, invalid, or user not found.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensure the current user is active.
    Raises 403 if user is deactivated.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return current_user


async def rate_limit(request: Request) -> None:
    """
    Rate limiting dependency using Redis.
    Limits requests per IP within the configured window.
    """
    import redis.asyncio as aioredis

    client_ip = request.client.host if request.client else "unknown"
    redis_key = f"rate_limit:{client_ip}:{request.url.path}"

    try:
        redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

        current = await redis.get(redis_key)
        if current and int(current) >= settings.RATE_LIMIT_REQUESTS:
            ttl = await redis.ttl(redis_key)
            await redis.close()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(ttl)},
            )

        pipe = redis.pipeline()
        pipe.incr(redis_key)
        pipe.expire(redis_key, settings.RATE_LIMIT_WINDOW_SECONDS)
        await pipe.execute()
        await redis.close()

    except HTTPException:
        raise
    except Exception:
        # If Redis is unavailable, allow the request (fail open)
        pass


async def subscription_check(
    required_tier: str = "free",
):
    """
    Factory for subscription tier checking.
    Returns a dependency that validates the user's subscription tier.
    """

    async def check_subscription(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        tier_levels = {"free": 0, "basic": 1, "pro": 2, "enterprise": 3}
        user_level = tier_levels.get(current_user.subscription_tier, 0)
        required_level = tier_levels.get(required_tier, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires a {required_tier} subscription or higher",
            )
        return current_user

    return check_subscription


def require_subscription(tier: str = "pro"):
    """
    Dependency factory that requires a minimum subscription tier.
    Usage: Depends(require_subscription("pro"))
    """

    async def _check(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        tier_levels = {"free": 0, "basic": 1, "pro": 2, "enterprise": 3}
        user_level = tier_levels.get(current_user.subscription_tier, 0)
        required_level = tier_levels.get(tier, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires a {tier} subscription or higher",
            )
        return current_user

    return _check
