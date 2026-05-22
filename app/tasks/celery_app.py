# app/tasks/celery_app.py
from celery import Celery
from app.config import settings

celery_app = Celery(
    "seo_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.example",
        "app.models.rank_tracking.tasks",
        "app.models.seo_data.tasks",
    ]
)

celery_app.conf.update(
    result_expires=3600,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "check-positions-every-hour": {
            "task": "rank_tracking.check_all_projects",
            "schedule": 3600.0,
        },
    },
)

# Backwards-compatible alias
celery = celery_app
