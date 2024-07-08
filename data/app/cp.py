#Camera Power
#Naming Convention: Camera Number - Sensor Name
#i.e: B8A44F7FF4C2-INA260
import os
import time
import board
import adafruit_ina260
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS, WriteOptions

class INA260Camera:
    def __init__(self):
        i2c = board.I2C()  # Setup I2C connection
        self.ina260 = adafruit_ina260.INA260(i2c, address=0x41)  # Initialize INA260 sensor
        # Load environment variables
        self.token = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
        self.org = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
        self.bucket = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
        self.url = os.getenv('INFLUXDB_URL')
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=WriteOptions(write_type=SYNCHRONOUS))
        
        self.prev_volt = None
        self.prev_watt = None
        self.prev_amp = None

    def get_current_amps(self):
        return round(self.ina260.current / 1000, 2)

    def get_voltage_volts(self):
        return round(self.ina260.voltage, 1)

    def get_power_watts(self):
        return round(self.ina260.power / 1000, 1)

    def record_measurement(self):
        try:
            current_V = self.get_voltage_volts()
            current_W = self.get_power_watts()
            current_A = self.get_current_amps()
            
            if self.prev_volt != current_V:
                point = Point("sensor_data")\
                    .tag("device", "camera")\
                    .field("volts", current_V)\
                    .field("watts", current_W)\
                    .field("amps", current_A)\
                    .time(int(time.time()), WritePrecision.S)
                self.write_api.write(self.bucket, self.org, point)
                print(f"Camera Volts: {current_V}.")
                print(f"Camera Watts: {current_W}.")
                print(f"Camera Amps: {current_A}.")
                self.prev_volt = current_V
                self.prev_watt = current_W
                self.prev_amp = current_A
            time.sleep(3)
        except OSError:
            print("Failed to read sensor data. Check the sensor connection.")
    
    def cp_run(self):
        for i in range(30):
            self.record_measurement()
            time.sleep(5)

    def __del__(self):
        self.client.close()


            
#Poll sensor every 30 seconds
#Only save changes in the data
#What should I do to handle extreme values such as power loss?
