import os
from utils.logging_setup import local_logger as logger

class Settings:
    def rpi_serial(self):
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('Serial'):
                        return line.split(':')[-1].strip().upper()
        except IOError as e:
            logger.error(f"Failed to get RPi Serial Number: {e}")
            return None
        
    # Database settings
    TOKEN = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
    ORG = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
    BUCKET = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
    INFLUXDB_URL = os.getenv('INFLUXDB_URL')

    # Redis settings
    REDIS_URL = os.getenv('REDIS_URL')

    # AWS settings
    CERT_DIR=os.getenv('CERT_DIR')
    AWS_REGION=os.getenv('AWS_REGION')
    AWS_ENDPOINT=os.getenv('AWS_ENDPOINT')
    AWS_CLIENT_ID = rpi_serial()
    AWS_ROOT_CA=os.getenv('AWS_ROOT_CA')
    DEVICE_ROOT_KEY=os.getenv('DEVICE_ROOT_KEY')
    DEVICE_ROOT_PEM=os.getenv('DEVICE_ROOT_PEM')
    DEVICE_KEY=os.getenv('DEVICE_KEY') # These may need to be a function call to make sure they are loaded correctly/exist
    DEVICE_CSR=os.getenv('DEVICE_CSR')
    DEVICE_CRT=os.getenv('DEVICE_CRT')
    COMBINED_CERTIFICATE=os.getenv('DEVICE_COMBINED_CRT')

    # Certificate subject attributes
    COUNTRY_NAME = "US"
    STATE_NAME = "Utah"
    LOCALITY_NAME = "Logan"
    ORGANIZATION_NAME = "Valorence"
    ORGANIZATIONAL_UNIT_NAME = "RPi"

    # MQTT settings
    DATA_TOPIC = f"{AWS_CLIENT_ID}/data"
    COMMAND_TOPIC = f"{AWS_CLIENT_ID}/command"
    ALERT_TOPIC = f"{AWS_CLIENT_ID}/alert"
    ERROR_TOPIC = f"{AWS_CLIENT_ID}/error"

    # System settings
    SERIAL_NUMBER1= rpi_serial()

    # SNMP settings
    COMMUNITY = 'public'
    SNMP_TARGET = '192.168.1.1'
    OIDS = {'sinr': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.5.0','rsrp': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.7.0','rsrq': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.8.0'}
    
    # Network/Ping settings
    PING_TARGET = '8.8.8.8'
    NULL = -9999 # Value to use for missing data, may need to be adjusted based on data type
    

settings = Settings()