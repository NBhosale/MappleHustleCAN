"""
Celery configuration for background tasks in MapleHustleCAN
"""
import os
from celery import Celery
from celery.schedules import crontab
from kombu import Queue

from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "maplehustlecan",
    broker=settings.CELERY_BROKER_URL or settings.REDIS_URL,
    backend=settings.CELERY_RESULT_BACKEND or settings.REDIS_URL,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.sms_tasks", 
        "app.tasks.file_tasks",
        "app.tasks.cleanup_tasks",
        "app.tasks.notification_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "email"},
        "app.tasks.sms_tasks.*": {"queue": "sms"},
        "app.tasks.file_tasks.*": {"queue": "files"},
        "app.tasks.cleanup_tasks.*": {"queue": "cleanup"},
        "app.tasks.notification_tasks.*": {"queue": "notifications"},
    },
    
    # Queue configuration
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("email", routing_key="email"),
        Queue("sms", routing_key="sms"),
        Queue("files", routing_key="files"),
        Queue("cleanup", routing_key="cleanup"),
        Queue("notifications", routing_key="notifications"),
    ),
    
    # Task execution settings
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    
    # Task retry settings
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Worker settings
    worker_hijack_root_logger=False,
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
    
    # Beat schedule (periodic tasks)
    beat_schedule={
        "cleanup-expired-tokens": {
            "task": "app.tasks.cleanup_tasks.cleanup_expired_tokens",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        "cleanup-old-sessions": {
            "task": "app.tasks.cleanup_tasks.cleanup_old_sessions",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
        },
        "cleanup-temp-files": {
            "task": "app.tasks.cleanup_tasks.cleanup_temp_files",
            "schedule": crontab(hour=4, minute=0),  # Daily at 4 AM
        },
        "send-daily-reports": {
            "task": "app.tasks.notification_tasks.send_daily_reports",
            "schedule": crontab(hour=9, minute=0),  # Daily at 9 AM
        },
        "backup-database": {
            "task": "app.tasks.cleanup_tasks.backup_database",
            "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM
        },
    },
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Security
    worker_direct=True,
    task_ignore_result=False,
)

# Set default configuration
celery_app.conf.task_default_queue = "default"


def get_celery_app() -> Celery:
    """Get Celery app instance"""
    return celery_app
