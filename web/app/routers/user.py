from fastapi import APIRouter, Depends, Request # type: ignore
from fastapi.responses import HTMLResponse, RedirectResponse # type: ignore
from core.security import get_current_user
from fastapi.templating import Jinja2Templates # type: ignore

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Home page route
@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request, user: dict = Depends(get_current_user)):
    if user is None:
        return RedirectResponse(url="/login")
    user_role = user["role"]
    return templates.TemplateResponse("home.html", {"request": request, "username": user["username"], "role": user_role})

#Help Page
@router.get("/help", response_class=HTMLResponse)
async def help_page(request: Request, user: dict = Depends(get_current_user)):
    if user is None:
        return RedirectResponse(url="/login")
    user_role = user["role"]
    return templates.TemplateResponse("help.html", {"request": request, "username": user["username"], "role": user_role})


# Testing 
@router.get("/test")
async def test(request: Request, user: dict = Depends(get_current_user)):
    return {"message": "Hey Pal, Go Fuck Yourself!!!! :)"}