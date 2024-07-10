#Temperature/Humidity
#Naming Convention: Rpi Serial Number - Sensor Name
#i.e: 10000000357d707e-AHT10
import time
import smbus2
import os
import json
from influxdb_client import InfluxDBClient, Point, WritePrecision # type: ignore
from influxdb_client.client.write_api import SYNCHRONOUS, WriteOptions # type: ignore

class AHT10:
    def __init__(self, i2c_bus=1, address=0x38):
        self.bus = smbus2.SMBus(i2c_bus)
        self.address = address
        self.init_sensor()
        self.token = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
        self.org = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
        self.bucket = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
        self.client = InfluxDBClient(url=os.getenv('INFLUXDB_URL'), token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=WriteOptions(write_type=SYNCHRONOUS))
        self.save_interval = 5
        self.counter = 0
        self.SYSTEM_INFO_PATH = '/app/device_info/system_info.json'
        with open(self.SYSTEM_INFO_PATH, 'r') as file:
            data = json.load(file)
        self.serial = data["RPi"]["Serial_Number"]
        self.sensor_id = data["RPi"]["Sensor_ID"]
        
    def init_sensor(self):
        self.bus.write_i2c_block_data(self.address, 0xE1, [0x08, 0x00])
        time.sleep(0.02)
        
    def read_humidity(self):
        data = self._read_raw_data()
        return round(((data[1] << 12) | (data[2] << 4) | (data[3] >> 4)) * 100 / 1048576, 1)
    
    def read_temperature(self):
        data = self._read_raw_data()
        temperature_c = (((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]) * 200 / 1048576 - 50
        return round(temperature_c * 9/5 +32, 1)
    
    def _read_raw_data(self):
        self.bus.write_i2c_block_data(self.address, 0xAC, [0x33, 0x00])
        time.sleep(0.5)
        return self.bus.read_i2c_block_data(self.address, 0x00, 6)
    
    def validation_check(self, temperature):
        if temperature < 10 or temperature > 100:
            return "WARNING"
        else:
            return "NORMAL"
        
    def process_data(self):
        try:
            current_T = self.read_temperature()
            current_H = self.read_humidity()
            validation_level = self.validation_check(current_T)
            if validation_level == "WARNING":
                self.save_critical(current_T, current_H, "WARNING")
                #Turn on fan
            else:
                self.counter += 1
                if self.counter >= self.save_interval:
                    self.save_normal(current_T, current_H)
                    self.counter = 0
        except OSError:
            print("Failed to read sensor data. Check Connection")
    
    def save_normal(self, temperature, humidity):
        point = Point("sensor_data")\
            .tag("device", "system")\
            .field("temperature", self.ensure_float(temperature))\
            .field("humidity", self.ensure_float(humidity))\
            .time(int(time.time()), WritePrecision.S)
        self.write_api.write(self.bucket, self.org, point)
            
    def save_critical(self, temperature, humidity, level):
        point = Point("critical_data")\
            .tag("device", "system")\
            .tag("level", level)\
            .field("temperature", self.ensure_float(temperature))\
            .field("humidity", self.ensure_float(humidity))\
            .time(int(time.time()), WritePrecision.S)
        self.write_api.write(self.bucket, self.org, point)
            
    def ensure_float(self, value):
        try:
            return float(value)
        except ValueError:
            return None
        
        
    def env_run(self):
        for i in range(10):
            self.process_data()
            time.sleep(5)
            
    def __del__(self):
        self.client.close()


#Set up scripts to poll sensors often (5-10s) Put data through initial validation check to identify issues quickly
#If DP passes the validation check set up a waiting/averaging method to either collect one DP every minute or average all of the DP's polled in a minute
#If DP fails validation check send to 'critical_data' and further process to identify error level
#Set up validation to check if the values are outside an acceptable range (Too Cold < x > Too Hot)
#Save outsiders to 'critical_data' group in DB marked with ID tags and LEVEL tags (INFO, WARNING, ERROR)
#INFO: Probably no action besides save in DB
#WARNING: Send MQTT message (LEVEL, Timestamp, ID/Device, Data), Update device status to WARNING (for Web App)
#WARNING: Verify device status with ping; Passed Ping Test--> Continue as WARNING; Failed Ping Test--> Promote WARNING to ERROR
#ERROR: Verify device status with ping; Passed Ping Test--> Demote to WARNING; Failed Ping Test--> Continue as ERROR
#ERROR: Send Error level MQTT message, Event Responding to get device online (Power Cycle, Send Reboot API if possible)
#ERROR: If Event Response Fails + Ping Verifies as OFFLINE still: Trigger backend API scripts to take needed shutdown and needed failsafes