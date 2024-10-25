import json
import aiosnmp  # type: ignore
import aiofiles  # type: ignore
from utils.logging_setup import logger

# This script also needs better error handling if the router or camera is offline or for some reason not responding.

MODEL_OID = '.1.3.6.1.2.1.1.1.0'
COMMUNITY = 'public'
PATH = '/device_info/system_info.json'

TARGETS = {
    'Router': {
        'ip': '192.168.1.1',
        'model_oid': MODEL_OID,
        'serial_oids': {
            'Peplink MAX BR1 Mini': '.1.3.6.1.4.1.23695.200.1.1.1.1.2.0',
            'Pepwave MAX BR1 Pro 5G': '.1.3.6.1.4.1.27662.200.1.1.1.1.2.0'
        }
    },
    'Camera': {
        'ip': '192.168.1.3',
        'model_oid': MODEL_OID,
        'serial_oid': '.1.3.6.1.2.1.2.2.1.6.2'
    }
}

async def get_snmp_data(host, oid, community=COMMUNITY):
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
        'Serial_Number': serial_number,
        'System_Name': 'R&D Test System',
        'Sensor_ID': serial_number + '-AHT10' if serial_number else None
    }

async def parse_router_info():
    router_target = TARGETS['Router']
    
    # Retrieve the router model data
    model = await get_snmp_data(router_target['ip'], router_target['model_oid'])
    if model and isinstance(model, bytes):
        model = model.decode('utf-8', errors='replace')  # Decode model if it's bytes
    
    serial = None  # Initialize serial
    
    # If model is retrieved, look up the corresponding serial OID and get the serial number
    if model:
        serial_oid = router_target['serial_oids'].get(model)
        if serial_oid:
            serial = await get_snmp_data(router_target['ip'], serial_oid)
            if serial and isinstance(serial, bytes):
                # Decode OctetString directly to a string, removing any unwanted characters
                try:
                    serial = serial.decode('utf-8', errors='ignore')
                except UnicodeDecodeError:
                    serial = serial.decode('latin1')
    # Return the decoded model and serial, or None if they are not retrieved
    if model and serial:
        return {
            'Model': model,
            'Serial_Number': serial,  # Plain string without colons
            'Sensor_ID': serial + '-INA260'
        }
    return {
        'Model': 'Error retrieving model',
        'Serial_Number': 'Error retrieving serial',
        'Sensor_ID': 'Error retrieving sensor ID'
    }

async def parse_camera_info():
    camera_target = TARGETS['Camera']
    model = await get_snmp_data(camera_target['ip'], camera_target['model_oid'])
    serial = await get_snmp_data(camera_target['ip'], camera_target['serial_oid'])
    
    if serial and isinstance(serial, bytes):
        serial = ':'.join(f'{byte:02X}' for byte in serial)
        serial = serial.replace(":", "").upper()
    
    if model and isinstance(model, bytes):
        model = model.decode()
        model_parts = model.split(';')
        if len(model_parts) > 1:
            model = model_parts[1].strip()
    
    if model and serial:
        return {
            'Model': model,
            'Serial_Number': serial,
            'Sensor_ID': serial + '-INA260'
        }
    return {
        'Model': 'Error retrieving model',
        'Serial_Number': 'Error retrieving serial',
        'Sensor_ID': 'Error retrieving sensor ID'
    }


async def start_up(path=PATH):
    system_info = {
        'RPi': await update_rpi_info(),
        'Router': await parse_router_info(),
        'Camera': await parse_camera_info()
    }
    async with aiofiles.open(path, 'w') as file:
        await file.write(json.dumps(system_info, indent=4))

