# app/models/seo_data/tasks.py
from app.tasks.celery_app import celery_app
from app.models.seo_data.service import SEODataService
from app.core.db import AsyncSessionLocal
from app.models.seo_data.models import SERPQuery, KeywordData, SEOAudit
import asyncio
import structlog

logger = structlog.get_logger()


@celery_app.task(name="seo.collect_serp")
def collect_serp_task(keyword: str, engine: str = "google"):
    async def _run():
        service = SEODataService()
        result = await service.get_serp(keyword, engine)
        if result.get("success"):
            async with AsyncSessionLocal() as db:
                record = SERPQuery(
                    keyword=keyword,
                    engine=engine,
                    results=result.get("results"),
                    total_results=result.get("total"),
                )
                db.add(record)
                await db.commit()
                logger.info("SERP saved", keyword=keyword, engine=engine)
    asyncio.run(_run())


@celery_app.task(name="seo.collect_keyword_volume")
def collect_keyword_volume_task(keyword: str):
    async def _run():
        service = SEODataService()
        result = await service.get_keyword_volume(keyword)
        if result.get("success"):
            async with AsyncSessionLocal() as db:
                record = KeywordData(
                    keyword=keyword,
                    frequency=result.get("frequency"),
                    related_keywords=result.get("related_keywords"),
                )
                db.add(record)
                await db.commit()
                logger.info("Keyword volume saved", keyword=keyword)
    asyncio.run(_run())


@celery_app.task(name="seo.audit_page")
def audit_page_task(url: str):
    async def _run():
        service = SEODataService()
        result = await service.audit_url(url)
        if result.get("success"):
            async with AsyncSessionLocal() as db:
                record = SEOAudit(
                    url=url,
                    score=result.get("score"),
                    audit_data=result.get("audit_data"),
                )
                db.add(record)
                await db.commit()
                logger.info("Audit saved", url=url, score=result.get("score"))
    asyncio.run(_run())
