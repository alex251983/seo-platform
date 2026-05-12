"""
Базовый класс SQLAlchemy для всех моделей.
Этот файл НЕ должен импортировать другие модели!
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовый класс для всех моделей БД."""
    pass
