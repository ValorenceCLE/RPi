from fastapi import FastAPI #type: ignore
from fastapi.staticfiles import StaticFiles #type: ignore
from starlette.middleware.gzip import GZipMiddleware #type: ignore
from core.middleware import LoggingMiddleware
from routers import relay, gauge, graph, signal, alerts, auth, user, admin
from core.startup import on_startup
from core.logger import logger

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await logger.setup(log_file="web.log")
    await on_startup(app)
    await logger.info("App started")
    

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
