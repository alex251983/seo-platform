# app/modules/seo_data/providers/openserp.py
import httpx
from typing import Any, Dict, Optional
from app.models.seo_data.providers.base import BaseSEOProvider
import structlog

logger = structlog.get_logger()


class OpenSERPProvider(BaseSEOProvider):
    """
    Бесплатный SERP-провайдер через OpenSERP.

    Требуется запущенный Docker-контейнер:
    docker run -p 7000:7000 -it karust/openserp serve -a 0.0.0.0 -p 7000
    """

    def __init__(self, base_url: str = "http://openserp:7000"):
        super().__init__()
        self.base_url = base_url

    async def get_serp_results(
        self,
        keyword: str,
        engine: str = "google",
        limit: int = 30,
        language: str = "ru",
        **kwargs
    ) -> Dict[str, Any]:
        """
        engine: google, yandex, bing, duckduckgo, baidu
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Используем Megasearch для агрегации (если нужно)
                response = await client.get(
                    f"{self.base_url}/{engine}/search",
                    params={
                        "text": keyword,
                        "limit": limit,
                        "lang": language.upper(),
                    },
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "success": True,
                    "keyword": keyword,
                    "engine": engine,
                    "results": data,
                    "total": len(data) if isinstance(data, list) else 0,
                }

        except Exception as e:
            logger.error("OpenSERP request failed", keyword=keyword, error=str(e))
            return {"success": False, "error": str(e)}

    async def get_keyword_data(self, keyword: str, **kwargs) -> Dict[str, Any]:
        """OpenSERP не предоставляет данные частотности — возвращаем SERP"""
        serp_data = await self.get_serp_results(keyword, **kwargs)
        return {
            "success": serp_data.get("success"),
            "keyword": keyword,
            "serp_count": serp_data.get("total"),
            "note": "OpenSERP not provides keyword volume",
        }