# app/modules/seo_data/router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.v1.deps import get_current_user
from app.models.seo_data.service import SEODataService
from pydantic import BaseModel, Field

router = APIRouter(prefix="/seo", tags=["SEO Data"])


# Схемы запросов
class SERPRequest(BaseModel):
    keyword: str
    engine: str = Field(default="google", description="google, yandex, bing, duckduckgo")

class KeywordRequest(BaseModel):
    keyword: str

class AuditRequest(BaseModel):
    url: str


# Сервис (можно вынести в dependency)
def get_seo_service():
    return SEODataService()


@router.post("/serp")
async def get_serp_data(
    request: SERPRequest,
    service: SEODataService = Depends(get_seo_service),
    user=Depends(get_current_user),
):
    """Получить SERP-результаты по ключевому слову"""
    result = await service.get_serp(request.keyword, engine=request.engine)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/keywords")
async def get_keyword_volume(
    request: KeywordRequest,
    service: SEODataService = Depends(get_seo_service),
    user=Depends(get_current_user),
):
    """Получить частотность ключевого слова (Яндекс.Вордстат)"""
    result = await service.get_keyword_volume(request.keyword)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/audit")
async def audit_page(
    request: AuditRequest,
    service: SEODataService = Depends(get_seo_service),
    user=Depends(get_current_user),
):
    """Запустить SEO-аудит страницы"""
    result = await service.audit_url(request.url)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/analyze")
async def analyze_keyword(
    keyword: str = Query(...),
    service: SEODataService = Depends(get_seo_service),
    user=Depends(get_current_user),
):
    """Комплексный анализ ключевого слова (SERP + частотность)"""
    return await service.full_keyword_analysis(keyword)


@router.get("/providers")
async def list_providers(
    user=Depends(get_current_user),
):
    """Список доступных провайдеров"""
    return {
        "serp": "OpenSERP (free, Docker-based)",
        "keywords": "Yandex Wordstat API (free, beta)",
        "audit": "XMLRiver (paid, Russian-friendly)", # Обновлено
    }