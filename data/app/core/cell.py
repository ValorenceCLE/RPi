from datetime import datetime
import asyncio
import aiosnmp #type: ignore
from utils.logging_setup import logger
from utils.config import settings
from utils.clients import RedisClient

# This script needs very strong error handling. It shouldnt cause a failure if the router is down/bad
# It also shouldnt fail if there is no SIM card or No ACTIVE SIM card.
# OID mappings for different router models
# OLD OID Mappings, See config.py for new OID mappings
# OID_MAPPINGS = {
#     "Peplink MAX BR1 Mini": {
#         'sinr_oid': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.5.0',
#         'rsrp_oid': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.7.0',
#         'rsrq_oid': '.1.3.6.1.4.1.23695.200.1.12.1.1.1.8.0'
#     },
#     "Pepwave MAX BR1 Pro 5G": {
#         'sinr_oid': '.1.3.6.1.4.1.27662.200.1.12.1.1.1.5.0',
#         'rsrp_oid': '.1.3.6.1.4.1.27662.200.1.12.1.1.1.7.0',
#         'rsrq_oid': '.1.3.6.1.4.1.27662.200.1.12.1.1.1.8.0'
#     }
# }

class CellularMetrics:
    def __init__(self):
        self.SYSTEM_INFO_PATH = settings.SYSTEM_INFO_PATH
        self.host = settings.HOST
        self.null = settings.NULL
        self.collection_interval = settings.COLLECTION_INTERVAL # Interval in seconds between SNMP requests
        self.oid_mappings = settings.OID_MAPPINGS
        # Commented out because we may not need to know the model of the router
        # Both routers have the same OID mappings so we can just use the mappings directly
        # with open(self.SYSTEM_INFO_PATH, 'r') as file:
        #     data = json.load(file)
        # self.model = data["Router"]["Model"]
        # self.oid_mappings = OID_MAPPINGS[self.model]
        
        
    async def async_init(self):
        self.redis = await RedisClient.get_instance()
    
    # This function needs better error handling. Basically if it fails here at any point instead of breaking or shutting down it should just pass and try again.
    # This may cause infinate failures but it will ensure that no router related issues will cause failures and that as soon as data is avaliable it will start to run 
    async def fetch_snmp_data(self, host, community, oid_mappings):
        """Fetch SNMP data asynchronously using aiosnmp"""
        oids = [oid for oid in oid_mappings.values()]
        results = {}
        async with aiosnmp.Snmp(host=host, community=community, port=161, timeout=5, retries=3, max_repetitions=10) as snmp:
            response = await snmp.get(oids)
            for varbind in response:
                for key, oid in oid_mappings.items():
                    if varbind.oid == oid:
                        results[key] = varbind.value
        return results
    
    async def process_data(self):
        try:
            data = await self.fetch_snmp_data(self.host, 'public', self.oid_mappings)
            if data:
                sinr = await self.ensure_float(data.get('sinr_oid'))
                rsrp = await self.ensure_float(data.get('rsrp_oid'))
                rsrq = await self.ensure_float(data.get('rsrq_oid'))
                await self.stream_data(sinr, rsrp, rsrq)
            else:
                await logger.warning("No data returned from SNMP request.")
        except Exception as e:
            await logger.error(f"Error processing data: {e}")
        
    async def stream_data(self, sinr, rsrp, rsrq):
        timestamp = datetime.utcnow().isoformat()
        data = {
            "timestamp": timestamp,
            "sinr": sinr,
            "rsrp": rsrp,
            "rsrq": rsrq
        }
        await self.redis.xadd('cellular_data', data)
        
        
    async def ensure_float(self, value):
        if value is None:
            await logger.warning("Warning: Received None value, using null placeholder.")
            return self.null
        try:
            return float(value)
        except (ValueError, TypeError) as e:
            await logger.error(f"Error converting value to float: {e}")
            return self.null
        
    async def cell_run(self):
        await self.async_init()
        while True:
            await self.process_data()
            await asyncio.sleep(self.collection_interval)
            
    def __del__(self):
        self.redis.close()
        
    
