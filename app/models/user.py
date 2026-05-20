from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # === Billing relationships ===
    subscription: Mapped["Subscription"] = relationship(  # ← ← ← Обратите внимание на аннотацию типа
        "Subscription", 
        back_populates="user", 
        uselist=False, 
        cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(  # ← ← ← И здесь
        "Payment", 
        back_populates="user"
    )
