#Camera Power
#Naming Convention: Camera Number - Sensor Name
#i.e: B8A44F7FF4C2-INA260
import os
import time
import board
import adafruit_ina260
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

class INA260Camera:
    def __init__(self):
        i2c = board.I2C()  # Setup I2C connection
        self.ina260 = adafruit_ina260.INA260(i2c, address=0x41)  # Initialize INA260 sensor
        # Load environment variables
        self.token = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
        self.org = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
        self.bucket = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
        self.url = os.getenv('INFLUXDB_URL')

        # Debug prints to verify environment variables
        print(f"Token: {self.token}")
        print(f"Org: {self.org}")
        print(f"Bucket: {self.bucket}")
        print(f"URL: {self.url}")

        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def get_current_amps(self):
        return round(self.ina260.current / 1000, 2)

    def get_voltage_volts(self):
        return round(self.ina260.voltage, 1)

    def get_power_watts(self):
        return round(self.ina260.power / 1000, 1)

    def record_measurement(self):
        current_A = self.get_current_amps()
        voltage_V = self.get_voltage_volts()
        power_W = self.get_power_watts()
        print(f"Camera Power- Current: {current_A} A, Voltage: {voltage_V} V, Power: {power_W} W")

        point = Point("sensor_data")\
            .tag("device", "camera")\
            .field("amps", current_A)\
            .field("volts", voltage_V)\
            .field("watts", power_W)\
            .time(time.time_ns(), WritePrecision.NS)

        self.write_api.write(self.bucket, self.org, point)

    def cp_test(self):
        for i in range(5):
            self.record_measurement()
            time.sleep(5)

    def __del__(self):
        self.client.close()

sensor = INA260Camera()
sensor.cp_test()


            
#Poll sensor every 30 seconds
#Only save changes in the data
#What should I do to handle extreme values such as power loss?
