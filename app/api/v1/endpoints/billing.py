# app/api/v1/endpoints/billing.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from typing import List
from pydantic import BaseModel
from app.core.db import get_async_session
from app.models.user import User
from app.models.billing.models import Subscription, SubscriptionTier, Payment
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/billing", tags=["Billing"])


class PlanResponse(BaseModel):
    tier: str
    name: str
    description: str
    requests_per_month: int
    price_rub: float
    features: List[str]


@router.get("/plans", response_model=List[PlanResponse])
async def get_plans():
    return [
        PlanResponse(tier="free", name="Бесплатный", description="1 запрос в месяц для тестирования",
                     requests_per_month=1, price_rub=0,
                     features=["1 запрос/месяц", "Базовый парсинг", "Поддержка по email"]),
        PlanResponse(tier="basic", name="Базовый", description="Для небольших проектов",
                     requests_per_month=100, price_rub=490,
                     features=["100 запросов/месяц", "Все провайдеры", "Приоритетная поддержка"]),
        PlanResponse(tier="pro", name="Профессиональный", description="Для агентств",
                     requests_per_month=1000, price_rub=2990,
                     features=["1000 запросов/месяц", "API доступ", "White-label отчёты"]),
        PlanResponse(tier="unlimited", name="Безлимитный", description="Для enterprise",
                     requests_per_month=-1, price_rub=9990,
                     features=["Безлимитные запросы", "SLA 99.9%", "Выделенный сервер"]),
    ]


@router.get("/subscription")
async def get_subscription(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
    sub = result.scalar_one_or_none()
    if not sub:
        return {"tier": "free", "requests_used": 0, "requests_limit": 1, "reset_at": None, "is_active": True}
    return {
        "tier": sub.tier.value,
        "requests_used": sub.requests_used,
        "requests_limit": sub.requests_limit if sub.tier != SubscriptionTier.UNLIMITED else "unlimited",
        "reset_at": sub.period_end.isoformat() if sub.period_end else None,
        "is_active": sub.is_active,
    }


@router.get("/payments")
async def get_payments(
    skip: int = 0, limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    result = await db.execute(
        select(Payment).where(Payment.user_id == user.id)
        .order_by(Payment.created_at.desc()).offset(skip).limit(limit)
    )
    return [{"id": p.id, "amount": p.amount, "currency": p.currency, "status": p.status,
             "description": p.description, "created_at": p.created_at.isoformat(),
             "receipt_url": p.receipt_url} for p in result.scalars().all()]


@router.post("/upgrade")
async def upgrade_subscription(
    tier: SubscriptionTier,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    return {
        "status": "pending_payment",
        "message": "Для активации тарифа необходимо оплатить счёт",
        "confirmation_url": "https://yookassa.ru/checkout/DEMO_PAYMENT_ID",
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat(),
    }
