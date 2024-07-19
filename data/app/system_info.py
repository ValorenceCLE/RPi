#THIS ENTIRE SCRIPT IS BROKEN SINCE WE CHANGED SNMP
import json
import os
from pysnmp.hlapi import *
import logging

MODEL_OID = '.1.3.6.1.2.1.1.1.0'
RETRIES = 3
COMMUNITY_STRING = 'public'
SYSTEM_INFO_PATH = '/app/device_info/system_info.json'

SNMP_TARGETS = {
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
logging.basicConfig(level=logging.INFO)

def get_snmp_data(ip_address, oid, community_string=COMMUNITY_STRING, retries=RETRIES):
    """Fetch SNMP data using retries for fault tolerance."""
    for attempt in range(retries):
        error_indication, error_status, error_index, var_binds = next(
            getCmd(SnmpEngine(),
                   CommunityData(community_string, mpModel=1),
                   UdpTransportTarget((ip_address, 161), timeout=1, retries=5),
                   ContextData(),
                   ObjectType(ObjectIdentity(oid)))
        )
        if not error_indication and not error_status:
            return var_binds[0][1].prettyPrint()
        logging.warning(f"SNMP attempt {attempt + 1} failed: {error_indication or error_status}")
    return None

def get_rpi_serial():
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('Serial'):
                    return line.split(':')[-1].strip().upper()
    except IOError:
        logging.error('Could not read /proc/cpuinfo.')
        return None
    
def update_rpi_info():
    """Collect the Raspberry Pi information."""
    serial_number = get_rpi_serial()
    return {
        'Serial_Number': serial_number,
        'System_Name': "R&D Test System",
        'Sensor_ID': serial_number + '-AHT10' if serial_number else None
    }
    
def get_device_info(device_name):
    device = SNMP_TARGETS[device_name]
    model = get_snmp_data(device['ip'], device['model_oid'])
    serial = None
    if device_name == 'Router' and model:
        serial_oid = device['serial_oids'].get(model)
        if serial_oid:
            serial = get_snmp_data(device['ip'], serial_oid)
    elif device_name == 'Camera':
        serial = get_snmp_data(device['ip'], device['serial_oid'])
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

def save(file_path=SYSTEM_INFO_PATH):
    system_info = {
        'RPi': update_rpi_info(),
        'Router': get_device_info('Router'),
        'Camera': get_device_info('Camera')
    }
    with open(file_path, 'w') as json_file:
        json.dump(system_info, json_file, indent=4)
        
#Use this file to handle getting Uptime and any other possible SNMP requests for the Front-End Web App.
#Use FastAPI to create a REST API that can be called to quickly get needed info and keeping the load off of the Web App