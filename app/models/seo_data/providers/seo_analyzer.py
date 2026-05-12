# app/modules/seo_data/providers/seo_analyzer.py
import httpx
from typing import Any, Dict, Optional
from app.models.seo_data.providers.base import BaseSEOProvider
import structlog

logger = structlog.get_logger()


class SEOAnalyzerProvider(BaseSEOProvider):
    """
    SEO-аудитор через RapidAPI (фримиум, бесплатных запросов достаточно для MVP).

    API: https://rapidapi.com/restyler/api/seo-analyzer-api
    """

    API_URL = "https://seo-analyzer-api.p.rapidapi.com"

    def __init__(self, rapidapi_key: str):
        super().__init__(api_key=rapidapi_key)
        self._headers = {
            "X-RapidAPI-Key": rapidapi_key,
            "X-RapidAPI-Host": "seo-analyzer-api.p.rapidapi.com",
        }

    async def audit_page(self, url: str) -> Dict[str, Any]:
        """Полный SEO-аудит страницы (19 проверок)"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.API_URL}/analyze",
                    params={"url": url},
                    headers=self._headers,
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "success": True,
                    "url": url,
                    "score": data.get("seo_score"),
                    "title": data.get("title", {}),
                    "meta_description": data.get("meta_description", {}),
                    "headings": data.get("headings", {}),
                    "images": data.get("images", {}),
                    "word_count": data.get("word_count"),
                    "audit_data": data,
                }

        except Exception as e:
            logger.error("SEO audit failed", url=url, error=str(e))
            return {"success": False, "error": str(e)}

    async def get_serp_results(self, keyword: str, **kwargs) -> Dict[str, Any]:
        return {"success": False, "error": "SERP not supported"}

    async def get_keyword_data(self, keyword: str, **kwargs) -> Dict[str, Any]:
        return {"success": False, "error": "Keyword data not supported"}