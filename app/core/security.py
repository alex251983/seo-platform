# app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Bcrypt имеет жёсткий лимит 72 байта.
    Безопасно обрезаем пароль до 72 байт перед хешированием.
    """
    encoded = password.encode('utf-8')
    if len(encoded) > 72:
        encoded = encoded[:72]
    return pwd_context.hash(encoded.decode('utf-8', 'ignore'))


def create_access_token( dict, expires_delta: Optional[timedelta] = None, scopes: Optional[list[str]] = None) -> str:
    """
    Создание JWT-токена с timezone-aware datetime и scopes.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),  # issued at
        "scope": scopes or ["user"],        # область действия токена
        "env": settings.ENVIRONMENT         # для отладки
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Декодирование и проверка JWT-токена."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return {}


def get_current_user_scope(token_payload: dict) -> list[str]:
    """Получение прав пользователя из токена."""
    return token_payload.get("scope", ["user"])
