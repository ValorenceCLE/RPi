import os
from functools import lru_cache
from utils.logging_setup import local_logger as logger

class Settings:
    @lru_cache(maxsize=1)
    def rpi_serial(self):
        """
        Get the Raspberry Pi serial number from /proc/cpuinfo.
        """
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('Serial'):
                        return line.split(':')[-1].strip().lower()
        except IOError as e:
            logger.error(f"Failed to get RPi Serial Number: {e}")
            return None

    def __init__(self):        
        # Database settings
        self.TOKEN = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
        self.ORG = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
        self.BUCKET = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
        self.INFLUXDB_URL = os.getenv('INFLUXDB_URL')

        # Redis settings
        self.REDIS_URL = os.getenv('REDIS_URL')

        # AWS settings
        self.AWS_CLIENT_ID = self.rpi_serial()  # Uses the cached result
        self.AWS_REGION = os.getenv('AWS_REGION')  # AWS Region (us-east-1)
        self.AWS_ENDPOINT = os.getenv('AWS_ENDPOINT')  # AWS IoT endpoint
        self.CERT_DIR = os.getenv('CERT_DIR')  # Directory to store certs
        self.AWS_ROOT_CA = os.getenv('AWS_ROOT_CA')  # Required
        self.DEVICE_ROOT_KEY = os.getenv('DEVICE_ROOT_KEY')  # Required for Generating Device Certs
        self.DEVICE_ROOT_PEM = os.getenv('DEVICE_ROOT_PEM')  # Required for Generating Device Certs
        self.DEVICE_KEY = os.getenv('DEVICE_KEY')  # Generated private key
        self.DEVICE_CSR = os.getenv('DEVICE_CSR')  # Generated CSR
        self.DEVICE_CRT = os.getenv('DEVICE_CRT')  # Generated CRT
        self.DEVICE_COMBINED_CRT = os.getenv('DEVICE_COMBINED_CRT')  # Generated combined CRT

        # Certificate subject attributes
        self.COUNTRY_NAME = "US"
        self.STATE_NAME = "Utah"
        self.LOCALITY_NAME = "Logan"
        self.ORGANIZATION_NAME = "Valorence"
        self.ORGANIZATIONAL_UNIT_NAME = "RPi"

        # MQTT settings
        self.DATA_TOPIC = f"{self.AWS_CLIENT_ID}/data"
        self.COMMAND_TOPIC = f"{self.AWS_CLIENT_ID}/command"
        self.ALERT_TOPIC = f"{self.AWS_CLIENT_ID}/alert"
        self.ERROR_TOPIC = f"{self.AWS_CLIENT_ID}/error"

        # System settings
        self.SERIAL_NUMBER = self.rpi_serial()  # Uses the cached result

        # SNMP settings
        self.COMMUNITY = 'public'
        self.SNMP_TARGET = '192.168.1.1'
        self.OIDS = {
            'sinr': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.5.0',
            'rsrp': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.7.0',
            'rsrq': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.8.0',
        }
        
        # Network/Ping settings
        self.PING_TARGET = '8.8.8.8'

        # Data collection settings
        self.COLLECTION_INTERVAL = 30
        self.NULL = -9999  # Value to use for missing data, may need to be adjusted based on data type

settings = Settings()
