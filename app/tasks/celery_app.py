from celery import Celery
from app.config import settings

celery = Celery(
    "seo-tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
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