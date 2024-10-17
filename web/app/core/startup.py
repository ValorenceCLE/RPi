from fastapi import FastAPI # type: ignore
#from core.security import load_hashed_passwords
from core.system_info import load_system_info

async def on_startup(app: FastAPI):
    #app.state.hashed_passwords = load_hashed_passwords()
    await load_system_info(app)