from starlette.middleware.base import BaseHTTPMiddleware # type: ignore
from fastapi import Request # type: ignore  
from typing import Callable


# Async logging middleware
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        logger = request.app.state.logger
        logger.info(f"Received request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Sent response: {response.status_code}")
        return response