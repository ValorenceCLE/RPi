from fastapi import APIRouter, Request, Form, Depends, Response, status # type: ignore
from fastapi.responses import RedirectResponse, HTMLResponse # type: ignore
from core.security import verify_password, get_current_user
from core.config import settings
from fastapi.templating import Jinja2Templates # type: ignore

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Dependency to get the hashed passwords
def get_hashed_passwords(request: Request):
    return request.app.state.hashed_passwords

# Login Page
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Login submission
@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    hashed_passwords: dict = Depends(get_hashed_passwords),
):
    # Authenticate User
    if username == hashed_passwords["USER_USERNAME"] and verify_password(password, hashed_passwords["USER_PASSWORD_HASH"]):
        role = "user"
    elif username == hashed_passwords["ADMIN_USERNAME"] and verify_password(password, hashed_passwords["ADMIN_PASSWORD_HASH"]):
        role = "admin"
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="username",
        value=username,
        max_age=3600,
        httponly=True,
        samesite="Lax"
    )
    return response

# Logout route
@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("username")
    return response