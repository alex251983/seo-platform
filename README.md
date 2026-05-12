# SEO Platform Skeleton

Готовый каркас для SEO-сервиса на FastAPI.

## Возможности
- Регистрация/вход с JWT
- Асинхронная PostgreSQL
- Фоновые задачи Celery + Redis
- Метрики Prometheus
- Админка (SQLAdmin)
- Логирование structlog

## Быстрый старт
1. Скопируйте `.env.example` в `.env`
2. `docker-compose up --build`
3. API: `http://localhost:8000/docs`
4. Админка: `http://localhost:8000/admin` (admin/admin)

## Миграции
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head