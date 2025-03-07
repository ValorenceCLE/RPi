
#! -----REFACTORING NOTES-----
#! This file will need major changes to work with the new Vue frontend
#! Maybe just delete it and make a more generic WS handler


import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect #type: ignore
from redis.asyncio import Redis #type: ignore
from core.config import settings
from core.logger import logger


router = APIRouter()
redis = Redis.from_url(settings.REDIS_URL)
PRESET_VALUES = settings.GAUGE_SETTINGS
STREAM_MAP = settings.STREAM_MAP

#Function to get the most recent data from Redis
async def get_live_data(stream: str):
    try:
        response = await redis.xrevrange(stream, count=1)
        if response:
            _, data = response[0]
            # Decode and round only numeric values, skip the timestamp
            decoded_data = {k.decode(): round(float(v.decode()), 1) if k.decode() != "timestamp" else v.decode() for k, v in data.items()}
            return decoded_data
        else:
            await logger.warning(f"No data found in stream {stream}")
    except Exception as e:
        await logger.error(f"Error reading from Redis stream {stream}: {e}")
    return None

# WebSocket endpoint for each page, including the homepage
@router.websocket("/ws/{page_name:path}")
async def websocket_endpoint(websocket: WebSocket, page_name: str):
    await websocket.accept()
    if page_name == "" or page_name == "/": # If the user is on the homepage, handle it accordingly
        stream_name = ["system_data", "environmental", "network"]
    else:
        stream_name = STREAM_MAP.get(page_name)
    if not stream_name:
        await websocket.send_text(json.dumps({"error": "Invalid Page Name"}))
        await logger.error(f"Invalid Page Name: {page_name}")
        return
    try:
        while True:
            # For homepage, handle multiple streams
            if page_name == "" or page_name == "/":
                data = {}
                for stream in stream_name:
                    stream_data = await get_live_data(stream)
                    if stream == "system_data":
                        data["volts"] = stream_data.get("volts", "N/A")
                    elif stream == "environmental":
                        data["temperature"] = stream_data.get("temperature", "N/A")
                    elif stream == "network":
                        data["avg_rtt"] = stream_data.get("avg_rtt", "N/A")

                if data:
                    await websocket.send_text(json.dumps(data))
                else:
                    await websocket.send_text(json.dumps({"error": "No data available"}))
            else:
                # For other pages, handle a single stream
                data = await get_live_data(stream_name)
                if data:
                    await websocket.send_text(json.dumps(data))
                else:
                    await websocket.send_text(json.dumps({"error": "No data available"}))

            await asyncio.sleep(30)  # Send updates every 30 seconds
    except WebSocketDisconnect:
        await logger.info(f"WebSocket disconnected from {page_name}")
    except Exception as e:
        await logger.error(f"Error in WebSocket connection for {page_name}: {e}")
        
# Endpoint to fetch preset values
@router.get("/presets/{page_name}")
async def get_presets(page_name: str):
    presets = PRESET_VALUES.get(page_name)
    if presets:
        return presets
    return {"error": "Invalid Page Name"}

