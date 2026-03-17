"""
FastAPI application entry point with CORS, middleware, routers, and lifespan events.
Includes Socket.IO integration for real-time agent communication.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as redis
import socketio
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.rate_limiter import RateLimitMiddleware
from app.db.session import close_db, init_db

logger = logging.getLogger(__name__)

# Socket.IO server with Redis message queue for multi-process support
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.CORS_ORIGINS,
    client_manager=socketio.AsyncRedisManager(settings.SOCKETIO_MESSAGE_QUEUE),
    logger=settings.DEBUG,
    engineio_logger=settings.DEBUG,
)

# Redis client for application-level caching and state
redis_client: redis.Redis = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    global redis_client

    logger.info("Starting JobPilot API server...")

    # Initialize database
    try:
        await init_db()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

    # Initialize Redis
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
        )
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}")
        redis_client = None

    # Store redis client in app state for dependency injection
    app.state.redis = redis_client

    logger.info(f"JobPilot API v{settings.APP_VERSION} started successfully")

    yield

    # Shutdown
    logger.info("Shutting down JobPilot API server...")

    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")

    await close_db()
    logger.info("Database connection closed")


def create_app() -> FastAPI:
    """
    Factory function to create and configure the FastAPI application.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered job application automation platform",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # Register exception handlers
    register_exception_handlers(app)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "X-Request-ID",
            "Accept",
            "Origin",
        ],
        expose_headers=[
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "X-Request-ID",
        ],
        max_age=600,
    )

    # Trusted Host middleware (production only)
    if settings.ENVIRONMENT == "production":
        domain = settings.DOMAIN
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=[domain, f"*.{domain}", f"api.{domain}", "localhost"],
        )

    # Rate limiting middleware
    app.add_middleware(
        RateLimitMiddleware,
        redis_url=settings.REDIS_URL,
        max_requests=settings.RATE_LIMIT_REQUESTS,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
        exclude_paths=["/health", "/docs", "/redoc", "/openapi.json", "/socket.io"],
    )

    # Request ID middleware
    app.add_middleware(RequestIDMiddleware)

    # Request logging middleware
    if settings.DEBUG:
        app.add_middleware(RequestLoggingMiddleware)

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint for load balancers and monitoring."""
        health_status = {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }

        # Check database
        try:
            from app.db.session import engine
            async with engine.connect() as conn:
                await conn.execute(
                    __import__("sqlalchemy").text("SELECT 1")
                )
            health_status["database"] = "connected"
        except Exception:
            health_status["database"] = "disconnected"
            health_status["status"] = "degraded"

        # Check Redis
        try:
            if app.state.redis:
                await app.state.redis.ping()
                health_status["redis"] = "connected"
            else:
                health_status["redis"] = "not configured"
        except Exception:
            health_status["redis"] = "disconnected"
            health_status["status"] = "degraded"

        status_code = (
            status.HTTP_200_OK
            if health_status["status"] == "healthy"
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return JSONResponse(content=health_status, status_code=status_code)

    # Include API routers
    _include_routers(app)

    return app


def _include_routers(app: FastAPI) -> None:
    """Include all API routers with the application."""
    try:
        from app.api.v1 import router as api_v1_router
        app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
        logger.info("API v1 routers registered")
    except ImportError:
        logger.warning("API v1 routers not found, skipping router registration")
    except Exception as e:
        logger.warning(f"Failed to register API routers: {e}")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add a unique request ID to each request."""

    async def dispatch(self, request: Request, call_next):
        import uuid
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request/response details in debug mode."""

    async def dispatch(self, request: Request, call_next):
        import time

        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        logger.debug(
            f"{request.method} {request.url.path} "
            f"status={response.status_code} "
            f"duration={duration:.3f}s"
        )

        return response


# Socket.IO event handlers
@sio.event
async def connect(sid, environ, auth):
    """Handle new Socket.IO connections with JWT authentication."""
    token = None
    if auth and isinstance(auth, dict):
        token = auth.get("token")

    if not token:
        logger.warning(f"Socket.IO connection rejected (no token): {sid}")
        raise socketio.exceptions.ConnectionRefusedError("Authentication required")

    from app.core.security import verify_access_token

    payload = verify_access_token(token)
    if not payload:
        logger.warning(f"Socket.IO connection rejected (invalid token): {sid}")
        raise socketio.exceptions.ConnectionRefusedError("Invalid or expired token")

    user_id = payload.get("sub")
    await sio.save_session(sid, {"user_id": user_id})

    # Auto-join user's personal room
    sio.enter_room(sid, f"user:{user_id}")
    logger.info(f"Socket.IO client connected: {sid} (user: {user_id})")


@sio.event
async def disconnect(sid):
    """Handle Socket.IO disconnections."""
    session = await sio.get_session(sid)
    user_id = session.get("user_id", "unknown") if session else "unknown"
    logger.info(f"Socket.IO client disconnected: {sid} (user: {user_id})")


@sio.event
async def join_room(sid, data):
    """Join a user-specific room for targeted notifications."""
    session = await sio.get_session(sid)
    if not session:
        return

    user_id = session.get("user_id")
    room = data.get("room")

    # Only allow users to join their own rooms
    if room and room in (f"user:{user_id}", f"agent:{user_id}"):
        sio.enter_room(sid, room)
        logger.debug(f"Client {sid} joined room {room}")
    else:
        logger.warning(f"Client {sid} denied access to room {room}")


@sio.event
async def leave_room(sid, data):
    """Leave a user-specific room."""
    room = data.get("room")
    if room:
        sio.leave_room(sid, room)
        logger.debug(f"Client {sid} left room {room}")


@sio.event
async def agent_subscribe(sid, data):
    """Subscribe to agent status updates for the authenticated user."""
    session = await sio.get_session(sid)
    if not session:
        return

    user_id = session.get("user_id")
    # Only subscribe to own agent events
    sio.enter_room(sid, f"agent:{user_id}")
    await sio.emit("agent_subscribed", {"user_id": user_id}, to=sid)


# Create the FastAPI app
app = create_app()

# Mount Socket.IO as ASGI sub-application
socket_app = socketio.ASGIApp(sio, app)


# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
