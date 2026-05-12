# app/modules/seo_data/models.py
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey, func
from app.models.base import Base

class SERPQuery(Base):
    """Сохранённые SERP-запросы"""
    __tablename__ = "serp_queries"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(500), nullable=False)
    engine = Column(String(50), nullable=False)  # google, yandex, bing
    language = Column(String(10), default="ru")
    results = Column(JSON, nullable=True)  # [{position, url, title, description}]
    total_results = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KeywordData(Base):
    """Данные по ключевым словам из Яндекс.Вордстат"""
    __tablename__ = "keyword_data"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(500), nullable=False)
    frequency = Column(Integer, nullable=True)
    related_keywords = Column(JSON, nullable=True)
    region = Column(String(100), nullable=True)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())


class SEOAudit(Base):
    """Результаты SEO-аудита"""
    __tablename__ = "seo_audits"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), nullable=False)
    score = Column(Float, nullable=True)
    title_status = Column(String(50), nullable=True)
    meta_status = Column(String(50), nullable=True)
    h1_count = Column(Integer, nullable=True)
    images_with_alt = Column(Integer, nullable=True)
    total_images = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    audit_data = Column(JSON, nullable=True)
    audited_at = Column(DateTime(timezone=True), server_default=func.now())