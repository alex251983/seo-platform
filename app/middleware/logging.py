import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            "request handled",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=round(process_time, 4),
        )
        response.headers["X-Process-Time"] = str(process_time)
        return response