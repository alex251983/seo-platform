import httpx
from typing import Optional, List
from app.models.seo_data.models import SERPQuery, KeywordData
from .base import BaseSEOProvider


class XMLRiverProvider(BaseSEOProvider):
    """
    Провайдер для XMLRiver API (https://xmlriver.com)
    Реализация через httpx (асинхронный, совместим с FastAPI).
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.xmlriver.ru"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
    
    async def search_yandex(
        self, 
        query: str, 
        domain: Optional[str] = None,
        limit: int = 10
    ) -> List[dict]:
        """Парсинг выдачи Яндекс через XMLRiver."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "query": query,
                "api_key": self.api_key,
                "limit": limit,
                "device": "desktop",
                "lang": "ru",
                "region": "213",
            }
            if domain:
                params["domain"] = domain
                
            response = await client.get(
                f"{self.base_url}/yandex/search",
                params=params
            )
            response.raise_for_status()
            return response.json().get("results", [])
    
    async def get_wordstat(
        self, 
        keyword: str, 
        region_id: int = 213
    ) -> List[KeywordData]:
        """Получение данных Wordstat через XMLRiver."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "keyword": keyword,
                "api_key": self.api_key,
                "region_id": region_id,
            }
            response = await client.get(
                f"{self.base_url}/wordstat",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            return [
                KeywordData(
                    keyword=item["keyword"],
                    searches=item["searches"],
                    competition=item.get("competition", 0)
                )
                for item in data.get("results", [])
            ]
