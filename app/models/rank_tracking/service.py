# app/models/rank_tracking/service.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.rank_tracking.models import (
    RankTrackingProject, TrackedKeyword, PositionHistory, PositionAlert
)
from app.models.seo_data.providers.openserp import OpenSERPProvider
import structlog

logger = structlog.get_logger()


class RankTrackingService:
    def __init__(self, serp_provider=None):
        self.serp = serp_provider or OpenSERPProvider()

    async def check_keyword(self, keyword: str, domain: str, engine: str = "google") -> Optional[int]:
        serp = await self.serp.get_serp_results(keyword, engine=engine, limit=50)
        if not serp.get("success"):
            return None
        for idx, item in enumerate(serp.get("results", []), start=1):
            if domain in item.get("link", ""):
                return idx
        return None

    async def update_keyword_position(
        self, db: AsyncSession, tracked_kw: TrackedKeyword, domain: str, engine: str
    ):
        new_pos = await self.check_keyword(tracked_kw.keyword, domain, engine)
        old_pos = tracked_kw.current_position
        tracked_kw.previous_position = old_pos
        tracked_kw.current_position = new_pos
        tracked_kw.last_checked = func.now()

        db.add(PositionHistory(keyword_id=tracked_kw.id, position=new_pos))
        await db.commit()

        if old_pos is not None and new_pos is not None:
            diff = old_pos - new_pos
            direction = "up" if diff > 0 else "down"
            abs_change = abs(diff)
            alerts_result = await db.execute(
                select(PositionAlert).where(
                    PositionAlert.project_id == tracked_kw.project_id,
                    PositionAlert.enabled == True,
                    PositionAlert.threshold <= abs_change,
                    PositionAlert.direction == direction,
                )
            )
            for alert in alerts_result.scalars().all():
                logger.info("Alert triggered", keyword=tracked_kw.keyword, change=diff, direction=direction)

        return new_pos

    async def check_all_project_keywords(self, db: AsyncSession, project_id: int):
        project = await db.get(RankTrackingProject, project_id)
        if not project:
            return
        result = await db.execute(select(TrackedKeyword).where(TrackedKeyword.project_id == project_id))
        for kw in result.scalars().all():
            await self.update_keyword_position(db, kw, project.domain, project.search_engine)
