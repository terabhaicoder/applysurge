import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Import all models so Alembic can detect them
from app.db.base import Base
from app.models.user import User, VerificationToken, RefreshToken, Session
from app.models.profile import UserProfile, UserEducation, UserExperience, UserSkill, UserCertification
from app.models.resume import Resume
from app.models.preferences import JobPreferences
from app.models.credentials import PlatformCredentials
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.application import Application, ApplicationLog
from app.models.email_settings import EmailSettings
from app.models.email_template import EmailTemplate
from app.models.agent_settings import AgentSettings
from app.models.notification import Notification
from app.models.analytics import DailyStats, Export
from app.models.billing import SubscriptionPlan, PaymentHistory
from app.models.startup_contact import StartupContact, StartupOutreachSettings

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
