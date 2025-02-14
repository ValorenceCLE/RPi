
#! -----REFACTORING NOTES-----
#? This will need to be cleaned up a lot.
#? We also may way to move to a more SQLite heavy approach instead of JSON
#! Minimize and consolidate imports, amd .env variables
#TODO: Add type hints/Config validation

import os
import secrets

class Settings:
    # Database/Redis settings
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
    BUCKET = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
    ORG = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
    TOKEN = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
    
    # Authentication/Security related settings   
    HASHED_PASSWORDS_FILE = "/app_data/hashed_passwords.json"
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    USER_USERNAME = os.getenv("USER_USERNAME")
    USER_PASSWORD = os.getenv("USER_PASSWORD")
    SECRET_KEY = secrets.token_hex(32)
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    CERT_DIR = "/etc/nginx/certs"
    CERT_FILE = os.path.join(CERT_DIR, "cert.pem")
    KEY_FILE = os.path.join(CERT_DIR, "key.pem")

    # SNMP settings
    COMMUNITY = 'public'
    ROUTER_IP = '192.168.1.1'
    CAMERA_IP = '192.168.1.3'
    CAMERA_OIDS = {"model": '.1.3.6.1.2.1.1.1.0', "serial": '.1.3.6.1.2.1.2.2.1.6.2'} # Neither Camera nor Router have an OID for uptime
    ROUTER_OIDS = {"model": '.1.3.6.1.2.1.1.1.0', "serial": '.1.3.6.1.4.1.23695.200.1.1.1.1.2.0', "firmware": '.1.3.6.1.4.1.23695.200.1.1.1.1.3.0', "ssid": '.1.3.6.1.4.1.23695.4.2.3.1.2.1',}
    
    # Etc settings
    GPIO_PINS = {"router": 21, "camera": 20, "strobe": 16, "fan": 12}
    STREAM_MAP = {"system": "system_data", "router": "router_data", "camera": "camera_data", "network": "cellular_data",}
    GAUGE_SETTINGS = {
    "system": {"volts": {"min": 0, "max": 20, "suffix": "V"}, "watts": {"min": 0, "max": 24, "suffix": "W"}, "amps": {"min": 0, "max": 2, "suffix": "A"}},
    "router": {"volts": {"min": 0, "max": 20, "suffix": "V"}, "watts": {"min": 0, "max": 24, "suffix": "W"}, "amps": {"min": 0, "max": 2, "suffix": "A"}},
    "camera": {"volts": {"min": 0, "max": 20, "suffix": "V"}, "watts": {"min": 0, "max": 24, "suffix": "W"}, "amps": {"min": 0, "max": 2, "suffix": "A"}},
    "network": {"rsrp": {"min": -110, "max": -80, "suffix": "dBm"}, "rsrq": {"min": -30, "max": 0, "suffix": "dB"}, "sinr": {"min": -10, "max": 20, "suffix": "dB"}},
    "home": {"volts": {"min": 0, "max": 20, "suffix": "V"}, "temperature": {"min": -32, "max": 120, "suffix": "°F"}, "latency": {"min": 0, "max": 1000, "suffix": "ms"}}
    }
    
settings = Settings()