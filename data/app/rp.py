import os
import asyncio
from datetime import datetime
import json
import aiofiles #type: ignore
from redis.asyncio import Redis # type: ignore
import board # type: ignore
import adafruit_ina260 # type: ignore
from alerting import alert_publisher

class INA260Router:
    def __init__(self):
        i2c = board.I2C()
        self.ina260 = adafruit_ina260.INA260(i2c, address=0x40)
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis = Redis.from_url(self.redis_url)
        self.collection_interval = 30 #30 second collection interval
        self.null = -9999
        self.alert_file = 'alerts.json'
        
    async def get_amps(self):
        return await asyncio.to_thread(lambda: round(self.ina260.current / 1000, 1))
    
    async def get_volts(self):
        return await asyncio.to_thread(lambda: round(self.ina260.voltage, 1))
    
    async def get_watts(self):
        return await asyncio.to_thread(lambda: round(self.ina260.power / 1000, 1))
    
    # Entry Point
    async def process_data(self):
        async with aiofiles.open(self.alert_file, 'r') as file:
            alert_templates = await file.read()
            alert_templates = json.loads(alert_templates)
            warning_alert = alert_templates["router_warning"]
            error_alert = alert_templates["router_error"]
        try:
            timestamp = datetime.utcnow().isoformat()
            volts = await self.get_volts()
            watts = await self.get_watts()
            amps = await self.get_amps()
            data = f"Volts: {volts}, Watts: {watts}, Amps: {amps}"
            if watts < 1:
                # Power Loss
                await alert_publisher.publish_alert(
                    source=error_alert["source"],
                    value=data,
                    level=error_alert["level"],
                    timestamp=timestamp,
                    message=error_alert["message"]
                )
                await self.stream_data(volts, watts, amps, timestamp)
            elif watts < 2 or watts > 5:
                # Power is outside of an acceptable range
                await alert_publisher.publish_alert(
                    source=warning_alert["source"],
                    value=data,
                    level=warning_alert["level"],
                    timestamp=timestamp,
                    message=warning_alert["message"]
                )
                await self.stream_data(volts, watts, amps, timestamp)
            else:
                await self.stream_data(volts, watts, amps, timestamp)
        except BaseException as e:
            print(f"Error processing data: {e}")
    
    async def stream_data(self, volts, watts, amps, timestamp):
        data = {
            "timestamp": timestamp,
            "volts": volts,
            "watts": watts,
            "amps": amps
        }
        await self.redis.xadd('router_data', data)
        
    async def run(self):
        while True:
            await self.process_data()
            await asyncio.sleep(self.collection_interval)
            
if __name__ == "__main__":
    rp = INA260Router()
    asyncio.run(rp.run())