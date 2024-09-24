from fastapi import FastAPI, Depends, HTTPException, status, Request, Form #type: ignore
from fastapi.staticfiles import StaticFiles #type: ignore
from fastapi.templating import Jinja2Templates #type: ignore
from fastapi.responses import HTMLResponse, RedirectResponse #type: ignore
from starlette.middleware.base import BaseHTTPMiddleware #type: ignore
#from starlette.requests import Request #type: ignore
from typing import Callable
import json
from routers import relay, gauge, graph, signal, alerts, auth, user
from core.logging_setup import setup_logging
from core.security import load_hashed_passwords, is_admin, get_current_user
import aiofiles # type: ignore
import os

app = FastAPI()

app.include_router(auth.router)
app.include_router(relay.router)
app.include_router(gauge.router)
app.include_router(graph.router)
app.include_router(signal.router)
app.include_router(alerts.router)
app.include_router(user.router)

# Hash Passwords
@app.on_event("startup")
async def startup_hash():
    app.state.hashed_passwords = load_hashed_passwords()
# Set up Logging on startup
@app.on_event("startup")
async def startup_event():
    app.state.logger = await setup_logging(log_file="web.log")
    
# Middleware to log incoming requests and responses
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        logger = app.state.logger
        logger.info(f"Received request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Sent response: {response.status_code}")
        return response

# Attatch the middleware to the app
app.add_middleware(LoggingMiddleware)

# System Info Caching
# Maybe add a new file to handle SNMP requests to get things like uptime periodically
SYSTEM_INFO_PATH = '/device_info/system_info.json'
@app.on_event("startup")
async def load_system_info():
    if os.path.exists(SYSTEM_INFO_PATH):
        async with aiofiles.open(SYSTEM_INFO_PATH, mode='r') as file:
            contents = await file.read()
            app.state.system_info = json.loads(contents)
    else:
        app.state.system_info = {
            "RPi": {"Serial_Number": "Unknown", "System_Name": "Unknown", "Sensor_ID": "Unknown"}, 
            "Router": {"Model": "Unknown", "Serial_Number": "Unknown"}, 
            "Camera": {"Model": "Unknown", "Serial_Number": "Unknown"}}

# Mount static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Alerts page route
@app.get("/alerts", response_class=HTMLResponse)
async def alert_page(request: Request, user: dict = Depends(get_current_user)):
    if user is None:
        return RedirectResponse(url="/login")
    if not is_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    # Pass both username and role to the template
    return templates.TemplateResponse("alerts.html", {
        "request": request, 
        "username": user["username"],
        "role": user["role"]
    })
    
# System page route
@app.get("/system", response_class=HTMLResponse)
async def system_page(request: Request, username: str = Depends(get_current_user)):    
    if isinstance(username, RedirectResponse):
        return username
    if not is_admin(username):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    # Pass both username and role to the template
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "System Info",
        "system_name": "System", 
        "model": app.state.system_info["RPi"]["System_Name"],
        "serial_number": app.state.system_info["RPi"]["Serial_Number"],
        "uptime": "99 days",
        "chart_name": "System Power",
        "gauges": [
            {"id": "volts", "title": "Volts"},
            {"id": "watts", "title": "Watts"},
            {"id": "amps", "title": "Amps"}
        ],
        "role": "admin" if is_admin(username) else "user"
    })
    
# Router page route
@app.get("/router", response_class=HTMLResponse)
async def router_page(request: Request, username: str = Depends(get_current_user)):
    if isinstance(username, RedirectResponse):
        return username
    if not is_admin(username):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    # Pass both username and role to the template
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "title": "Router Info", 
        "system_name": "Router",
        "model": app.state.system_info["Router"]["Model"],
        "serial_number": app.state.system_info["Router"]["Serial_Number"],
        "uptime": "99 days",
        "chart_name": "Router Power",
        "gauges": [
            {"id": "volts", "title": "Volts"},
            {"id": "watts", "title": "Watts"},
            {"id": "amps", "title": "Amps"}
        ],
        "role": "admin" if is_admin(username) else "user"
    })
# Camera page route
@app.get("/camera", response_class=HTMLResponse)
async def camera_page(request: Request, username: str = Depends(get_current_user)):
    if isinstance(username, RedirectResponse):
        return username
    if not is_admin(username):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    # Pass both username and role to the template
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Camera Info",  
        "system_name": "Camera",
        "model": app.state.system_info["Camera"]["Model"],
        "serial_number": app.state.system_info["Camera"]["Serial_Number"],
        "uptime": "99 days",
        "chart_name": "Camera Power",
        "gauges": [
            {"id": "volts", "title": "Volts"},
            {"id": "watts", "title": "Watts"},
            {"id": "amps", "title": "Amps"}
        ],
        "role": "admin" if is_admin(username) else "user"
    })

@app.get("/network", response_class=HTMLResponse)
async def network_page(request: Request, username: str = Depends(get_current_user)):
    if isinstance(username, RedirectResponse):
        return username
    if not is_admin(username):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    # Pass both username and role to the template
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Network Info",  
        "system_name": "Network",
        "model": app.state.system_info["Router"]["Model"],
        "serial_number": app.state.system_info["Router"]["Serial_Number"],
        "uptime": "99 days",
        "chart_name": "Cellular Signal",
        "gauges": [
            {"id": "rsrp", "title": "RSRP"},
            {"id": "rsrq", "title": "RSRQ"},
            {"id": "sinr", "title": "SINR"}
        ],
        "role": "admin" if is_admin(username) else "user"
    })