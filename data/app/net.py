#Network Data from running ping tests
#Naming Convention: Router Serial Number - NET
#i.e: 192F10E882C7-NET

import os
import time
from pythonping import ping
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS, WriteOptions

class NetworkPingTest:
    def __init__(self, target_ip='8.8.8.8'):
        self.target_ip = target_ip
        self.token = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
        self.org = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
        self.bucket = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
        self.url = os.getenv('INFLUXDB_URL')
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=WriteOptions(write_type=SYNCHRONOUS))
    
    
    
    def run_ping_test(self):
        try:
            response_list = ping(self.target_ip, count=10, verbose=False)
            packet_loss = self.ensure_float(response_list.packet_loss) *100
            avg_rtt = self.ensure_float(response_list.rtt_avg_ms) /1000
            max_rtt = self.ensure_float(response_list.rtt_max_ms) /1000
            min_rtt = self.ensure_float(response_list.rtt_min_ms) /1000
            validation_level = self.validation_check(packet_loss)
            if validation_level == "NORMAL":
                self.save_normal(avg_rtt, min_rtt, max_rtt)
            else:
                self.save_critical(avg_rtt, min_rtt, max_rtt, packet_loss, validation_level) 
            
        except Exception as e:
            print(f"Failed to perform ping test: {e}")
            
    def validation_check(self, packet_loss):
        if packet_loss > 2:
            return "ERROR"
        elif packet_loss > 1:
            return "WARNING"
        else:
            return "NORMAL"
    
    def save_normal(self, avg, min, max):
        test = self.run_ping_test()
        point = Point("network_data")\
            .tag("device", "router")\
            .field("avg_rtt", avg)\
            .field("min_rtt", min)\
            .field("max_rtt", max)\
            .time(int(time.time()), WritePrecision.S)
        self.write_api.write(self.bucket, self.org, point)
    
    def save_critical(self, avg, min, max, packet_loss, level):
        point = Point("critical_data")\
            .tag("device", "router")\
            .tag("level", level)\
            .field("avg_rtt", avg)\
            .field("min_rtt", min)\
            .field("max_rtt", max)\
            .field("packet_loss", packet_loss)\
            .time(int(time.time()), WritePrecision.S)
        self.write_api.write(self.bucket, self.org, point)
    
    def net_run(self):
        for i in range(10):
            self.run_ping_test()
            time.sleep(10)
            
    def ensure_float(self, value):
        try:
            return float(value)
        except ValueError:
            return None
        
    def __del__(self):
        self.client.close()
            

#Set up another class that can be used by other scripts to run ping tests if needed.

#Run a ping test every 60 seconds (Avg_RTT, Max_RTT, Min_RTT, Jitter(Max_RTT-Min_RTT), Packet_Loss)
#If No packets lost save to normal DB (Avg_RTT, Max_RTT, Min_RTT, Jitter)*No Packet Loss
#IF Packets Lost save to automatically move to 'critical_data' and run validation checks
#If Packets Lost send data including packet losses through validation checks
#VALIDATION CHECKS: Check all values to make sure they are in a given range. (Packets Lost =< 0) (Avg_RTT =< 100) Mabybe Jitter
#MAKE SURE NORMAL DATA COLLECTION CYCLE BREAKS DURING VALIDATION CHECKS UNTIL ROUTER IS DEEMED "NORMAL"
#PACKET LOSS CHECK: IF packet losses trigger the validation check then run a seperate or additional ping for further checks
#PACKET LOSS CHECK: IF packet losses persist in further checks then promote automatically to WARNING
#PACKET LOSS CHECK: IF packet losses stop in further checks then return to normal and log that DP in 'critical_data' as INFO
#INFO: High Latency or Lost Packet. Just save the data to 'critical_data'
#WARNING: High Latency AND Lost Packet or MULTIPLE Lost Packets: Send MQTT message, save with WARNING tag
#ERROR: Any blocking error occurs or unable to send ping OR Continued Packet Loss (5+ min), Send MQTT message, save with ERROR tag
#ERROR: For errors or failures make sure the script is still running, if not turn it back on.
#ERROR: For continued packet loss send MQTT message and trigger API event process to reboot router.
#NOTES: Make sure that when any one scripts triggers a restart that other scripts know that and know not to trigger another restart.
