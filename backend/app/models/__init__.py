"""
Import all SQLAlchemy models so they are registered with the Base metadata.
This ensures Alembic and other tools can discover all models.
"""

from app.models.user import User, VerificationToken, RefreshToken, Session
from app.models.profile import (
    UserProfile,
    UserEducation,
    UserExperience,
    UserSkill,
    UserCertification,
)
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

__all__ = [
    "User",
    "VerificationToken",
    "RefreshToken",
    "Session",
    "UserProfile",
    "UserEducation",
    "UserExperience",
    "UserSkill",
    "UserCertification",
    "Resume",
    "JobPreferences",
    "PlatformCredentials",
    "Job",
    "JobMatch",
    "Application",
    "ApplicationLog",
    "EmailSettings",
    "EmailTemplate",
    "AgentSettings",
    "Notification",
    "DailyStats",
    "Export",
    "SubscriptionPlan",
    "PaymentHistory",
    "StartupContact",
    "StartupOutreachSettings",
]
