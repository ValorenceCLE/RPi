
#! -----REFACTORING NOTES-----
#! ----- Remove all template code -----

from fastapi import APIRouter, Depends, status, Request # type: ignore
from fastapi.responses import HTMLResponse, RedirectResponse # type: ignore
from fastapi.templating import Jinja2Templates # type: ignore
from fastapi.exceptions import HTTPException # type: ignore
from core.security import get_current_user, is_admin
from routers.snmp import router_uptime, camera_uptime, rpi_uptime


router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Alerts page route (Needs formatting work)
@router.get("/alerts", response_class=HTMLResponse)
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
@router.get("/system", response_class=HTMLResponse)
async def system_page(request: Request, user: dict = Depends(get_current_user)):
    info = request.app.state.device_info["RPi"] # Get the Raspberry Pi info from the app state
    uptime = rpi_uptime() # Get the Raspberry Pi uptime
    
    if user is None: # Redirect to login if user is not logged in
        return RedirectResponse(url="/login") 
    if not is_admin(user): # Check if the user is an admin
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    # Pass both username and role to the template
    serial = info["serial"]
    return templates.TemplateResponse("index.html", {
        "request": request,
        "username": user["username"],
        "role": user["role"],
        "title": "System Info",
        "page_header": "System Performance", 
        "var1": info["system_name"], # Model, e.g Logan PD DPM #3
        "var2": f"Serial Number: {serial}", # Serial Number
        "var3": f"Uptime: {uptime}", # Uptime
        "chart_name": "System Power Consumption",
        "gauges": [
            {"id": "volts", "title": "Volts"},
            {"id": "watts", "title": "Watts"},
            {"id": "amps", "title": "Amps"}
        ],
    })
    
# Router page route
@router.get("/router", response_class=HTMLResponse)
async def router_page(request: Request, user: dict = Depends(get_current_user)):
    info = request.app.state.device_info["Router"] # Get the Router info from the app state
    uptime = await router_uptime() # Get the Router uptime
    serial = info["serial"]
    if user is None:
        return RedirectResponse(url="/login")
    if not is_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    # Pass both username and role to the template
    return templates.TemplateResponse("index.html", {
        "request": request,
        "username": user["username"],
        "role": user["role"], 
        "title": "Router Info", 
        "page_header": "Router Performance",
        "var1": info["model"],
        "var2": f"Serial Number: {serial}",
        "var3": f"Uptime: {uptime}",
        "chart_name": "Router Power Consumption",
        "gauges": [
            {"id": "volts", "title": "Volts"},
            {"id": "watts", "title": "Watts"},
            {"id": "amps", "title": "Amps"}
        ]
    })
    
# Camera page route
@router.get("/camera", response_class=HTMLResponse)
async def camera_page(request: Request, user: dict = Depends(get_current_user)):
    info = request.app.state.device_info["Camera"] # Get the Camera info from the app state
    uptime = await camera_uptime() # Get the Camera uptime
    serial = info["serial"]
    if user is None:
        return RedirectResponse(url="/login")
    if not is_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    # Pass both username and role to the template
    return templates.TemplateResponse("index.html", {
        "request": request,
        "username": user["username"],
        "role": user["role"],
        "title": "Camera Info",  
        "page_header": "Camera Performance",
        "var1": info["model"],
        "var2": f"Serial Number: {serial}",
        "var3": f"Uptime: {uptime}",
        "chart_name": "Camera Power Consumption",
        "gauges": [
            {"id": "volts", "title": "Volts"},
            {"id": "watts", "title": "Watts"},
            {"id": "amps", "title": "Amps"}
        ]
    })
    
# Network page route
@router.get("/network", response_class=HTMLResponse)
async def network_page(request: Request, user: dict = Depends(get_current_user)):
    info = request.app.state.device_info["Router"] # Get the Router info from the app state
    if user is None:
        return RedirectResponse(url="/login")
    if not is_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    # Pass both username and role to the template
    return templates.TemplateResponse("index.html", {
        "request": request,
        "username": user["username"],
        "role": user["role"],
        "title": "Network Info",  
        "page_header": "Network Performance",
        "var1": "Verizon", # Carrier
        "var2": info["ssid"],
        "var3": info["firmware"],
        "chart_name": "Cellular Signal Strength",
        "gauges": [
            {"id": "rsrp", "title": "RSRP"},
            {"id": "rsrq", "title": "RSRQ"},
            {"id": "sinr", "title": "SINR"}
        ],
    })