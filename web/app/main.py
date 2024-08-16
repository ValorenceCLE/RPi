from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import os
from routers import api

app = FastAPI()
app.include_router(api.router)
# Load credentials directly from environment variables
USER_USERNAME = os.getenv("USER_USERNAME")
USER_PASSWORD = os.getenv("USER_PASSWORD")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Mount static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Helper function to get the current user
async def get_current_user(request: Request):
    username = request.cookies.get("username")
    print(f"Current user from cookie: {username}")  # Debugging output
    if username is None:
        # Redirect to login page if not authenticated
        return RedirectResponse(url="/login")
    return username


# Helper function to check if the user is an admin
def is_admin(username: str):
    is_admin_user = username == "admin"
    print(f"Is admin check: {is_admin_user}")  # Debugging output
    return is_admin_user


# Home page route
@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request, username: str = Depends(get_current_user)):
    # If user is redirected to login, process that first
    if isinstance(username, RedirectResponse):
        return username

    user_role = "admin" if is_admin(username) else "user"
    return templates.TemplateResponse("home.html", {"request": request, "username": username, "role": user_role})

# Help page route
@app.get("/help", response_class=HTMLResponse)
async def help_page(request: Request, username: str = Depends(get_current_user)):
    # If user is redirected to login, process that first
    if isinstance(username, RedirectResponse):
        return username

    user_role = "admin" if is_admin(username) else "user"
    return templates.TemplateResponse("help.html", {"request": request, "username": username, "role": user_role})

# Alerts page route
@app.get("/alerts", response_class=HTMLResponse)
async def admin_page(request: Request, username: str = Depends(get_current_user)):
    print(f"Accessing /admin with username: {username}")
    
    if isinstance(username, RedirectResponse):
        return username

    if not is_admin(username):
        print("User is not an admin. Access forbidden.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    print("User is an admin. Access granted.")
    # Pass both username and role to the template
    return templates.TemplateResponse("alerts.html", {
        "request": request, 
        "username": username,
        "role": "admin" if is_admin(username) else "user"
    })
# Login page route (GET)
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Login form submission route (POST)
@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    # Check if the entered credentials match either the user or admin credentials
    if (username == "user" and password == "Covert1234") or \
       (username == "admin" and password == "Avscle2010"):
        
        # Set a session cookie for the user
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="username", value=username, max_age=3600)  # Cookie expires in 1 hour
        return response
    else:
        # Return to login page with an error message if credentials are invalid
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

# Logout route
@app.get("/logout", response_class=RedirectResponse)
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("username")  # Remove the session cookie to log out
    return response
@app.get("/system", response_class=HTMLResponse)
async def admin_page(request: Request, username: str = Depends(get_current_user)):
    print(f"Accessing /admin with username: {username}")
    
    if isinstance(username, RedirectResponse):
        return username

    if not is_admin(username):
        print("User is not an admin. Access forbidden.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    print("User is an admin. Access granted.")
    # Pass both username and role to the template
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "System Info", 
        "system_name": "System",
        "model": "R&D System",
        "serial_number": "1234",
        "role": "admin" if is_admin(username) else "user"
    })

@app.get("/router", response_class=HTMLResponse)
async def admin_page(request: Request, username: str = Depends(get_current_user)):
    print(f"Accessing /admin with username: {username}")
    
    if isinstance(username, RedirectResponse):
        return username

    if not is_admin(username):
        print("User is not an admin. Access forbidden.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    print("User is an admin. Access granted.")
    # Pass both username and role to the template
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "title": "Router Info", 
        "system_name": "Router",
        "model": "BR1 Mini",
        "serial_number": "NWAC0F2",
        "role": "admin" if is_admin(username) else "user"
    })
@app.get("/camera", response_class=HTMLResponse)
async def admin_page(request: Request, username: str = Depends(get_current_user)):
    print(f"Accessing /admin with username: {username}")
    
    if isinstance(username, RedirectResponse):
        return username

    if not is_admin(username):
        print("User is not an admin. Access forbidden.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    print("User is an admin. Access granted.")
    # Pass both username and role to the template
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Camera Info",  
        "system_name": "Camera",
        "model": "Q6135",
        "serial_number": "ABC",
        "role": "admin" if is_admin(username) else "user"
    })
@app.get("/network", response_class=HTMLResponse)
async def admin_page(request: Request, username: str = Depends(get_current_user)):
    print(f"Accessing /admin with username: {username}")
    
    if isinstance(username, RedirectResponse):
        return username

    if not is_admin(username):
        print("User is not an admin. Access forbidden.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    print("User is an admin. Access granted.")
    # Pass both username and role to the template
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Network Info",  
        "system_name": "Network",
        "model": "BR1 Mini",
        "serial_number": "NWAC0F2",
        "role": "admin" if is_admin(username) else "user"
    })