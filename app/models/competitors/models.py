# app/modules/competitors/models.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float, func
from app.models.base import Base

class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    domain = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)  # название компании
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CompetitorComparison(Base):
    __tablename__ = "competitor_comparisons"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    keywords = Column(JSON, nullable=False)  # ["key1", "key2"]
    results = Column(JSON, nullable=True)    # {domain: {keyword: position, ...}}
    created_at = Column(DateTime(timezone=True), server_default=func.now())