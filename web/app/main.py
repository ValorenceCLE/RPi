from fastapi import FastAPI #type: ignore
from fastapi.staticfiles import StaticFiles #type: ignore
from core.middleware import LoggingMiddleware
from routers import relay, gauge, graph, signal, alerts, auth, user, admin
from core.startup import on_startup

app = FastAPI()

app.include_router(auth.router)
app.include_router(relay.router)
app.include_router(gauge.router)
app.include_router(graph.router)
app.include_router(signal.router)
app.include_router(alerts.router)
app.include_router(user.router)
app.include_router(admin.router)

app.add_middleware(LoggingMiddleware)

@app.on_event("startup")
async def startup_event():
    await on_startup(app)

app.mount("/static", StaticFiles(directory="static"), name="static")
