import os
import json
from datetime import datetime
import asyncio
from redis.asyncio import Redis
from pysnmp.hlapi.asyncio.slim import Slim
from pysnmp.smi.rfc1902 import ObjectIdentity, ObjectType

OID_MAPPINGS = {
    "Peplink MAX BR1 Mini": {
        'rsrp_oid': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.7',
        'rsrq_oid': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.8',
        'sinr_oid': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.5'
    },
    "Pepwave MAX BR1 Pro 5G": {
        'rsrp_oid': '.1.3.6.1.4.1.27662.200.1.12.1.1.1.7.0',
        'rsrq_oid': '.1.3.6.1.4.1.27662.200.1.12.1.1.1.8.0',
        'sinr_oid': '.1.3.6.1.4.1.27662.200.1.12.1.1.1.5.0'
    }
}
class CellularMetrics:
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis = Redis.from_url(self.redis_url)
        self.SYSTEM_INFO_PATH = '/app/device_info/system_info.json'
        self.host = '192.168.1.1'
        self.null = -9999
        self.collection_interval = 30
        with open(self.SYSTEM_INFO_PATH, 'r') as file:
            data = json.load(file)
        self.model = data["Router"]["Model"]
        self.oid_mappings = OID_MAPPINGS[self.model]
        
        
    async def fetch_snmp_data(self, host, community, port, oid_mappings):
        async with Slim() as slim:
            var_binds = [ObjectType(ObjectIdentity(oid)) for oid in oid_mappings.values()]
            errorIndication, errorStatus, errorIndex, varBindTable = await slim.get(
                community,
                host,
                port,
                0, 
                *var_binds
            )
            if errorIndication:
                print(f"SNMP error: {errorIndication}")
                return None
            elif errorStatus:
                print(f"SNMP error at {errorIndex}: {errorStatus.prettyPrint()}")
                return None
            else:
                results = {}
                for varBindRow in varBindTable:
                    for varBind in varBindRow:
                        oid, value = varBind
                        for name, oid_str in oid_mappings.items():
                            if oid.prettyPrint().startswith(oid_str):
                                results[name] = value.prettyPrint()
                return results
    
    async def process_data(self):
        data = await self.fetch_snmp_data(self.host, 'public', 161, self.oid_mappings)
        if data:
            sinr = self.ensure_float(data.get('sinr_oid'))
            rsrp = self.ensure_float(data.get('rsrp_oid'))
            rsrq = self.ensure_float(data.get('rsrq_oid'))
            if sinr > self.null and rsrp > self.null and rsrq > self.null:
                timestamp = datetime.utcnow().isoformat()
                await self.stream_data(sinr, rsrp, rsrq, timestamp)
            else:
                print("SNMP request fail, check cellular status.")
        
        
    async def stream_data(self, sinr, rsrp, rsrq, timestamp):
        data = {
            "timestamp": timestamp,
            "sinr": sinr,
            "rsrp": rsrp,
            "rsrq": rsrq
        }
        await self.redis.xadd('cellular_data', data)
        print(data)
        
    def ensure_float(self, value):
        try:
            return float(value)
        except ValueError:
            return self.null
        
    async def cell_run(self):
        while True:
            await self.process_data()
            await asyncio.sleep(self.collection_interval)
    
    def __del__(self):
        self.redis.close()
        
if __name__ == "__main__":
    cell = CellularMetrics
    asyncio.run(cell.cell_run())