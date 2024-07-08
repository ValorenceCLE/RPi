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
            packet_loss = response_list.packet_loss
            avg_rtt = response_list.rtt_avg_ms
            max_rtt = response_list.rtt_max_ms
            min_rtt = response_list.rtt_min_ms
            
            point = Point("network_data")\
                .tag("device", "router")\
                .field("avg_rtt_ms", avg_rtt)\
                .field("max_rtt_ms", max_rtt)\
                .field("min_rtt_ms", min_rtt)\
                .field("packet_loss_percent", packet_loss * 100)\
                .time(int(time.time()), WritePrecision.S)
            self.write_api.write(self.bucket, self.org, point)
            print(f"Avg. Response Time: {avg_rtt}.")
            print(f"Max. Response Time: {max_rtt}.")
            print(f"Min. Response Time: {min_rtt}.")
            print(f"Packets Lost (%): {packet_loss *100}.")
        except Exception as e:
            print(f"Failed to perform ping test: {e}")
            
    def net_run(self):
        for i in range(10):
            self.run_ping_test()
            time.sleep(10)
    
    def __del__(self):
        self.client.close()
            

#This should have good error handling but even if the router is offline we should collect this data because it will show that the router was offline
#We just need to make sure that it doesnt run into errors when trying to ping a possibly down router
#Is jitter something we actually need to save?
#Do we save all or some of the packet loss information since most the time it will be 0?
