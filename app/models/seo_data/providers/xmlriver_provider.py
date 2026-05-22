import httpx
from typing import Optional, Dict, Any
from .base import BaseSEOProvider
import structlog

logger = structlog.get_logger()


class XMLRiverProvider(BaseSEOProvider):
    """Провайдер для XMLRiver API (https://xmlriver.com)."""

    def __init__(self, user_id: str = "", api_key: str = "", base_url: str = "https://api.xmlriver.ru"):
        super().__init__(api_key=api_key)
        self.user_id = user_id
        self.base_url = base_url.rstrip("/")

    async def get_serp_results(self, keyword: str, engine: str = "google", limit: int = 10, **kwargs) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "XMLRiver API key not configured", "results": [], "total": 0}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/{engine}/search",
                    params={"query": keyword, "api_key": self.api_key, "limit": limit, "device": "desktop", "lang": "ru"},
                )
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])
                return {"success": True, "keyword": keyword, "engine": engine, "results": results, "total": len(results)}
        except Exception as e:
            logger.error("XMLRiver SERP failed", keyword=keyword, error=str(e))
            return {"success": False, "error": str(e), "results": [], "total": 0}

    async def get_keyword_data(self, keyword: str, region_id: int = 213, **kwargs) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "XMLRiver API key not configured"}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/wordstat",
                    params={"keyword": keyword, "api_key": self.api_key, "region_id": region_id},
                )
                response.raise_for_status()
                data = response.json()
                return {"success": True, "keyword": keyword, "frequency": data.get("frequency", 0),
                        "related_keywords": data.get("related", [])}
        except Exception as e:
            logger.error("XMLRiver Wordstat failed", keyword=keyword, error=str(e))
            return {"success": False, "error": str(e)}

    async def audit_page(self, url: str, **kwargs) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "XMLRiver API key not configured"}
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(f"{self.base_url}/audit", params={"url": url, "api_key": self.api_key})
                response.raise_for_status()
                data = response.json()
                return {"success": True, "url": url, "score": data.get("score", 0), "audit_data": data}
        except Exception as e:
            logger.error("XMLRiver audit failed", url=url, error=str(e))
            return {"success": False, "error": str(e)}
