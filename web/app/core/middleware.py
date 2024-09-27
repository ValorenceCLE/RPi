from starlette.middleware.base import BaseHTTPMiddleware # type: ignore
from starlette.requests import Request # type: ignore
from typing import Callable
from core.logger import logger


# Async logging middleware
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        await logger.info(f"Received request: {request.method} {request.url}")
        response = await call_next(request)
        await logger.info(f"Sent response: {response.status_code}")
        return response