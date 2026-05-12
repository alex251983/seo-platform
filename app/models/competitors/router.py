# app/modules/competitors/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_user
from app.core.db import get_async_session
from app.models.competitors.models import Competitor, CompetitorComparison
from app.models.competitors.service import CompetitorService
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/competitors", tags=["Competitors"])


class CompetitorCreate(BaseModel):
    domain: str
    name: Optional[str] = None

class ComparisonRequest(BaseModel):
    keywords: List[str]
    engine: str = "google"

# Зависимость
def get_competitor_service():
    return CompetitorService()


@router.post("/")
async def add_competitor(
    data: CompetitorCreate,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user),
):
    comp = Competitor(domain=data.domain, name=data.name, user_id=user.id)
    db.add(comp)
    await db.commit()
    await db.refresh(comp)
    return comp


@router.get("/")
async def list_competitors(
    db: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user),
):
    from sqlalchemy.future import select
    result = await db.execute(select(Competitor).where(Competitor.user_id == user.id))
    return result.scalars().all()


@router.delete("/{competitor_id}")
async def delete_competitor(
    competitor_id: int,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user),
):
    from sqlalchemy.future import select
    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id, Competitor.user_id == user.id))
    comp = result.scalars().first()
    if not comp:
        raise HTTPException(404, "Competitor not found")
    await db.delete(comp)
    await db.commit()
    return {"ok": True}


@router.post("/compare")
async def compare_competitors(
    data: ComparisonRequest,
    service: CompetitorService = Depends(get_competitor_service),
    db: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user),
):
    # Получаем своих конкурентов
    from sqlalchemy.future import select
    result = await db.execute(select(Competitor).where(Competitor.user_id == user.id))
    competitors = result.scalars().all()
    if not competitors:
        raise HTTPException(400, "Add competitors first")
    domains = [c.domain for c in competitors]
    comparison = await service.compare_competitors(domains, data.keywords, data.engine)
    # Сохраняем сравнение в историю
    history = CompetitorComparison(
        user_id=user.id,
        keywords=data.keywords,
        results=comparison["results"],
    )
    db.add(history)
    await db.commit()
    return comparison


@router.get("/history")
async def comparison_history(
    db: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user),
):
    from sqlalchemy.future import select
    result = await db.execute(
        select(CompetitorComparison).where(CompetitorComparison.user_id == user.id).order_by(CompetitorComparison.created_at.desc())
    )
    return result.scalars().all()