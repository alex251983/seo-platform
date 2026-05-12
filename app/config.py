from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = "postgresql+asyncpg://seo:seopass@postgres:5432/seodb"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    OPENSERP_URL: str = "http://openserp:7000"
    YANDEX_OAUTH_TOKEN: str = ""
    YANDEX_CLIENT_LOGIN: str = ""
    RAPIDAPI_KEY: str = ""
    XMLRIVER_USER_ID: str = ""
    XMLRIVER_API_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()