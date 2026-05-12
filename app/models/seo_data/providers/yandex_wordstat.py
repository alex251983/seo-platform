# app/modules/seo_data/providers/yandex_wordstat.py
import httpx
from typing import Any, Dict, Optional
from app.models.seo_data.providers.base import BaseSEOProvider
import structlog

logger = structlog.get_logger()


class YandexWordstatProvider(BaseSEOProvider):
    """
    Бесплатный API Яндекс.Вордстат (бета).

    Требуется:
    1. OAuth-токен Яндекса
    2. Заявка на доступ: https://yandex.ru/support2/wordstat/ru/content/api-wordstat
    """

    API_URL = "https://api.direct.yandex.ru/v5/wordstat"

    def __init__(self, oauth_token: str, client_login: str):
        super().__init__(api_key=oauth_token)
        self.client_login = client_login
        self._headers = {
            "Authorization": f"Bearer {oauth_token}",
            "Client-Login": client_login,
            "Accept-Language": "ru",
        }

    async def get_keyword_data(
        self,
        keyword: str,
        region_ids: Optional[list] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Получение данных по ключевым словам из Вордстата.

        Docs: https://yandex.ru/dev/direct/doc/ref-v5/wordstat/wordstat_get.html
        """
        try:
            payload = {
                "method": "get",
                "params": {
                    "SelectionCriteria": {
                        "Keywords": [keyword],
                        "RegionIds": region_ids or [225],  # 225 = Россия
                    },
                    "FieldNames": [
                        "Keyword",
                        "Impressions",
                        "KeywordsStatistics",
                    ],
                },
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.API_URL,
                    json=payload,
                    headers=self._headers,
                )
                response.raise_for_status()
                data = response.json()

                # Парсим результат
                stats = data.get("result", {}).get("KeywordsStatistics", [])
                if stats:
                    keyword_stat = stats[0]
                    return {
                        "success": True,
                        "keyword": keyword,
                        "frequency": keyword_stat.get("Impressions", 0),
                        "related_keywords": [
                            {
                                "keyword": k.get("Keyword"),
                                "frequency": k.get("Impressions"),
                            }
                            for k in keyword_stat.get("KeywordsStatistics", [])[:10]
                        ],
                    }

                return {"success": False, "error": "No data in response"}

        except Exception as e:
            logger.error("Wordstat request failed", keyword=keyword, error=str(e))
            return {"success": False, "error": str(e)}

    async def get_serp_results(self, keyword: str, **kwargs) -> Dict[str, Any]:
        """Вордстат не предоставляет SERP"""
        return {"success": False, "error": "SERP not supported by Wordstat"}