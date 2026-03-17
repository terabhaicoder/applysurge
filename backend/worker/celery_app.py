"""
Celery application configuration for JobPilot.

Configures Celery with RabbitMQ broker, Redis result backend,
task routing, beat schedule, and serialization settings.
"""

import os
from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

# Broker and backend URLs
BROKER_URL = os.environ.get("CELERY_BROKER_URL", "amqp://jobpilot:rabbitmq_pass@rabbitmq:5672/")
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/2")

# Create Celery app
celery_app = Celery(
    "jobpilot",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
)

# Exchanges
default_exchange = Exchange("default", type="direct")
browser_exchange = Exchange("browser", type="direct")
scraping_exchange = Exchange("scraping", type="direct")
email_exchange = Exchange("email", type="direct")

# Queue definitions
celery_app.conf.task_queues = (
    Queue("default", default_exchange, routing_key="default"),
    Queue("browser", browser_exchange, routing_key="browser"),
    Queue("scraping", scraping_exchange, routing_key="scraping"),
    Queue("emails", email_exchange, routing_key="emails"),
)

celery_app.conf.task_default_queue = "default"
celery_app.conf.task_default_exchange = "default"
celery_app.conf.task_default_routing_key = "default"

# Task routing
celery_app.conf.task_routes = {
    # Agent orchestration tasks -> browser queue (long-running)
    "worker.tasks.agent_tasks.run_agent_session": {"queue": "browser"},
    "worker.tasks.agent_tasks.stop_agent_session": {"queue": "default"},
    "worker.tasks.agent_tasks.get_agent_logs": {"queue": "default"},
    "worker.tasks.agent_tasks.validate_credentials_task": {"queue": "browser"},
    # Browser automation tasks -> browser queue
    "worker.tasks.application_task.apply_to_job": {"queue": "browser"},
    "worker.tasks.application_task.process_user_queue": {"queue": "browser"},
    # Scraping tasks -> scraping queue
    "worker.tasks.job_discovery.discover_jobs_for_user": {"queue": "scraping"},
    "worker.tasks.job_discovery.discover_jobs_for_all_users": {"queue": "scraping"},
    # Email tasks -> emails queue
    "worker.tasks.email_task.send_cold_email_task": {"queue": "emails"},
    "worker.tasks.email_task.process_email_response": {"queue": "emails"},
    "worker.tasks.followup_task.send_scheduled_followups": {"queue": "emails"},
    "worker.tasks.scheduled_tasks.send_daily_summaries": {"queue": "emails"},
    # Startup outreach tasks -> scraping and emails queues
    "worker.tasks.startup_outreach_task.discover_startups_task": {"queue": "scraping"},
    "worker.tasks.startup_outreach_task.scrape_startup_contacts_task": {"queue": "scraping"},
    "worker.tasks.startup_outreach_task.send_startup_outreach_task": {"queue": "emails"},
    "worker.tasks.startup_outreach_task.process_startup_pipeline": {"queue": "scraping"},
    "worker.tasks.startup_outreach_task.process_all_users_pipeline": {"queue": "default"},
    # Everything else -> default queue
    "worker.tasks.job_matching.match_jobs_for_user": {"queue": "default"},
    "worker.tasks.analytics_task.update_daily_stats": {"queue": "default"},
    "worker.tasks.scheduled_tasks.reset_daily_limits": {"queue": "default"},
}

# Celery Beat schedule
celery_app.conf.beat_schedule = {
    # Job discovery is triggered by agent session (run_agent_session), not by beat.
    # This prevents background scraping when the user hasn't started the agent.
    "reset-daily-limits": {
        "task": "worker.tasks.scheduled_tasks.reset_daily_limits",
        "schedule": crontab(hour=0, minute=0),  # Daily at midnight
        "options": {"queue": "default"},
    },
    "send-daily-summaries": {
        "task": "worker.tasks.scheduled_tasks.send_daily_summaries",
        "schedule": crontab(hour=20, minute=0),  # Daily at 8 PM
        "options": {"queue": "emails"},
    },
    "update-daily-stats": {
        "task": "worker.tasks.analytics_task.update_daily_stats",
        "schedule": crontab(hour=23, minute=55),  # Daily at 11:55 PM
        "options": {"queue": "default"},
    },
    # Startup outreach: discover daily at 6 AM UTC
    "discover-startups-daily": {
        "task": "worker.tasks.startup_outreach_task.process_all_users_pipeline",
        "schedule": crontab(hour=6, minute=0),  # Daily at 6 AM UTC
        "options": {"queue": "default"},
    },
    # Startup outreach: send batch at 9 AM UTC
    "startup-outreach-morning": {
        "task": "worker.tasks.startup_outreach_task.process_all_users_pipeline",
        "schedule": crontab(hour=9, minute=0),  # Daily at 9 AM UTC
        "options": {"queue": "default"},
    },
    # Startup outreach: send batch at 2 PM UTC
    "startup-outreach-afternoon": {
        "task": "worker.tasks.startup_outreach_task.process_all_users_pipeline",
        "schedule": crontab(hour=14, minute=0),  # Daily at 2 PM UTC
        "options": {"queue": "default"},
    },
}

# Serialization
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "UTC"
celery_app.conf.enable_utc = True

# Task execution settings
# acks_late disabled globally - long-running browser tasks (agent sessions up to 1hr)
# exceed RabbitMQ's default consumer_timeout. Tasks ack immediately on receipt.
celery_app.conf.task_acks_late = False
celery_app.conf.task_reject_on_worker_lost = True
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.worker_max_tasks_per_child = 100
celery_app.conf.worker_max_memory_per_child = 512000  # 512MB

# Task time limits
celery_app.conf.task_soft_time_limit = 300  # 5 minutes soft limit
celery_app.conf.task_time_limit = 600  # 10 minutes hard limit

# Result settings
celery_app.conf.result_expires = 3600  # 1 hour
celery_app.conf.result_backend_transport_options = {
    "visibility_timeout": 3600,
}

# Retry settings
celery_app.conf.task_default_retry_delay = 60  # 1 minute
celery_app.conf.task_max_retries = 3

# Concurrency per queue type
celery_app.conf.worker_concurrency = int(os.environ.get("CELERY_CONCURRENCY", 4))

# Auto-discover tasks
celery_app.autodiscover_tasks([
    "worker.tasks",
])
