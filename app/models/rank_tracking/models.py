# app/modules/rank_tracking/models.py
from sqlalchemy import Boolean,  Column, Integer, String, DateTime, JSON, ForeignKey, Float, func
from app.models.base import Base

class RankTrackingProject(Base):
    __tablename__ = "rank_tracking_projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False)  # отслеживаемый домен
    search_engine = Column(String(50), default="google")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TrackedKeyword(Base):
    __tablename__ = "tracked_keywords"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("rank_tracking_projects.id"), nullable=False)
    keyword = Column(String(500), nullable=False)
    current_position = Column(Integer, nullable=True)
    previous_position = Column(Integer, nullable=True)
    last_checked = Column(DateTime(timezone=True), nullable=True)

class PositionHistory(Base):
    __tablename__ = "position_history"

    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("tracked_keywords.id"), nullable=False)
    position = Column(Integer, nullable=True)
    checked_at = Column(DateTime(timezone=True), server_default=func.now())

class PositionAlert(Base):
    __tablename__ = "position_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("rank_tracking_projects.id"), nullable=False)
    keyword_id = Column(Integer, ForeignKey("tracked_keywords.id"), nullable=True)  # None = для всех
    direction = Column(String(10), nullable=False)  # "up" или "down"
    threshold = Column(Integer, nullable=False)  # изменение в пунктах
    enabled = Column(Boolean, server_default="true")
