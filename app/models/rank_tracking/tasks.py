# app/models/rank_tracking/tasks.py
from app.tasks.celery_app import celery_app
from app.core.db import AsyncSessionLocal
from app.models.rank_tracking.models import RankTrackingProject
from app.models.rank_tracking.service import RankTrackingService
from sqlalchemy.future import select
import asyncio


@celery_app.task(name="rank_tracking.check_all_projects")
def check_all_projects_task():
    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(RankTrackingProject))
            projects = result.scalars().all()
            service = RankTrackingService()
            for p in projects:
                await service.check_all_project_keywords(db, p.id)
    asyncio.run(_run())
