# app/models/rank_tracking/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.v1.deps import get_current_user
from app.core.db import get_async_session
from app.models.rank_tracking.service import RankTrackingService
from app.models.rank_tracking.models import (
    RankTrackingProject, TrackedKeyword, PositionHistory, PositionAlert
)
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/rank-tracking", tags=["Rank Tracking"])


class ProjectCreate(BaseModel):
    name: str
    domain: str
    search_engine: str = "google"


class KeywordAdd(BaseModel):
    keyword: str


class AlertCreate(BaseModel):
    project_id: int
    keyword_id: Optional[int] = None
    direction: str
    threshold: int


def get_rank_service():
    return RankTrackingService()


@router.post("/projects")
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user),
):
    project = RankTrackingProject(user_id=user.id, **data.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/projects")
async def list_projects(
    db: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user),
):
    result = await db.execute(select(RankTrackingProject).where(RankTrackingProject.user_id == user.id))
    return result.scalars().all()


@router.post("/projects/{project_id}/keywords")
async def add_keyword(
    project_id: int, data: KeywordAdd,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user),
):
    project = await db.get(RankTrackingProject, project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(404, "Project not found")
    kw = TrackedKeyword(project_id=project_id, keyword=data.keyword)
    db.add(kw)
    await db.commit()
    await db.refresh(kw)
    return kw


@router.get("/projects/{project_id}/keywords")
async def list_keywords(
    project_id: int,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user),
):
    project = await db.get(RankTrackingProject, project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(404, "Project not found")
    result = await db.execute(select(TrackedKeyword).where(TrackedKeyword.project_id == project_id))
    return result.scalars().all()


@router.post("/projects/{project_id}/check")
async def check_positions_now(
    project_id: int,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user),
    service: RankTrackingService = Depends(get_rank_service),
):
    project = await db.get(RankTrackingProject, project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(404, "Project not found")
    await service.check_all_project_keywords(db, project_id)
    return {"status": "check completed"}


@router.get("/projects/{project_id}/history")
async def position_history(
    project_id: int,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user),
):
    project = await db.get(RankTrackingProject, project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(404, "Project not found")
    kw_result = await db.execute(select(TrackedKeyword).where(TrackedKeyword.project_id == project_id))
    history = {}
    for kw in kw_result.scalars().all():
        hist = await db.execute(
            select(PositionHistory).where(PositionHistory.keyword_id == kw.id)
            .order_by(PositionHistory.checked_at)
        )
        history[kw.keyword] = [
            {"position": h.position, "date": h.checked_at.isoformat()}
            for h in hist.scalars().all()
        ]
    return history


@router.post("/alerts")
async def create_alert(
    data: AlertCreate,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user),
):
    alert = PositionAlert(user_id=user.id, **data.model_dump())
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.get("/alerts")
async def list_alerts(db: AsyncSession = Depends(get_async_session), user=Depends(get_current_user)):
    result = await db.execute(select(PositionAlert).where(PositionAlert.user_id == user.id))
    return result.scalars().all()


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_user),
):
    alert = await db.get(PositionAlert, alert_id)
    if not alert or alert.user_id != user.id:
        raise HTTPException(404, "Alert not found")
    await db.delete(alert)
    await db.commit()
    return {"ok": True}
