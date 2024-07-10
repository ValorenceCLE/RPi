#Network Data from running ping tests
#Naming Convention: Router Serial Number - NET
#i.e: 192F10E882C7-NET

import os
import time
import asyncio
import aioping
from influxdb_client import InfluxDBClient, Point, WritePrecision # type: ignore
from influxdb_client.client.write_api import ASYNCHRONOUS, WriteOptions # type: ignore

class NetworkPingTest:
    def __init__(self, target_ip='8.8.8.8'):
        self.target_ip = target_ip
        self.token = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
        self.org = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
        self.bucket = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
        self.url = os.getenv('INFLUXDB_URL')
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=WriteOptions(write_type=ASYNCHRONOUS))
        self.collection_interval = 30 #45 Seconds
        self.ping_count = 5 #Number of pings to be sent per ping test (5 ping tests per data point)
    
    async def run_ping_test(self):
        try:
            response_list = await asyncio.gather(*[self.ping_host() for _ in range(self.ping_count)]) # Send 5 pings per Ping Test
            packets_lost = response_list.count(None)
            packet_loss_percent = response_list.count(None) / self.ping_count *100
            avg_rtt = sum(filter(None, response_list)) / len(response_list)
            max_rtt = max(filter(None, response_list))
            min_rtt = min(filter(None, response_list))
            jitter = max_rtt - min_rtt
            validation_level = self.validation_check(packets_lost, avg_rtt)
            if validation_level =="NORMAL":
                await self.save_normal(avg_rtt, packet_loss_percent, jitter)
            else:
                await self.save_critical(avg_rtt, min_rtt, max_rtt, packets_lost, validation_level)
        except Exception as e:
            print(f"Failed to perform ping test: {e}")
            #Implement a counter to see if it has uploaded several points to the critical bucket in a row.
            #This would mean consistant errors and need for at least a notification/alert
            
    async def ping_host(self):
        try:
            delay = await aioping.ping(self.target_ip)
            return delay * 1000 # Convert (s) --> (ms)
        except TimeoutError:
            return None
        
    async def router_online(self, host='192.168.1.1', timeout=1):
        try:
            delay = await aioping.ping(host, timeout=timeout)
            return True
        except TimeoutError:
            return False
        
    def validation_check(self, packets_lost, avg_rtt):
        online = self.router_online()
        if packets_lost == self.ping_count:
            if online:
                return "WARNING"
            else:
                return "ERROR"
            #Run further checks specifically on the router just to check if its online.
            #If router OFFLINE send Pub/Sub message
        elif packets_lost < self.ping_count and packets_lost > 2:
            if online:
                return "WARNING"
            else:
                return "ERROR"
            #Check if router is ONLINE, if 
        elif packets_lost > 0 or avg_rtt > 200:
            return "INFO"
        else:
            return "NORMAL"
        
    async def save_normal(self, avg_rtt, packet_loss_percent, jitter):
        point = Point("network_data")\
            .tag("device", "router")\
            .field("avg_rtt_ms", avg_rtt)\
            .field("packet_loss_percent", packet_loss_percent)\
            .field("jitter", jitter)\
            .time(int(time.time()), WritePrecision.S)
        await self.write_api.write(self.bucket, self.org, point)
    
    async def save_critical(self, avg, min, max, packets_lost, level):
        point = Point("critical_data")\
            .tag("device", "router")\
            .tag("level", level)\
            .field("avg_rtt_ms", avg)\
            .field("min_rtt_ms", min)\
            .field("max_rtt_ms", max)\
            .field("packets_lost", packets_lost)\
            .time(int(time.time()), WritePrecision.S)
        await self.write_api.write(self.bucket, self.org, point)
    
    async def net_run(self):
        while True:
            await self.run_ping_test()
            await asyncio.sleep(self.collection_interval)
            
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
