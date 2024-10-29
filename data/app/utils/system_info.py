import json
import aiosnmp
import aiofiles
from utils.logging_setup import logger
from utils.config import settings

# This script also needs better error handling if the router or camera is offline or for some reason not responding.
MODEL = settings.OIDS['model']
async def get_snmp_data(host, oid, community=settings.COMMUNITY):
    try:
        async with aiosnmp.Snmp(host=host, community=community, port=161, timeout=5, max_repetitions=5) as snmp:
            response = await snmp.get(oid)
            for varbind in response:
                if varbind.oid == oid:
                    return varbind.value
    except Exception as e:
        await logger.error(f"SNMP request failed: {e}")
        return None

async def rpi_serial():
    try:
        async with aiofiles.open('/proc/cpuinfo', 'r') as f:
            async for line in f:
                if line.startswith('Serial'):
                    return line.split(':')[-1].strip().upper()
    except IOError as e:
        await logger.error(f"Failed to get RPi Serial Number: {e}")
        return None

async def update_rpi_info():
    serial_number = await rpi_serial()
    return {
        'serial': serial_number,
        'system_name': 'R&D Test System'
    }

async def parse_router_info():
    # Retrieve the router model data
    host = settings.ROUTER_IP
    model = await get_snmp_data(host, MODEL)
    if model and isinstance(model, bytes):
        model = model.decode('utf-8', errors='replace')  # Decode model if it's bytes
    serial = None  # Initialize serial number as None
    # If model is retrieved, get the serial number
    if model:
        serial_oid = settings.OIDS['router_serial']
        if serial_oid:
            serial = await get_snmp_data(host, serial_oid)
            if serial and isinstance(serial, bytes):
                # Decode OctetString directly to a string, removing any unwanted characters
                try:
                    serial = serial.decode('utf-8', errors='ignore')
                except UnicodeDecodeError:
                    serial = serial.decode('latin1')
    # Return the decoded model and serial, or None if they are not retrieved
    if model and serial:
        return {
            'model': model,
            'serial_number': serial
        }
    return {
        'model': 'Error retrieving model',
        'serial_sumber': 'Error retrieving serial'
    }

async def parse_camera_info():
    host = settings.CAMERA_IP
    model = await get_snmp_data(host, MODEL)
    serial = await get_snmp_data(host, settings.OIDS['camera_serial'])
    if serial and isinstance(serial, bytes): # Convert serial to a readable string
        serial = ':'.join(f'{byte:02X}' for byte in serial)
        serial = serial.replace(":", "").upper()
    if model and isinstance(model, bytes): # Extract the model from the returned data
        model = model.decode()
        model_parts = model.split(';')
        if len(model_parts) > 1:
            model = model_parts[1].strip()
    if model and serial:
        return {
            'model': model,
            'serial_number': serial
        }
    return {
        'model': 'Error retrieving model',
        'serial_number': 'Error retrieving serial'
    }


async def start_up(path=settings.SYSTEM_INFO_PATH):
    system_info = {
        'RPi': await update_rpi_info(),
        'Router': await parse_router_info(),
        'Camera': await parse_camera_info()
    }
    async with aiofiles.open(path, 'w') as file:
        await file.write(json.dumps(system_info, indent=4))

