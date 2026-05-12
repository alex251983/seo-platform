# app/modules/rank_tracking/tasks.py
from celery import shared_task
from app.tasks.celery_app import celery
from app.core.db import AsyncSessionLocal
from app.models.rank_tracking.models import RankTrackingProject
from app.models.rank_tracking.service import RankTrackingService
from sqlalchemy.future import select
import asyncio

@celery.task(name="rank_tracking.check_all_projects")
def check_all_projects_task():
    """Запускает проверку всех активных проектов (может вызываться по расписанию)."""
    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(RankTrackingProject))
            projects = result.scalars().all()
            service = RankTrackingService()
            for p in projects:
                await service.check_all_project_keywords(db, p.id)
    asyncio.run(_run())