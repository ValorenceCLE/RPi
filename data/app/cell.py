#New SNMP script that uses Redis and Async.
#Make sure that we set it up to send all GET requests at the same time rather than one after another.
import os
import json
from datetime import datetime
import asyncio
from redis.asyncio import Redis
from pysnmp.entity.engine import SnmpEngine
from pysnmp.hlapi.asyncio import CommunityData, UdpTransportTarget, ContextData, ObjectType, bulkCmd, ObjectIdentity


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
        self.serial = data["Router"]["Serial_Number"]
        self.MIB_NAMES = {
            'sinr_mib': 'cellularSignalSinr.0',
            'rsrp_mib': 'cellularSignalRsrp.0',
            'rsrq_mib': 'cellularSignalRsrq.0'
        }
        
    async def fetch_snmp_data(self, host, community, mib_triplets):
        """Fetch SNMP data asynchronously using bulkCmd."""
        engine = SnmpEngine()
        results = {}
        errorIndication, errorStatus, errorIndex, varBindTable = await bulkCmd(
            engine,
            CommunityData(community, mpModel=1),
            UdpTransportTarget((host, 161), timeout=1, retries=3),
            ContextData(),
            0, len(mib_triplets),  # Fetch only the needed OIDs
            *[ObjectType(ObjectIdentity(*triplet)) for triplet in mib_triplets]
        )
        if errorIndication:
            print(f"SNMP error: {errorIndication}")
        elif errorStatus:
            print(f"SNMP error at {errorIndex}: {errorStatus.prettyPrint()}")
        else:
            for varBindRow in varBindTable:
                for varBind in varBindRow:
                    oid, value = varBind
                    for triplet in mib_triplets:
                        mib_name = f"{triplet[0]}::{triplet[1]}.0"
                        if mib_name in oid.prettyPrint():
                            results[triplet[1]] = value.prettyPrint()  # Use MIB object name as key
        return results
    
    async def process_data(self):
        data = await self.fetch_snmp_data(self.host, 'public', self.MIB_NAMES)
        sinr = self.ensure_float(data.get('cellularSignalSinr'))
        rsrp = self.ensure_float(data.get('cellularSignalRsrp'))
        rsrq = self.ensure_float(data.get('cellularSignalRsrq'))
        if sinr > self.null and rsrp > self.null and rsrq > self.null:
            await self.stream_data(sinr, rsrp, rsrq)
        else:
            print("Invalid SNMP response, verify cellular connection.")
    
    async def stream_data(self, sinr, rsrp, rsrq):
        timestamp = datetime.utcnow().isoformat()
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
    cell = CellularMetrics()
    asyncio.run(cell.cell_run())
        