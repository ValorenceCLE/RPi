
#! -----REFACTORING NOTES-----
#! -----DELETE THIS FILE-----
#? This file is not needed anymore

import aiosnmp
import aiofiles
from fastapi import FastAPI, APIRouter, Request
from core.config import settings
from core.logger import logger

router = APIRouter()

async def snmp_engine(host, oid, community=settings.COMMUNITY):
    try:
        async with aiosnmp.Snmp(host=host, community=community, port=161, timeout=5, max_repetitions=5) as snmp:
            response = await snmp.get(oid)
            for varbind in response:
                if varbind.oid == oid:
                    return varbind.value
    except Exception as e:
        await logger.error(f"SNMP request failed: {e}")
        return None

async def load_device_info(app: FastAPI):
    # Initialize the device info dictionary
    app.state.device_info = {
        "RPi": {"serial": "Unknown", "system_name": "R&D Demo System"},
        "Router": {"model": "Unknown", "serial": "Unknown", "ssid": "Unknown", "firmware": "Unknown"},
        "Camera": {"model": "Unknown", "serial": "Unknown"}
    }
    
    # Fetch the data from the Raspberry Pi
    serial = await rpi_serial()
    system_name = "R&D Demo System"
    rpi_info = {"serial": serial, "system_name": system_name}
    
    # Fetch the SNMP data for the Router
    router_info = {}
    for name, oid in settings.ROUTER_OIDS.items():
        result = await snmp_engine(settings.ROUTER_IP, oid)
        result = result.decode('utf-8')
        router_info[name] = result
        
    # Fetch the SNMP data for the Camera
    camera_info = {}
    for name, oid in settings.CAMERA_OIDS.items():
        result = await snmp_engine(settings.CAMERA_IP, oid)
        if name == "serial" and isinstance(result, bytes):
            result = ':'.join(f'{byte:02X}' for byte in result)
            result = result.replace(':','').upper()
        if name == "model" and isinstance(result, bytes):
            result = result.decode()
            result_parts = result.split(';')
            if len(result_parts) > 1:
                result = result_parts[1].strip()
        camera_info[name] = result
        
    app.state.device_info["RPi"] = rpi_info
    app.state.device_info["Router"] = router_info
    app.state.device_info["Camera"] = camera_info
        
def format_uptime(uptime_data: int, is_ticks: bool) -> str:
    if is_ticks:
        ticks = int(uptime_data)
        seconds = ticks // 100
    else:
        seconds = uptime_data
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    uptime = []
    if days > 0:
        uptime.append(f"{days}d")
    if hours > 0:
        uptime.append(f"{hours}h")
    if minutes > 0:
        uptime.append(f"{minutes}m")
    return " ".join(uptime) or "0s"    

async def rpi_serial():
    try:
        async with aiofiles.open('/proc/cpuinfo', 'r') as f:
            async for line in f:
                if line.startswith('Serial'):
                    return line.split(':')[-1].strip().upper()
    except IOError as e:
        await logger.error(f"Failed to get RPi Serial Number: {e}")
        return None
    
def rpi_uptime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        uptime_seconds = int(uptime_seconds)
        result = format_uptime(uptime_seconds, False)
        return result

async def router_uptime():
    oid = '.1.3.6.1.2.1.25.1.1.0'
    result = await snmp_engine(settings.ROUTER_IP, oid)
    return format_uptime(result, True)

async def camera_uptime():
    oid = '.1.3.6.1.2.1.1.3.0'
    result = await snmp_engine(settings.CAMERA_IP, oid)
    return format_uptime(result, True)

@router.get('/snmp/info')
async def snmp_info(request: Request):
    await load_device_info(request.app)
    data = request.app.state.device_info
    router = await router_uptime()
    camera = await camera_uptime()
    rpi = rpi_uptime()
    uptime = {"router": router, "camera": camera, "rpi": rpi}
    return {"device_info": data, "uptime": uptime}
    
    
    