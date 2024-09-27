import os

class Settings:
    """
    A class to hold all configuration settings for the application.
    """
    HASHED_PASSWORDS_FILE = "/app_data/hashed_passwords.json"
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    USER_USERNAME = os.getenv("USER_USERNAME")
    USER_PASSWORD = os.getenv("USER_PASSWORD")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    GPIO_PINS = {"router": 21, "camera": 20, "strobe": 16, "fan": 12}
    GAUGE_SETTINGS = {
    "system": {"volts": {"min": 0, "max": 20, "suffix": "V"}, "watts": {"min": 0, "max": 24, "suffix": "W"}, "amps": {"min": 0, "max": 2, "suffix": "A"}},
    "router": {"volts": {"min": 0, "max": 20, "suffix": "V"}, "watts": {"min": 0, "max": 24, "suffix": "W"}, "amps": {"min": 0, "max": 2, "suffix": "A"}},
    "camera": {"volts": {"min": 0, "max": 20, "suffix": "V"}, "watts": {"min": 0, "max": 24, "suffix": "W"}, "amps": {"min": 0, "max": 2, "suffix": "A"}},
    "network": {"rsrp": {"min": -110, "max": -80, "suffix": "dBm"}, "rsrq": {"min": -30, "max": 0, "suffix": "dB"}, "sinr": {"min": -10, "max": 20, "suffix": "dB"}},
    "home": {"volts": {"min": 0, "max": 20, "suffix": "V"}, "temperature": {"min": -32, "max": 120, "suffix": "°F"}, "latency": {"min": 0, "max": 1000, "suffix": "ms"}}}
    STREAM_MAP = {"system": "system_data", "router": "router_data", "camera": "camera_data", "network": "cellular_data",}
    INFLUXDB_URL = os.getenv('INFLUXDB_URL')
    BUCKET = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
    ORG = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
    TOEKN = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
    
    
settings = Settings()