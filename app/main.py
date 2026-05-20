# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from app.api.v1.router import api_router
from app.admin.setup import setup_admin
from app.core.db import engine, Base
from app.middleware.logging import LoggingMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from fastapi.responses import FileResponse
from pathlib import Path
import redis.asyncio as aioredis
import structlog
import os

logger = structlog.get_logger()

app = FastAPI(title="SEO Platform", version="0.1.0")

# === Middleware (порядок важен!) ===
# 1. LoggingMiddleware — первым, чтобы логировать все запросы
app.add_middleware(LoggingMiddleware)

# 2. Prometheus metrics
Instrumentator().instrument(app).expose(app)

# === Rate Limiting: кастомный обработчик 429 (опционально, но полезно) ===
async def http429_handler(request: Request, respond):
    """Красивый ответ при превышении лимита запросов."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests. Please slow down.",
            "retry_after_seconds": 30
        },
        headers={"Retry-After": "30"}
    )

# === Инициализация при старте (ОБЪЕДИНЁННАЯ) ===
@app.on_event("startup")
async def on_startup():
    """
    Единая точка инициализации:
    1. Rate Limiter (Redis)
    2. Создание таблиц БД (только для dev-режима!)
    """
    # 1. Инициализация Rate Limiter
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    await FastAPILimiter.init(aioredis.from_url(redis_url))
    FastAPILimiter.http429_handler = http429_handler  # ← кастомный ответ 429
    
    # 2. Создание таблиц БД (⚠️ только для разработки! В продакшене используйте Alembic)
    if os.getenv("ENVIRONMENT", "production") != "production":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created (dev mode)")
    else:
        logger.info("Production mode: skipping auto table creation (use Alembic migrations)")

# === Корректное завершение работы ===
@app.on_event("shutdown")
async def on_shutdown():
    """Закрываем соединения с Redis при остановке приложения."""
    await FastAPILimiter.close()
    logger.info("FastAPI-Limiter connections closed")

# === Роутеры ===
app.include_router(api_router, prefix="/api/v1")
# ===== FRONTEND: SPA ROUTING =====
FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "dist"

@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    """Раздаёт index.html для всех путей, кроме API и документации."""
    # Исключаем системные и API-маршруты
    if full_path.startswith(("api/", "docs", "openapi.json", "health", "static/")):
        return {"detail": "Not Found"}
    
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"detail": "Frontend not built"}
# === Админ-панель ===
setup_admin(app)

# === Health check (без лимита — для мониторинга) ===
# === Health check endpoint ===
@app.get("/health", include_in_schema=False)
async def health_check():
    """Простая проверка здоровья сервиса."""
    return {"status": "ok"}

# === Корневой эндпоинт (заглушка) ===
@app.get("/")
async def root():
    return {
        "service": "SEO Platform API",
        "version": "0.1.0",
        "docs": "/docs",
        "admin": "/admin",
        "health": "/health"
    }
