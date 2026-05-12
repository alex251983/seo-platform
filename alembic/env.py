# alembic/env.py — ЗАМЕНИТЕ ВЕСЬ ФАЙЛ НА ЭТОТ:
import asyncio
from logging.config import fileConfig
import os
import sys

# Добавляем путь к проекту для импорта моделей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# === Импорт Base и ВСЕХ моделей (чтобы Alembic их видел) ===
from app.models.base import Base
from app.models.user import User
from app.models.seo_data.models import SERPQuery, KeywordData, SEOAudit
from app.models.rank_tracking.models import RankTrackingProject, TrackedKeyword, PositionHistory, PositionAlert
from app.models.competitors.models import Competitor, CompetitorComparison

config = context.config
target_metadata = Base.metadata  # Все модели наследуются от Base

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def get_url():
    """Безопасное получение URL БД из переменных окружения."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://seo:seopass@postgres:5432/seodb"
    )

def run_migrations_offline() -> None:
    """Запуск миграций в "оффлайн-режиме" (без подключения к БД)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    """Запуск миграций с активным подключением."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """Асинхронный запуск миграций (для production)."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    """Точка входа для онлайн-миграций."""
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
