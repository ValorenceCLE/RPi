import os

class Settings:
    # Database/Redis settings
    TOKEN = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
    ORG = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
    BUCKET = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
    INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # SNMP settings
    COMMUNITY = 'public'
    ROUTER_IP = '192.168.1.1'
    CAMERA_IP = '192.168.1.3'
    OIDS = {
        'model': '.1.3.6.1.2.1.1.1.0',
        'router_serial': '.1.3.6.1.4.1.23695.200.1.1.1.1.2.0',
        'camera_serial': '.1.3.6.1.2.1.2.2.1.6.2'
    }
    CELLULAR_OIDS = {
        'sinr_oid': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.5.0',
        'rsrp_oid': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.7.0',
        'rsrq_oid': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.8.0'
    }
    # Etc settings
    HOST = '192.168.1.1'
    SYSTEM_INFO_PATH = '/device_info/system_info.json'
    NULL = -9999
    COLLECTION_INTERVAL = 30  # Interval in seconds between data collections
    ALERT_FILE = 'alerts.json'
    PING_TARGET = '8.8.8.8'
settings = Settings()