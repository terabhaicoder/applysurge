"""
Application configuration using pydantic-settings.
Loads all environment variables with validation and defaults.
"""

from typing import List, Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "JobPilot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    APP_ENV: str = ""  # Alias - if set, overrides ENVIRONMENT
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # URLs
    FRONTEND_URL: str = "http://localhost:3000"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://jobpilot:jobpilot_pass@postgres:5432/jobpilot_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_MAX_CONNECTIONS: int = 20

    # JWT
    JWT_SECRET_KEY: str = "change-this-to-a-secure-random-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Encryption
    ENCRYPTION_KEY: str = "change-this-to-a-32-byte-base64-encoded-key"

    # Email (SMTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@jobpilot.ai"
    SMTP_FROM_NAME: str = "JobPilot"
    SMTP_USE_TLS: bool = True

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

    # SendGrid
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "outreach@jobpilot.ai"

    # Hunter.io
    HUNTER_API_KEY: str = ""

    # Startup Outreach
    STARTUP_OUTREACH_MAX_EMAILS_PER_DAY: int = 20
    STARTUP_OUTREACH_MAX_DISCOVERY_PER_RUN: int = 50

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_PRO: str = ""
    STRIPE_PRICE_ID_ENTERPRISE: str = ""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # LinkedIn OAuth
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""

    # LLM
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""

    # Celery / Task Queue
    CELERY_BROKER_URL: str = "amqp://jobpilot:rabbitmq_pass@rabbitmq:5672/"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # File Storage
    STORAGE_BACKEND: str = "local"  # "local" or "s3"
    STORAGE_LOCAL_PATH: str = "/app/storage"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_S3_REGION: str = "us-east-1"

    # Sentry
    SENTRY_DSN: str = ""

    # Socket.IO
    SOCKETIO_MESSAGE_QUEUE: str = "redis://redis:6379/3"

    # Agent
    AGENT_MAX_APPLICATIONS_PER_DAY: int = 50
    AGENT_COOLDOWN_SECONDS: int = 30
    AGENT_MAX_CONCURRENT_SESSIONS: int = 3

    # Beta limits
    BETA_MAX_TOTAL_APPLICATIONS: int = 10
    ADMIN_EMAILS: str = "paarth.paan3@gmail.com"

    # Domain (for production CORS / TrustedHost)
    DOMAIN: str = "localhost"

    @property
    def admin_email_list(self) -> list[str]:
        """Parse ADMIN_EMAILS into a list."""
        return [e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()]

    @model_validator(mode="after")
    def resolve_environment(self):
        """Use APP_ENV to set ENVIRONMENT if APP_ENV is provided."""
        if self.APP_ENV:
            self.ENVIRONMENT = self.APP_ENV
        return self

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def async_database_url(self) -> str:
        """Ensure the database URL uses asyncpg driver."""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.DATABASE_URL

    @property
    def sync_database_url(self) -> str:
        """Get synchronous database URL for migrations."""
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)


settings = Settings()
