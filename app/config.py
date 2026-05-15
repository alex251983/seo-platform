# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # === Auth & Security ===
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # === Admin ===
    ADMIN_EMAIL: str = "admin@seoviden.ru"
    ADMIN_PASSWORD: str
    
    # === Database ===
    DATABASE_URL: str = "postgresql+asyncpg://seo:seopass@postgres:5432/seodb"
    
    # === Redis & Celery ===
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"
    
    # === External APIs ===
    OPENSERP_URL: str = "http://openserp:7000"
    YANDEX_OAUTH_TOKEN: str = ""
    YANDEX_CLIENT_LOGIN: str = ""
    RAPIDAPI_KEY: str = ""
    XMLRIVER_USER_ID: str = ""
    XMLRIVER_API_KEY: str = ""
    
    # === Environment ===
    ENVIRONMENT: str = "production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# === Валидация на старте (критично для prod!) ===
if len(settings.SECRET_KEY) < 32:
    raise ValueError("❌ SECRET_KEY должен быть минимум 32 символа! Сгенерируйте: python3 -c \"import secrets; print(secrets.token_urlsafe(64))\"")

if settings.ENVIRONMENT == "production" and settings.SECRET_KEY == "change-me":
    raise ValueError("❌ Замените SECRET_KEY в .env перед запуском в production!")
