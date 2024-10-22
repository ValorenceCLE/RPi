import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import Response, RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from routers import relay, gauge, graph, signal, alerts, auth, user, admin, line
from core.startup import on_startup
from core.logger import logger
from core.certificate import is_certificate_valid, generate_cert
from core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not is_certificate_valid():
        generate_cert()
    await logger.setup(log_file="web.log")
    await on_startup(app)
    await logger.info("App started")
    yield
    await logger.info("Shutting down...")

app = FastAPI(lifespan=lifespan)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return RedirectResponse(url='/login')
    else:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net https://code.highcharts.com; "
        "style-src 'self' https://cdn.jsdelivr.net; "
        "img-src 'self' data:; "
        "font-src 'self' https://cdn.jsdelivr.net; "
        "connect-src 'self' wss:; "  # Allow any secure WebSocket connection
        "frame-src 'self'; "
    )
    response.headers['X-Frame-Options'] = "DENY"
    response.headers['X-Content-Type-Options'] = "nosniff"
    response.headers['Strict-Transport-Security'] = "max-age=31536000; includeSubDomains"
    response.headers['Referrer-Policy'] = "no-referrer"
    return response

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    logger.info(f"Received request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Sent response: {response.status_code}")
    return response

# Include your routers
app.include_router(auth.router)
app.include_router(relay.router)
app.include_router(gauge.router)
app.include_router(graph.router)
app.include_router(signal.router)
app.include_router(alerts.router)
app.include_router(user.router)
app.include_router(admin.router)
app.include_router(line.router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    # Remove SSL parameters since Nginx handles SSL
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,  # Ensure this matches the proxy_pass in Nginx
        reload=True  # Optional: Enable reload for development
    )
