import os
import json
from datetime import datetime
import asyncio
from redis.asyncio import Redis #type: ignore
import aiosnmp #type: ignore
# OID mappings for different router models

# This script needs very strong error handling. It shouldnt cause a failure if the router is down/bad
# It also shouldnt fail if there is no SIM card or No ACTIVE SIM card.

OID_MAPPINGS = {
    "Peplink MAX BR1 Mini": {
        'sinr_oid': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.5.0',
        'rsrp_oid': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.7.0',
        'rsrq_oid': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.8.0'
    },
    "Pepwave MAX BR1 Pro 5G": {
        'sinr_oid': '.1.3.6.1.4.1.27662.200.1.12.1.1.1.5.0',
        'rsrp_oid': '.1.3.6.1.4.1.27662.200.1.12.1.1.1.7.0',
        'rsrq_oid': '.1.3.6.1.4.1.27662.200.1.12.1.1.1.8.0'
    }
}

class CellularMetrics:
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis = Redis.from_url(self.redis_url)
        self.SYSTEM_INFO_PATH = '/app/device_info/system_info.json'
        self.host = '192.168.1.1'
        self.null = -9999
        self.collection_interval = 30  # Interval in seconds between SNMP requests
        with open(self.SYSTEM_INFO_PATH, 'r') as file:
            data = json.load(file)
        self.model = data["Router"]["Model"]
        self.oid_mappings = OID_MAPPINGS[self.model]
    
    # This function needs better error handling. Basically if it fails here at any point instead of breaking or shutting down it should just pass and try again.
    # This may cause infinate failures but it will ensure that no router related issues will cause failures and that as soon as data is avaliable it will start to run 
    async def fetch_snmp_data(self, host, community, oid_mappings):
        """Fetch SNMP data asynchronously using aiosnmp"""
        oids = [oid for oid in oid_mappings.values()]
        results = {}
        start_time = datetime.utcnow()
        async with aiosnmp.Snmp(host=host, community=community, port=161, timeout=5, retries=3, max_repetitions=10) as snmp:
            response = await snmp.get(oids)
            for varbind in response:
                for key, oid in oid_mappings.items():
                    if varbind.oid == oid:
                        results[key] = varbind.value
        end_time = datetime.utcnow()
        elapsed_time = (end_time - start_time).total_seconds()
        print(f"SNMP request took {elapsed_time} seconds\nSNMP request response:{results}")
        return results
    
    async def process_data(self):
        try:
            data = await self.fetch_snmp_data(self.host, 'public', self.oid_mappings)
            if data:
                sinr = self.ensure_float(data.get('sinr_oid'))
                rsrp = self.ensure_float(data.get('rsrp_oid'))
                rsrq = self.ensure_float(data.get('rsrq_oid'))
                await self.stream_data(sinr, rsrp, rsrq)
            else:
                print("No data returned from SNMP request.")
        except Exception as e:
            print(f"Error processing data: {e}")
        
    async def stream_data(self, sinr, rsrp, rsrq):
        timestamp = datetime.utcnow().isoformat()
        data = {
            "timestamp": timestamp,
            "sinr": sinr,
            "rsrp": rsrp,
            "rsrq": rsrq
        }
        print(f"Redis Data: {data}")
        await self.redis.xadd('cellular_data', data)
        
        
    def ensure_float(self, value):
        if value is None:
            print("Warning: Received None value, using null placeholder.")
            return self.null
        try:
            return float(value)
        except (ValueError, TypeError) as e:
            print(f"Error converting value to float: {e}")
            return self.null
        
    async def cell_run(self):
        while True:
            await self.process_data()
            await asyncio.sleep(self.collection_interval)
            
    def __del__(self):
        self.redis.close()
        
#if __name__ == "__main__":
    #cell = CellularMetrics()
    #asyncio.run(cell.cell_run())
    
