import os

class Settings:
    TOKEN = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
    ORG = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
    BUCKET = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
    DB_URL = os.getenv('INFLUXDB_URL')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    HOST = '192.168.1.1'
    SYSTEM_INFO_PATH = '/device_info/system_info.json'
    NULL = -9999
    COLLECTION_INTERVAL = 30  # Interval in seconds between data collections
    OID_MAPPINGS = {
        'sinr_oid': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.5.0',
        'rsrp_oid': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.7.0',
        'rsrq_oid': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.8.0'
        }
    ALERT_FILE = 'alerts.json'
    PING_TARGET = '8.8.8.8'
    
settings = Settings()