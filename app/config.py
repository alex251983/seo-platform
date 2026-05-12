# app/config.py — ЗАМЕНИТЕ ВЕСЬ ФАЙЛ НА ЭТОТ:
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # === Auth ===
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # === Database ===
    DATABASE_URL: str = "postgresql+asyncpg://seo:seopass@postgres:5432/seodb"

    # === Redis ===
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"
    redis_url: Optional[str] = "redis://redis:6379/0"  # ← ← ← ДОБАВЛЕНО (для FastAPI-Limiter)

    # === External APIs ===
    OPENSERP_URL: str = "http://openserp:7000"
    YANDEX_OAUTH_TOKEN: str = ""
    YANDEX_CLIENT_LOGIN: str = ""
    RAPIDAPI_KEY: str = ""
    XMLRIVER_USER_ID: str = ""
    XMLRIVER_API_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Pydantic v2: разрешаем дополнительные поля из .env (безопасно)
        extra = "ignore"

settings = Settings()
