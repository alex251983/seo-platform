# app/models/seo_data/providers/xmlriver.py
import httpx
import logging
from typing import Optional, List, Dict, Any
from app.models.seo_data.providers.base import BaseProvider
from app.config import settings

logger = logging.getLogger(__name__)


class XMLRiverProvider(BaseProvider):
    """
    Провайдер для XMLRiver API.
    Документация: https://xmlriver.ru/api
    """
    
    def __init__(self, user_id: Optional[str] = None, api_key: Optional[str] = None):
        self.user_id = user_id or settings.XMLRIVER_USER_ID
        self.api_key = api_key or settings.XMLRIVER_API_KEY
        self.base_url = "https://api.xmlriver.ru/v1"
        self.timeout = 30.0
        
        if not self.user_id or not self.api_key:
            logger.warning("XMLRiver credentials not configured — using mock mode")
            self._mock_mode = True
        else:
            self._mock_mode = False
    
    def _get_auth_params(self) -> Dict[str, str]:
        """Возвращает параметры авторизации для запросов."""
        return {
            "user_id": self.user_id,
            "api_key": self.api_key
        }
    
    async def _request(self, endpoint: str, params: Optional[Dict] = None, method: str = "GET") -> Dict[str, Any]:
        """Универсальный метод для HTTP-запросов к API."""
        url = f"{self.base_url}/{endpoint}"
        auth_params = self._get_auth_params()
        request_params = {**auth_params, **(params or {})}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, params=request_params)
                else:
                    response = await client.post(url, json=request_params)
                
                response.raise_for_status()
                result = response.json()
                
                # XMLRiver возвращает {status: "ok", data: {...}} или {status: "error", error: "..."}
                if result.get("status") == "error":
                    logger.error(f"XMLRiver API error: {result.get('error')}")
                    raise ValueError(result.get("error", "Unknown API error"))
                
                return result.get("data", {})
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP {e.response.status_code} from XMLRiver: {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error to XMLRiver: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error calling XMLRiver: {e}")
                raise
    
    async def get_keyword_data(self, keyword: str, region: Optional[str] = None) -> Dict[str, Any]:
        """
        Получение данных о ключевом слове через XMLRiver.
        
        Args:
            keyword: Поисковый запрос
            region: Код региона (опционально)
        
        Returns:
            Dict с данными: volume, competition, cpc, trends и т.д.
        """
        if self._mock_mode:
            return self._mock_keyword_data(keyword, region)
        
        try:
            params = {"word": keyword}
            if region:
                params["region"] = region
            
            data = await self._request("keywords/data", params=params)
            
            # Нормализуем ответ в единый формат
            return {
                "keyword": keyword,
                "region": region,
                "volume": int(data.get("search_volume", 0)),
                "competition": data.get("competition_level", "unknown"),
                "cpc": float(data.get("cpc", 0.0)),
                "trends": data.get("monthly_trends", []),
                "related_keywords": data.get("related_words", [])[:10],
                "raw_response": data
            }
            
        except Exception as e:
            logger.warning(f"Failed to fetch keyword data for '{keyword}': {e}")
            # Возвращаем заглушку при ошибке, чтобы не ломать весь запрос
            return self._mock_keyword_data(keyword, region)
    
    async def get_serp_results(self, query: str, limit: int = 10, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Получение результатов выдачи (SERP) через XMLRiver.
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            region: Код региона (опционально)
        
        Returns:
            Список словарей с позициями, заголовками, URL и т.д.
        """
        if self._mock_mode:
            return self._mock_serp_results(query, limit)
        
        try:
            params = {
                "query": query,
                "limit": min(limit, 50),  # XMLRiver лимит: до 50 за запрос
                "device": "desktop"
            }
            if region:
                params["region"] = region
            
            data = await self._request("serp/results", params=params)
            
            # Парсим результаты в единый формат
            results = []
            for item in data.get("organic", [])[:limit]:
                results.append({
                    "position": int(item.get("position", 0)),
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "domain": item.get("domain", ""),
                    "description": item.get("snippet", ""),
                    "favicon": item.get("favicon", ""),
                    "is_ad": False,
                    "raw_data": item
                })
            
            # Добавляем рекламные блоки если есть
            for ad in data.get("ads", [])[:3]:
                results.append({
                    "position": int(ad.get("position", 0)),
                    "title": ad.get("title", ""),
                    "url": ad.get("url", ""),
                    "domain": ad.get("display_url", ""),
                    "description": ad.get("text", ""),
                    "favicon": "",
                    "is_ad": True,
                    "raw_data": ad
                })
            
            # Сортируем по позиции
            results.sort(key=lambda x: x["position"])
            return results[:limit]
            
        except Exception as e:
            logger.warning(f"Failed to fetch SERP for '{query}': {e}")
            return self._mock_serp_results(query, limit)
    
    def _mock_keyword_data(self, keyword: str, region: Optional[str] = None) -> Dict[str, Any]:
        """Заглушка для режима без ключей или при ошибке API."""
        import random
        return {
            "keyword": keyword,
            "region": region,
            "volume": random.randint(100, 10000),
            "competition": random.choice(["low", "medium", "high"]),
            "cpc": round(random.uniform(0.5, 50.0), 2),
            "trends": [random.randint(50, 100) for _ in range(12)],
            "related_keywords": [f"{keyword} купить", f"{keyword} цена", f"лучший {keyword}"],
            "mock": True
        }
    
    def _mock_serp_results(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Заглушка для режима без ключей или при ошибке API."""
        return [
            {
                "position": i + 1,
                "title": f"Результат {i+1} для '{query}'",
                "url": f"https://example{i+1}.com/{query.replace(' ', '-')}",
                "domain": f"example{i+1}.com",
                "description": f"Описание результата поиска для запроса: {query}",
                "favicon": "",
                "is_ad": i == 0,  # Первый результат — реклама (для теста)
                "mock": True
            }
            for i in range(limit)
        ]
    
    async def check_quota(self) -> Dict[str, Any]:
        """Проверка остатка запросов к API (если поддерживается)."""
        if self._mock_mode:
            return {"remaining": 999, "limit": 1000, "reset_at": None}
        
        try:
            data = await self._request("account/quota")
            return {
                "remaining": int(data.get("requests_remaining", 0)),
                "limit": int(data.get("requests_limit", 0)),
                "reset_at": data.get("reset_date"),
                "plan": data.get("plan_name")
            }
        except Exception as e:
            logger.warning(f"Failed to check XMLRiver quota: {e}")
            return {"remaining": 0, "limit": 0, "error": str(e)}
