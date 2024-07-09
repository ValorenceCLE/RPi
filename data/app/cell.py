import logging
import os
import time
import json
from pysnmp.hlapi import SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, getCmd
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS, WriteOptions


class CellularMetrics:
    def __init__(self):
        self.token = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
        self.org = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
        self.bucket = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
        self.url = os.getenv('INFLUXDB_URL')
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=WriteOptions(write_type=SYNCHRONOUS))
        self.SYSTEM_INFO_PATH = '/app/device_info/system_info.json'
        self.host = '192.168.1.1'
        self.null = -9999
        with open(self.SYSTEM_INFO_PATH, 'r') as file:
            data = json.load(file)
        self.model = data["Router"]["Model"]
        self.serial = data["Router"]["Serial_Number"]
        self.OID_MAPPINGS = {
            "Peplink MAX BR1 Mini": {
                'rsrp_oid': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.7.0',
                'rsrq_oid': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.8.0',
                'sinr_oid': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.5.0'
            },
            "Pepwave MAX BR1 Pro 5G": {
                'rsrp_oid': '.1.3.6.1.4.1.27662.200.1.12.1.1.1.7.0',
                'rsrq_oid': '.1.3.6.1.4.1.27662.200.1.12.1.1.1.8.0',
                'sinr_oid': '.1.3.6.1.4.1.27662.200.1.12.1.1.1.5.0'
            }
        }
        
    def fetch_snmp_data(self, host, community, oid_dict):
        """Fetch SNMP data synchronously."""
        engine = SnmpEngine()
        results = {}
        for oid_name, oid in oid_dict.items():
            errorIndication, errorStatus, errorIndex, varBinds = next(
                getCmd(
                    engine,
                    CommunityData(community, mpModel=1),
                    UdpTransportTarget((host, 161),timeout=1, retries=3),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid))
                )
            )
            if errorIndication:
                print(f"SNMP error: {errorIndication}")
                continue
            elif errorStatus:
                print(f"SNMP error at {errorIndex}: {errorStatus.prettyPrint()}")
                continue
            else:
                results[oid_name] = varBinds[0][1].prettyPrint()

        return results
    
    def process_data(self):
        oid_dict = self.OID_MAPPINGS.get(self.model)
        if not oid_dict:
            print(f"No OID mapping found for {self.model}")
            return
        data = self.fetch_snmp_data(self.host, 'public', oid_dict)
        current_sinr = self.ensure_float(data.get('sinr_oid'))
        current_rsrp = self.ensure_float(data.get('rsrp_oid'))
        current_rsrq = self.ensure_float(data.get('rsrq_oid'))
        if current_sinr > self.null and current_rsrp > self.null and current_rsrq > self.null:
            self.save_normal(current_sinr, current_rsrp, current_rsrq)
        else:
            print("Null response from router, verify cellular connection.")
            pass
        
    def save_normal(self, sinr, rsrp, rsrq):
        point = Point("network_data")\
            .tag("device", "router")\
            .field("sinr", sinr)\
            .field("rsrp", rsrp)\
            .field("rsrq", rsrq)\
            .time(int(time.time()), WritePrecision.S)
        self.write_api.write(self.bucket, self.org, point)
        
    def ensure_float(self, value):
        try:
            return float(value)
        except ValueError:
            return None        
        
    def cell_run(self):
        for i in range(10):
            self.process_data()
            time.sleep(30)
            
    def __del__(self):
        self.client.close()


#Build out script assuming we have a sim card
#Build out a detailed error handling to make sure that instead of failing the script will try again later and restart
#This script will be the most prone to blocking errors to it needs to be well set up
#No advanced handling or analysis needs to be done for this data because we cant do anything about any possible issues
#Run an SNMP poll every minute and save the data to the 'network_data' DB
#Focus most of the detail of this script on making sure the script will not fail.