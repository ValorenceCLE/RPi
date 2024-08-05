from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
#from app.routers import api

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

#app.include_router(api.router)

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/help")
async def login(request: Request):
    return templates.TemplateResponse("help.html", {"request": request})

@app.get("/test")
async def login(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})