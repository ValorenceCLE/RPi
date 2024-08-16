import os
import asyncio
from datetime import datetime
from redis.asyncio import Redis # type: ignore
import board # type: ignore
import adafruit_ina260 # type: ignore

class INA260System:
    def __init__(self):
        i2c = board.I2C()  # Setup I2C connection
        self.ina260 = adafruit_ina260.INA260(i2c, address=0x45)  # Initialize INA260 sensor | Demo For now
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis = Redis.from_url(self.redis_url)
        self.collection_interval = 30  # Interval in seconds between data collections
        
    async def get_amps(self):
        return await asyncio.to_thread(lambda: round(self.ina260.current / 1000, 1))
    
    async def get_volts(self):
        return await asyncio.to_thread(lambda: round(self.ina260.voltage, 1))
    
    async def get_watts(self):
        return await asyncio.to_thread(lambda: round(self.ina260.power / 1000, 1))
    
    async def stream_data(self):
        timestamp = datetime.utcnow().isoformat()
        volts = await self.get_volts()
        watts = await self.get_watts()
        amps = await self.get_amps()
        data = {
            "timestamp": timestamp,
            "volts": volts,
            "watts": watts,
            "amps": amps
        }
        await self.redis.xadd('system_data', data)
        
    async def run(self):
        while True:
            await self.stream_data()
            await asyncio.sleep(self.collection_interval)
            
if __name__ == "__main__":
    sp = INA260System()
    asyncio.run(sp.run())