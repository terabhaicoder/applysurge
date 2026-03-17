"""
JobPilot Worker Module.

Celery-based task processing for job discovery, matching, application automation,
email campaigns, and analytics.
"""

from worker.celery_app import celery_app

__all__ = ["celery_app"]
