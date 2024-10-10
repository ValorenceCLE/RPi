from fastapi import FastAPI #type: ignore
import uvicorn #type: ignore
from fastapi.staticfiles import StaticFiles #type: ignore
from starlette.middleware.gzip import GZipMiddleware #type: ignore
from contextlib import asynccontextmanager
from core.middleware import LoggingMiddleware
from routers import relay, gauge, graph, signal, alerts, auth, user, admin
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

app.add_middleware(LoggingMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(auth.router)
app.include_router(relay.router)
app.include_router(gauge.router)
app.include_router(graph.router)
app.include_router(signal.router)
app.include_router(alerts.router)
app.include_router(user.router)
app.include_router(admin.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    if not is_certificate_valid():
        generate_cert()

    uvicorn.run(
        "ssl_cert_automation:app",
        host="0.0.0.0",
        port=443,  # Update to port 443 for HTTPS
        ssl_certfile=settings.CERT_FILE,
        ssl_keyfile=settings.KEY_FILE
    )