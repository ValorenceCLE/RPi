from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
from core.logger import logger


# Async logging middleware
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        await logger.info(f"Received request: {request.method} {request.url}")
        response = await call_next(request)
        await logger.info(f"Sent response: {response.status_code}")
        return response
    
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        response.headers['X-Frame-Options'] = "DENY"
        response.headers['X-Content-Type-Options'] = "nosniff"
        response.headers['Strict-Transport-Security'] = "max-age=31536000; includeSubDomains"
        response.headers['Referrer-Policy'] = "no-referrer"
        return response