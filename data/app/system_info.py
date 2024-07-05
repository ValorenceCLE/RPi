import json
import os
from pysnmp.hlapi import *
import logging

path = '/app/device_info/system_info.json'
RETRIES = 3

def get_raspberry_pi_serial_number():
    """Read the Raspberry Pi serial number from /proc/cpuinfo."""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('Serial'):
                    return line.split(':')[-1].strip().upper()
    except IOError:
        logging.error('Could not read /proc/cpuinfo.')
    return None

def raspberry_pi_info():
    """Collect the Raspberry Pi information."""
    serial_number = get_raspberry_pi_serial_number()
    return {
        'Serial_Number': serial_number,
        'System_Name': "R&D Test System",
        'SensorID': serial_number + '-AHT10' if serial_number else None
    }
    
def save():
    with open(path, "w") as info:
        json.dump(raspberry_pi_info(), info)