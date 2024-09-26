from fastapi import FastAPI # type: ignore
from core.security import load_hashed_passwords
from core.logging_setup import setup_logging
from core.system_info import load_system_info

async def on_startup(app: FastAPI):
    app.state.hashed_passwords = load_hashed_passwords()
    app.state.logger = await setup_logging(log_file="web.log")
    await load_system_info(app)