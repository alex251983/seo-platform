# app/modules/seo_data/service.py
from typing import Optional
from app.models.seo_data.providers.openserp import OpenSERPProvider
from app.models.seo_data.providers.yandex_wordstat import YandexWordstatProvider
# Заменяем строку:
# from app.models.seo_data.providers.seo_analyzer import SEOAnalyzerProvider
# На новую:
from app.models.seo_data.providers.xmlriver_provider import XMLRiverProvider
from app.config import settings
import structlog

logger = structlog.get_logger()


class SEODataService:
    """
    Оркестратор SEO-провайдеров.
    Автоматически выбирает подходящего провайдера:
    - SERP: OpenSERP (бесплатный)
    - Ключевые слова: Яндекс.Вордстат (бесплатный, RU)
    - Аудит и расширенные данные: XMLRiver
    """
    def __init__(self):
        self._serp_provider = OpenSERPProvider(
            base_url=getattr(settings, "OPENSERP_URL", "http://openserp:7000")
        )
        self._keyword_provider = YandexWordstatProvider(
            oauth_token=getattr(settings, "YANDEX_OAUTH_TOKEN", ""),
            client_login=getattr(settings, "YANDEX_CLIENT_LOGIN", ""),
        )
        # Инициализируем нового провайдера
        self._xmlriver_provider = XMLRiverProvider(
            user_id=settings.XMLRIVER_USER_ID,
            api_key=settings.XMLRIVER_API_KEY
        )

    async def get_serp(self, keyword: str, engine: str = "google") -> dict:
        # Для SERP используем XMLRiver, как более стабильный
        return await self._xmlriver_provider.get_serp_results(keyword, engine=engine)

    async def get_keyword_volume(self, keyword: str) -> dict:
        # Для частотки используем XMLRiver Wordstat
        return await self._xmlriver_provider.get_keyword_data(keyword)

    async def audit_url(self, url: str) -> dict:
        # Аудит теперь через XMLRiver (базовая проверка)
        return await self._xmlriver_provider.audit_page(url)

    async def full_keyword_analysis(self, keyword: str) -> dict:
        """Комплексный анализ: SERP + частотность + (опционально) аудит"""
        serp_data = await self.get_serp(keyword)
        volume_data = await self.get_keyword_volume(keyword)

        return {
            "keyword": keyword,
            "volume": volume_data.get("frequency", 0),
            "serp_count": serp_data.get("total", 0),
            "serp_results": serp_data.get("results", [])[:10],
            "related_keywords": volume_data.get("related_keywords", []),
        }
