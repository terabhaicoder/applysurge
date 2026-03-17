"""Database initialization utilities."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger(__name__)


async def create_tables():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created.")


async def drop_tables():
    """Drop all database tables (use with caution)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("Database tables dropped.")


async def init_db(session: AsyncSession):
    """Initialize database with required data.

    SubscriptionPlan records are per-user and created on user registration.
    No global seed data is needed.
    """
    logger.info("Database initialization complete.")
