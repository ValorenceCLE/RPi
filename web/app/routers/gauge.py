from fastapi import APIRouter, WebSocket, WebSocketDisconnect #type: ignore
import asyncio
from redis.asyncio import Redis #type: ignore
import json
import os

router = APIRouter()

redis = Redis.from_url(os.getenv('REDIS_URL'))

PRESET_VALUES = {
    "system": {"volts": {"min": 0, "max": 20, "suffix": "V"}, "watts": {"min": 0, "max": 24, "suffix": "W"}, "amps": {"min": 0, "max": 2, "suffix": "A"}},
    "router": {"volts": {"min": 0, "max": 20, "suffix": "V"}, "watts": {"min": 0, "max": 24, "suffix": "W"}, "amps": {"min": 0, "max": 2, "suffix": "A"}},
    "camera": {"volts": {"min": 0, "max": 20, "suffix": "V"}, "watts": {"min": 0, "max": 24, "suffix": "W"}, "amps": {"min": 0, "max": 2, "suffix": "A"}},
    "network": {"rsrp": {"min": -110, "max": -80, "suffix": "dBm"}, "rsrq": {"min": -30, "max": 0, "suffix": "dB"}, "sinr": {"min": -10, "max": 20, "suffix": "dB"}},
    "home": {"volts": {"min": 0, "max": 20, "suffix": "V"}, "temperature": {"min": -32, "max": 120, "suffix": "°F"}, "latency": {"min": 0, "max": 1000, "suffix": "ms"}},

}

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
            print(f"No data found in stream {stream}")
    except Exception as e:
        print(f"Error reading from Redis stream {stream}: {e}")
    return None


# WebSocket endpoint for each page, including the homepage
@router.websocket("/ws/{page_name:path}")
async def websocket_endpoint(websocket: WebSocket, page_name: str):
    await websocket.accept()
    # If the user is on the homepage, handle it accordingly
    if page_name == "" or page_name == "/":
        stream_name = ["system_data", "environment_data", "network_data"]
    else:
        stream_map = {
            "system": "system_data",
            "router": "router_data",
            "camera": "camera_data",
            "network": "cellular_data",
        }
        stream_name = stream_map.get(page_name)

    if not stream_name:
        await websocket.send_text(json.dumps({"error": "Invalid Page Name"}))
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
                    elif stream == "environment_data":
                        data["temperature"] = stream_data.get("temperature", "N/A")
                    elif stream == "network_data":
                        data["latency"] = stream_data.get("avg_rtt", "N/A")

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
        print(f"WebSocket disconnected from {page_name}")
    except Exception as e:
        print(f"Error in WebSocket connection for {page_name}: {e}")
        
# Endpoint to fetch preset values
@router.get("/presets/{page_name}")
async def get_presets(page_name: str):
    presets = PRESET_VALUES.get(page_name)
    if presets:
        return presets
    return {"error": "Invalid Page Name"}

