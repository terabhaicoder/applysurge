"""
JobPilot task modules.

All Celery tasks for job discovery, matching, application processing,
email campaigns, followups, analytics, and scheduled maintenance.
"""

from worker.tasks.job_discovery import discover_jobs_for_all_users, discover_jobs_for_user
from worker.tasks.job_matching import match_jobs_for_user
from worker.tasks.application_task import process_queues, process_user_queue, apply_to_job
from worker.tasks.email_task import send_cold_email_task, process_email_response
from worker.tasks.followup_task import send_scheduled_followups
from worker.tasks.analytics_task import update_daily_stats
from worker.tasks.scheduled_tasks import reset_daily_limits, send_daily_summaries
from worker.tasks.agent_tasks import run_agent_session, stop_agent_session, get_agent_logs

__all__ = [
    "discover_jobs_for_all_users",
    "discover_jobs_for_user",
    "match_jobs_for_user",
    "process_queues",
    "process_user_queue",
    "apply_to_job",
    "send_cold_email_task",
    "process_email_response",
    "send_scheduled_followups",
    "update_daily_stats",
    "reset_daily_limits",
    "send_daily_summaries",
    "run_agent_session",
    "stop_agent_session",
    "get_agent_logs",
]
