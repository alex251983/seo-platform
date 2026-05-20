from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, billing
from app.models.seo_data.router import router as seo_router
from app.models.competitors.router import router as competitors_router
from app.models.rank_tracking.router import router as rank_tracking_router


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(seo_router)
api_router.include_router(competitors_router)
api_router.include_router(rank_tracking_router)
api_router.include_router(billing.router, tags=["Billing"])  # ← подключите
