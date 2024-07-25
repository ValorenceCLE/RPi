import json
import asyncio
import aiosnmp # type: ignore
import aiofiles # type: ignore

MODEL_OID = '.1.3.6.1.2.1.1.1.0'
SYSTEM_NAME = '.1.3.6.1.2.1.1.5.0'
COMMUNITY = 'public'
PATH = '/app/device_info/system_info.json'

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
        print(f"SNMP request failed: {e}")
        return None
    
async def rpi_serial():
    try:
        async with aiofiles.open('/proc/cpuinfo', 'r') as f:
            async for line in f:
                if line.startswith('Serial'):
                    return line.split(':')[-1].strip().upper()
    except IOError as e:
        print(f"Failed to get RPi Serial Number: {e}")
        return None

async def update_rpi_info():
    serial_number = await rpi_serial()
    return {
        'Serial_Number': serial_number,
        'System_Name': 'R&D Test System',
        'Sensor_ID': serial_number + '-AHT10' if serial_number else None
    }

async def get_device_info(device_name):
    device = TARGETS[device_name]
    model = await get_snmp_data(device['ip'], device['model_oid'])
    serial = None
    if device_name == 'Router' and model:
        serial_oid = device['serial_oids'].get(model)
        if serial_oid:
            serial = await get_snmp_data(device['ip'], serial_oid)
    elif device_name == 'Camera':
        serial = await get_snmp_data(device['ip'], device['serial_oid'])
        if serial:
            serial = serial.split('0x')[1].strip().upper()
        if model:
            model = model.split(';')[1].strip()
    
    if model and serial:
        return {
            'Model': model,
            'Serial_Number': serial,
            'Sensor_ID': serial + '-INA260'
        }
    return None

async def save(path=PATH):
    system_info = {
        'RPi': await update_rpi_info(),
        'Router': await get_device_info('Router'),
        'Camera': await get_device_info('Camera')
    }
    async with aiofiles.open(path, 'w') as file:
        await file.write(json.dumps(system_info, indent=4))
        
if __name__ == "__main__":
    asyncio.run(save())
