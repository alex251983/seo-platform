# app/api/v1/endpoints/dashboard.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel

from app.core.db import get_async_session
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.rank_tracking.models import RankTrackingProject, TrackedKeyword, PositionHistory
from app.models.billing.models import UserUsageLog
from app.models.seo_data.models import SEOAudit
from app.models.competitors.models import Competitor

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    domain: str
    search_engine: str = "google"
    keywords: Optional[List[str]] = []


class KeywordCreate(BaseModel):
    project_id: int
    keywords: List[str]


class CompetitorCreate(BaseModel):
    domain: str
    name: Optional[str] = None


@router.get("/stats/summary")
async def stats_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    projects_count = (await db.execute(
        select(func.count(RankTrackingProject.id)).where(RankTrackingProject.user_id == user.id)
    )).scalar() or 0

    kw_rows = (await db.execute(
        select(TrackedKeyword)
        .join(RankTrackingProject, TrackedKeyword.project_id == RankTrackingProject.id)
        .where(RankTrackingProject.user_id == user.id)
    )).scalars().all()

    top10 = sum(1 for k in kw_rows if k.current_position and k.current_position <= 10)

    audits = (await db.execute(select(SEOAudit).order_by(desc(SEOAudit.audited_at)).limit(10))).scalars().all()
    avg_score = int(sum(a.score for a in audits if a.score) / len(audits)) if audits else 0

    return {
        "projects_count": projects_count,
        "projects_growth": 0,
        "top10_keywords": top10,
        "top10_growth": 0,
        "top10_percent": round(top10 / max(len(kw_rows), 1) * 100, 1),
        "avg_traffic": 0,
        "traffic_growth": 0,
        "seo_score": avg_score,
        "score_growth": 0,
        "breakdown": {"content": avg_score, "technical": avg_score, "backlinks": 0, "speed": 0},
        "last_update": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/activity/recent")
async def activity_recent(
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    logs = (await db.execute(
        select(UserUsageLog)
        .where(UserUsageLog.user_id == user.id)
        .order_by(desc(UserUsageLog.timestamp))
        .limit(limit)
    )).scalars().all()

    def describe(log):
        ep = log.endpoint or ""
        if "serp" in ep:      text, t = "Проверка SERP-выдачи", "purple"
        elif "audit" in ep:   text, t = "SEO-аудит страницы", "green"
        elif "keyword" in ep: text, t = "Анализ ключевого слова", "blue"
        elif "rank" in ep or "position" in ep: text, t = "Проверка позиций", "purple"
        else:                 text, t = f"Запрос: {ep}", "purple"
        if not log.success:   text, t = text + " (ошибка)", "red"
        return {"text": text, "type": t, "created_at": log.timestamp.isoformat() if log.timestamp else None}

    return {"items": [describe(l) for l in logs]}


@router.get("/positions/changes")
async def positions_changes(
    limit: int = 10,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    rows = (await db.execute(
        select(TrackedKeyword, RankTrackingProject.name.label("project_name"))
        .join(RankTrackingProject, TrackedKeyword.project_id == RankTrackingProject.id)
        .where(RankTrackingProject.user_id == user.id, TrackedKeyword.current_position.isnot(None))
        .order_by(TrackedKeyword.last_checked.desc())
        .limit(limit)
    )).all()

    return {"items": [{
        "keyword": r[0].keyword,
        "position": r[0].current_position,
        "delta": (r[0].previous_position - r[0].current_position)
                 if r[0].previous_position and r[0].current_position else 0,
        "project": r[1],
        "last_checked": r[0].last_checked.isoformat() if r[0].last_checked else None,
    } for r in rows]}


@router.get("/projects")
async def list_projects(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    projects = (await db.execute(
        select(RankTrackingProject)
        .where(RankTrackingProject.user_id == user.id)
        .order_by(desc(RankTrackingProject.created_at))
    )).scalars().all()

    items = []
    for p in projects:
        kw_count = (await db.execute(
            select(func.count(TrackedKeyword.id)).where(TrackedKeyword.project_id == p.id)
        )).scalar() or 0
        top10 = (await db.execute(
            select(func.count(TrackedKeyword.id)).where(
                TrackedKeyword.project_id == p.id,
                TrackedKeyword.current_position <= 10,
                TrackedKeyword.current_position.isnot(None),
            )
        )).scalar() or 0
        items.append({
            "id": p.id, "name": p.name, "domain": p.domain,
            "search_engine": p.search_engine,
            "keywords_count": kw_count, "top10_count": top10,
            "status": "active",
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })
    return {"items": items}


@router.post("/projects")
async def create_project(
    data: ProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    project = RankTrackingProject(
        user_id=user.id, name=data.name, domain=data.domain, search_engine=data.search_engine.lower()
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    for kw in (data.keywords or []):
        kw = kw.strip()
        if kw:
            db.add(TrackedKeyword(project_id=project.id, keyword=kw))
    if data.keywords:
        await db.commit()
    return {"id": project.id, "name": project.name, "domain": project.domain,
            "keywords_count": len([k for k in (data.keywords or []) if k.strip()]), "status": "active"}


@router.get("/keywords")
async def list_keywords(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    rows = (await db.execute(
        select(TrackedKeyword, RankTrackingProject.name.label("project_name"), RankTrackingProject.domain)
        .join(RankTrackingProject, TrackedKeyword.project_id == RankTrackingProject.id)
        .where(RankTrackingProject.user_id == user.id)
        .order_by(TrackedKeyword.current_position.asc().nulls_last())
    )).all()

    return {"items": [{
        "id": r[0].id, "keyword": r[0].keyword,
        "position": r[0].current_position,
        "previous_position": r[0].previous_position,
        "delta": (r[0].previous_position - r[0].current_position)
                 if r[0].previous_position and r[0].current_position else 0,
        "project": r[1], "domain": r[2],
        "last_checked": r[0].last_checked.isoformat() if r[0].last_checked else None,
    } for r in rows]}


@router.post("/keywords")
async def add_keywords(
    data: KeywordCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    project = await db.get(RankTrackingProject, data.project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    added = []
    for kw in data.keywords:
        kw = kw.strip()
        if kw:
            db.add(TrackedKeyword(project_id=data.project_id, keyword=kw))
            added.append(kw)
    await db.commit()
    return {"added": len(added), "keywords": added}


@router.post("/competitors")
async def add_competitor(
    data: CompetitorCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    comp = Competitor(domain=data.domain, name=data.name, user_id=user.id)
    db.add(comp)
    await db.commit()
    await db.refresh(comp)
    return {"id": comp.id, "domain": comp.domain, "name": comp.name}
