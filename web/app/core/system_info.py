import os
import json
from fastapi import FastAPI # type: ignore

SYSTEM_INFO_PATH = '/device_info/system_info.json'

async def load_system_info(app: FastAPI):
    if os.path.exists(SYSTEM_INFO_PATH):
        with open(SYSTEM_INFO_PATH, mode='r') as file:
            contents = file.read()
            app.state.system_info = json.loads(contents)
    else:
        app.state.system_info = {
            "RPi": {"Serial_Number": "Unknown", "System_Name": "Unknown", "Sensor_ID": "Unknown"},
            "Router": {"Model": "Unknown", "Serial_Number": "Unknown"},
            "Camera": {"Model": "Unknown", "Serial_Number": "Unknown"}
        }