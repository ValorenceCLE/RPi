import os

class Settings:
    TOKEN = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
    ORG = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
    BUCKET = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
    DB_URL = os.getenv('INFLUXDB_URL')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    SYSTEM_INFO_PATH = '/device_info/system_info.json'
    NULL = -9999
    
    
settings = Settings()