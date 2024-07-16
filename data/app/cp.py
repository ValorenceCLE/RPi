#Camera Power
#Naming Convention: Camera Number - Sensor Name
#i.e: B8A44F7FF4C2-INA260
import os
import time
import board # type: ignore
import json
import adafruit_ina260 # type: ignore
from influxdb_client import InfluxDBClient, Point, WritePrecision # type: ignore
from influxdb_client.client.write_api import SYNCHRONOUS, WriteOptions # type: ignore

    #Converting Sync functions to Async functions:
    #async def get_current_amps(self):
        #return await asyncio.to_thread(lambda: round(self.ina260.current / 1000, 2))
        
class INA260Camera:
    def __init__(self):
        i2c = board.I2C()  # Setup I2C connection
        self.ina260 = adafruit_ina260.INA260(i2c, address=0x41)  # Initialize INA260 sensor
        self.token = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
        self.org = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
        self.bucket = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
        self.url = os.getenv('INFLUXDB_URL')
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=WriteOptions(write_type=SYNCHRONOUS))
        self.save_interval = 5
        self.counter = 0
        self.SYSTEM_INFO_PATH = '/app/device_info/system_info.json'
        
        with open(self.SYSTEM_INFO_PATH, 'r') as file:
            data = json.load(file)
        self.serial = data["Camera"]["Serial_Number"]
        self.sensor_id = data["Camera"]["Sensor_ID"]

    def get_current_amps(self):
        return round(self.ina260.current / 1000, 2)

    def get_voltage_volts(self):
        return round(self.ina260.voltage, 1)

    def get_power_watts(self):
        return round(self.ina260.power / 1000, 1)
    
    def validation_check(self, volts):
        if volts < 8 or volts > 16:
             return "ERROR"
        elif volts < 10 or volts > 14:
            return "WARNING"
        elif volts < 11 or volts > 13:
            return "INFO"
        else:
            return "NORMAL"
        
    def process_data(self):
        try:
            current_V = self.get_voltage_volts()
            current_W = self.get_power_watts()
            current_A = self.get_current_amps()
            validation_level = self.validation_check(current_V)
            
            if validation_level == "NORMAL":
                self.counter += 1
                if self.counter >= self.save_interval:
                    self.save_normal(current_V, current_W, current_A)
                    self.counter = 0
            if validation_level == "INFO":
                self.save_critical(current_V, current_W, current_A, "INFO")
            if validation_level == "WARNING":
                self.save_critical(current_V, current_W, current_A, "WARNING")
                #Further Processing
            if validation_level == "ERROR":
                self.save_critical(current_V, current_W, current_A, "ERROR")
                #Further actions and processing
        
        except OSError:
            print("Failed to read sensor data. Check connection")
    
    def save_normal(self, volts, watts, amps):
        point = Point("sensor_data")\
            .tag("device", "camera")\
            .field("volts", self.ensure_float(volts))\
            .field("watts", self.ensure_float(watts))\
            .field("amps", self.ensure_float(amps))\
            .time(int(time.time()), WritePrecision.S)
        self.write_api.write(self.bucket, self.org, point)
    
    def save_critical(self, volts, watts, amps, level):
        point = Point("critical_data")\
            .tag("device", "camera")\
            .tag("level", level)\
            .field("volts", self.ensure_float(volts))\
            .field("watts", self.ensure_float(watts))\
            .field("amps", self.ensure_float(amps))\
            .time(int(time.time()), WritePrecision.S)
        self.write_api.write(self.bucket, self.org, point)
    
    def ensure_float(self, value):
        try:
            return float(value)
        except ValueError:
            return None
    
    def cp_run(self):
        for i in range(10):
            self.process_data()
            time.sleep(5)

    def __del__(self):
        self.client.close()


            
#Set up scripts to poll sensors often (5-10s) Put data through initial validation check to identify issues quickly
#If DP passes the validation check set up a waiting/averaging method to either collect one DP every minute or average all of the DP's polled in a minute
#If DP fails validation check send to 'critical_data' and further process to identify error level
#Set up validation to check if the values are outside an acceptable range (Power Loss < x > Power Surge)
#Save outsiders to 'critical_data' group in DB marked with ID tags and LEVEL tags (INFO, WARNING, ERROR)
#INFO: Probably no action besides save in DB
#WARNING: Send MQTT message (LEVEL, Timestamp, ID/Device, Data), Update device status to WARNING (for Web App)
#WARNING: Verify device status with ping; Passed Ping Test--> Continue as WARNING; Failed Ping Test--> Promote WARNING to ERROR
#ERROR: Verify device status with ping; Passed Ping Test--> Demote to WARNING; Failed Ping Test--> Continue as ERROR
#ERROR: Send Error level MQTT message, Event Responding to get device online (Power Cycle, Send Reboot API if possible)
#ERROR: If Event Response Fails + Ping Verifies as OFFLINE still: Trigger backend API scripts to take needed shutdown and needed failsafes
