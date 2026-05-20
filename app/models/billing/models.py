# app/models/billing/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from uuid import UUID

from app.models.base import Base


class SubscriptionTier(enum.Enum):
    FREE = "free"           # 1 бесплатный запрос
    BASIC = "basic"         # 100 запросов/месяц
    PRO = "pro"             # 1000 запросов/месяц
    UNLIMITED = "unlimited" # без лимита


class Subscription(Base):
    """Подписка пользователя с квотами."""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    
    tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    requests_limit = Column(Integer, default=1)      # лимит запросов в период
    requests_used = Column(Integer, default=0)       # использовано в текущем периоде
    period_start = Column(DateTime(timezone=True), server_default=func.now())
    period_end = Column(DateTime(timezone=True), nullable=True)  # NULL = бессрочно
    
    is_active = Column(Boolean, default=True)
    payment_provider_id = Column(String, nullable=True)  # ID в платёжной системе (ЮKassa и т.д.)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    user = relationship("User", back_populates="subscription")
    payments = relationship("Payment", back_populates="subscription", lazy="select")


class Payment(Base):
    """История платежей."""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    
    amount = Column(Float, nullable=False)  # сумма в рублях
    currency = Column(String, default="RUB")
    status = Column(String, default="pending")  # pending, succeeded, failed, refunded
    payment_id = Column(String, unique=True, index=True)  # ID транзакции в платёжной системе
    description = Column(String, nullable=True)
    receipt_url = Column(Text, nullable=True)  # ссылка на чек
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")


class UserUsageLog(Base):
    """Детальный лог использования (для аналитики и отладки)."""
    __tablename__ = "user_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    endpoint = Column(String, nullable=False)  # например, "/api/v1/seo/serp"
    request_id = Column(String, unique=True, index=True)  # UUID запроса
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    success = Column(Boolean, default=True)
    response_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    user = relationship("User")
