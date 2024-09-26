from fastapi import APIRouter, Depends, status, Request # type: ignore
from fastapi.responses import HTMLResponse, RedirectResponse # type: ignore
from fastapi.templating import Jinja2Templates # type: ignore
from fastapi.exceptions import HTTPException # type: ignore
from core.security import get_current_user, is_admin


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
    if user is None:
        return RedirectResponse(url="/login")
    if not is_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    # Pass both username and role to the template
    return templates.TemplateResponse("index.html", {
        "request": request,
        "username": user["username"],
        "role": user["role"],
        "title": "System Info",
        "system_name": "System", 
        "model": request.app.state.system_info["RPi"]["System_Name"],
        "serial_number": request.app.state.system_info["RPi"]["Serial_Number"],
        "uptime": "99 days",
        "chart_name": "System Power",
        "gauges": [
            {"id": "volts", "title": "Volts"},
            {"id": "watts", "title": "Watts"},
            {"id": "amps", "title": "Amps"}
        ],
    })
    
# Router page route
@router.get("/router", response_class=HTMLResponse)
async def router_page(request: Request, user: dict = Depends(get_current_user)):
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
        "system_name": "Router",
        "model": request.app.state.system_info["Router"]["Model"],
        "serial_number": request.app.state.system_info["Router"]["Serial_Number"],
        "uptime": "99 days",
        "chart_name": "Router Power",
        "gauges": [
            {"id": "volts", "title": "Volts"},
            {"id": "watts", "title": "Watts"},
            {"id": "amps", "title": "Amps"}
        ]
    })
    
# Camera page route
@router.get("/camera", response_class=HTMLResponse)
async def camera_page(request: Request, user: dict = Depends(get_current_user)):
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
        "system_name": "Camera",
        "model": request.app.state.system_info["Camera"]["Model"],
        "serial_number": request.app.state.system_info["Camera"]["Serial_Number"],
        "uptime": "99 days",
        "chart_name": "Camera Power",
        "gauges": [
            {"id": "volts", "title": "Volts"},
            {"id": "watts", "title": "Watts"},
            {"id": "amps", "title": "Amps"}
        ]
    })
    
# Network page route
@router.get("/network", response_class=HTMLResponse)
async def network_page(request: Request, user: dict = Depends(get_current_user)):
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
        "system_name": "Network",
        "model": request.app.state.system_info["Router"]["Model"],
        "serial_number": request.app.state.system_info["Router"]["Serial_Number"],
        "uptime": "99 days",
        "chart_name": "Cellular Signal",
        "gauges": [
            {"id": "rsrp", "title": "RSRP"},
            {"id": "rsrq", "title": "RSRQ"},
            {"id": "sinr", "title": "SINR"}
        ],
    })