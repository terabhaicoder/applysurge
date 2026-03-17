"""
Main API v1 router that includes all sub-routers.
"""

from fastapi import APIRouter

from app.api.v1 import (
    agent,
    analytics,
    applications,
    auth,
    billing,
    credentials,
    email_settings,
    email_templates,
    exports,
    jobs,
    notifications,
    preferences,
    profile,
    resumes,
    startups,
    users,
    websocket,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(profile.router, prefix="/profile", tags=["Profile"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["Resumes"])
api_router.include_router(preferences.router, prefix="/preferences", tags=["Preferences"])
api_router.include_router(credentials.router, prefix="/credentials", tags=["Credentials"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(applications.router, prefix="/applications", tags=["Applications"])
api_router.include_router(agent.router, prefix="/agent", tags=["Agent"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(email_settings.router, prefix="/email/settings", tags=["Email Settings"])
api_router.include_router(email_templates.router, prefix="/email/templates", tags=["Email Templates"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(exports.router, prefix="/exports", tags=["Exports"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing"])
api_router.include_router(startups.router, prefix="/startups", tags=["Startup Outreach"])
api_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
