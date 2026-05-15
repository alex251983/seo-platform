# app/tasks/celery_app.py
from celery import Celery
from app.config import settings

celery_app = Celery(
    "seo_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,  # ← включили сохранение результатов
    include=["app.tasks.example"]
)

# Надёжные настройки для production
celery_app.conf.update(
    result_expires=3600,  # результаты задач живут 1 час
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,  # ← авто-переподключение к Redis
    timezone="UTC",
    enable_utc=True,
)

# Перечень модулей, в которых Celery ищет задачи
celery.conf.update(
    imports=[
        "app.tasks.example",          # наша тестовая задача
        "app.models.rank_tracking.tasks", "app.models.seo_data.tasks",  # задачи отслеживания позиций
        # здесь можно добавлять другие модули
    ],
    # Расписание (beat schedule) — если нужно запускать по крону
    beat_schedule={
        "check-positions-every-hour": {
            "task": "rank_tracking.check_all_projects",
            "schedule": 3600.0,  # каждый час
        },
    },
)
