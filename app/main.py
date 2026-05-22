# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from app.api.v1.router import api_router
from app.admin.setup import setup_admin
from app.middleware.logging import LoggingMiddleware
from fastapi_limiter import FastAPILimiter
from pathlib import Path
import redis.asyncio as aioredis
import structlog
import os

logger = structlog.get_logger()

FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "dist"

app = FastAPI(title="SEO Platform", version="0.1.0")

# SessionMiddleware must come before any middleware that touches sessions (sqladmin needs it)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "change-me-32-chars-minimum-here!"))
app.add_middleware(LoggingMiddleware)

Instrumentator().instrument(app).expose(app)


@app.on_event("startup")
async def on_startup():
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    redis = aioredis.from_url(redis_url)
    await FastAPILimiter.init(redis)
    logger.info("Application started")


@app.on_event("shutdown")
async def on_shutdown():
    await FastAPILimiter.close()


# API routes
app.include_router(api_router, prefix="/api/v1")

# Admin panel
setup_admin(app)


@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "ok"}


# Serve frontend static files if built
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def root():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"service": "SEO Platform API", "version": "0.1.0", "docs": "/docs", "admin": "/admin"}


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    # Don't intercept API/admin/docs routes
    for prefix in ("api/", "docs", "openapi.json", "health", "admin", "metrics", "static/"):
        if full_path.startswith(prefix):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse(status_code=404, content={"detail": "Frontend not built"})
