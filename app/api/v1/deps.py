# app/api/v1/deps.py
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
import uuid
import logging

from app.core.db import get_async_session
from app.models.user import User
from app.models.billing.models import Subscription, SubscriptionTier, UserUsageLog

logger = logging.getLogger(__name__)

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    Получение текущего пользователя из JWT-токена.
    Временная реализация для тестов — замените на полную проверку токена.
    """
    # === ВРЕМЕННАЯ РЕАЛИЗАЦИЯ ДЛЯ ТЕСТОВ ===
    # Берём первого активного пользователя
    result = await db.execute(
        select(User).where(User.is_active == True).limit(1)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="No active users found. Please register first."
        )
    return user

async def check_quota(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Проверка лимита запросов пользователя с отладкой."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔍 check_quota START for user_id={user.id}, email={user.email}")
    
    try:
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        subscription = result.scalar_one_or_none()
        
        now = datetime.now(timezone.utc)
        
        if not subscription:
            logger.info(f"🆕 No subscription found. Creating FREE tier for user {user.id}")
            subscription = Subscription(
                user_id=user.id,
                tier=SubscriptionTier.FREE,
                requests_limit=1,
                requests_used=0,
                period_start=now,
                period_end=now + timedelta(days=30),
                is_active=True
            )
            db.add(subscription)
            await db.commit()
            await db.refresh(subscription)
            logger.info(f"✅ Subscription created: limit={subscription.requests_limit}, used={subscription.requests_used}")
        
        # Сброс если период истёк
        if subscription.period_end and now > subscription.period_end:
            subscription.requests_used = 0
            subscription.period_start = now
            subscription.period_end = now + timedelta(days=30)
            await db.commit()
            await db.refresh(subscription)
            logger.info(f"🔄 Quota reset for user {user.id}")
        
        # Проверка лимита
        if subscription.tier != SubscriptionTier.UNLIMITED and subscription.is_active:
            logger.info(f"📊 Checking limit: used={subscription.requests_used} / limit={subscription.requests_limit}")
            
            if subscription.requests_used >= subscription.requests_limit:
                logger.warning(f"🚫 QUOTA EXCEEDED for user {user.id}")
                usage = UserUsageLog(
                    user_id=user.id,
                    endpoint=request.url.path,
                    request_id=str(uuid.uuid4()),
                    success=False,
                    error_message="quota_exceeded"
                )
                db.add(usage)
                await db.commit()
                
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "quota_exceeded",
                        "message": "Бесплатный лимит исчерпан. Пожалуйста, выберите тариф для продолжения.",
                        "used": subscription.requests_used,
                        "limit": subscription.requests_limit,
                        "reset_at": subscription.period_end.isoformat() if subscription.period_end else None,
                        "upgrade_url": "/api/v1/billing/plans"
                    }
                )
            
            # Инкремент
            subscription.requests_used += 1
            await db.commit()
            await db.refresh(subscription)
            logger.info(f"✅ Request counted: used={subscription.requests_used}")
        
        # Лог использования
        usage = UserUsageLog(
            user_id=user.id,
            endpoint=request.url.path,
            request_id=str(uuid.uuid4()),
            success=True
        )
        db.add(usage)
        await db.commit()
        
    except Exception as e:
        logger.error(f"💥 ERROR in check_quota: {e}", exc_info=True)
        # В случае ошибки БД — НЕ блокируем запрос, чтобы не ломать UX при отладке
        # В продакшене можно заменить на raise HTTPException(500, ...)
        
    return user
