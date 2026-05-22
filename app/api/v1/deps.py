# app/api/v1/deps.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
import uuid
import jwt

from app.core.db import get_async_session
from app.models.user import User
from app.models.billing.models import Subscription, SubscriptionTier, UserUsageLog
from app.config import settings
import structlog

logger = structlog.get_logger()

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_async_session),
) -> User:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated. Provide Authorization: Bearer <token>",
        )
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


async def check_quota(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> User:
    try:
        result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
        subscription = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)

        if not subscription:
            subscription = Subscription(
                user_id=user.id,
                tier=SubscriptionTier.FREE,
                requests_limit=1,
                requests_used=0,
                period_start=now,
                period_end=now + timedelta(days=30),
                is_active=True,
            )
            db.add(subscription)
            await db.commit()
            await db.refresh(subscription)

        if subscription.period_end:
            period_end = subscription.period_end
            if period_end.tzinfo is None:
                period_end = period_end.replace(tzinfo=timezone.utc)
            if now > period_end:
                subscription.requests_used = 0
                subscription.period_start = now
                subscription.period_end = now + timedelta(days=30)
                await db.commit()
                await db.refresh(subscription)

        if subscription.tier != SubscriptionTier.UNLIMITED and subscription.is_active:
            if subscription.requests_used >= subscription.requests_limit:
                db.add(UserUsageLog(
                    user_id=user.id,
                    endpoint=request.url.path,
                    request_id=str(uuid.uuid4()),
                    success=False,
                    error_message="quota_exceeded",
                ))
                await db.commit()
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "quota_exceeded",
                        "message": "Бесплатный лимит исчерпан. Пожалуйста, выберите тариф.",
                        "used": subscription.requests_used,
                        "limit": subscription.requests_limit,
                        "reset_at": subscription.period_end.isoformat() if subscription.period_end else None,
                        "upgrade_url": "/api/v1/billing/plans",
                    },
                )
            subscription.requests_used += 1
            await db.commit()

        db.add(UserUsageLog(
            user_id=user.id,
            endpoint=request.url.path,
            request_id=str(uuid.uuid4()),
            success=True,
        ))
        await db.commit()

    except HTTPException:
        raise
    except Exception as e:
        logger.error("check_quota error", error=str(e))

    return user
