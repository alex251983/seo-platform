# app/modules/seo_data/providers/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import structlog

logger = structlog.get_logger()


class BaseSEOProvider(ABC):
    """Базовый класс для всех SEO-провайдеров"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    @abstractmethod
    async def get_serp_results(self, keyword: str, **kwargs) -> Dict[str, Any]:
        """Получить результаты SERP"""
        pass

    @abstractmethod
    async def get_keyword_data(self, keyword: str, **kwargs) -> Dict[str, Any]:
        """Получить данные по ключевому слову"""
        pass

    def is_available(self) -> bool:
        """Проверка доступности провайдера"""
        return True