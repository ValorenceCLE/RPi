#Router Power
#Naming Convention: Router Serial Number - Sensor Name
#i.e: 192F10E882C7-INA260
import os
import time
import board
import adafruit_ina260
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS, WriteOptions

class INA260Router:
    def __init__(self):
        i2c = board.I2C()
        self.ina260 = adafruit_ina260.INA260(i2c, address=0x40) #Initialize sensor
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
        return round(self.ina260.current / 1000, 3)

    def get_voltage_volts(self):
        return round(self.ina260.voltage, 1)

    def get_power_watts(self):
        return round(self.ina260.power / 1000, 1)
    
    def record_measurement(self):
        try:
            current_V = self.get_voltage_volts()
            current_W = self.get_power_watts()
            current_A = self.get_current_amps()
            
            if self.prev_volt != current_V or self.prev_amp != current_A or self.prev_watt != current_W:
                point = Point("sensor_data")\
                    .tag("device", "router")\
                    .field("volts", current_V)\
                    .field("watts", current_W)\
                    .field("amps", current_A)\
                    .time(int(time.time()), WritePrecision.S)
                self.write_api.write(self.bucket, self.org, point)
                print(f"Router Volts: {current_V}.")
                print(f"Router Watts: {current_W}.")
                print(f"Router Amps: {current_A}.")
                self.prev_volt = current_V
                self.prev_watt = current_W
                self.prev_amp = current_A
            time.sleep(3)
        except OSError:
            print("Failed to read sensor data. Check the sensor connection.")
            
    def rp_run(self):
        for i in range(10):
            self.record_measurement()
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
