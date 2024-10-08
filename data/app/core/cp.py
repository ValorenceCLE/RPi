import asyncio
from datetime import datetime
import json
import aiofiles #type: ignore
import board # type: ignore
import adafruit_ina260 # type: ignore
from utils.alerting import alert_publisher
from utils.logging_setup import logger
from utils.config import settings
from utils.clients import RedisClient

class INA260Camera:
    def __init__(self):
        i2c = board.I2C()  # Setup I2C connection
        self.ina260 = adafruit_ina260.INA260(i2c, address=0x41)  # Initialize INA260 sensor
        self.collection_interval = settings.COLLECTION_INTERVAL  # Interval in seconds between data collections
        self.alert_file = settings.ALERT_FILE
        
        
    async def async_init(self):
        self.redis = await RedisClient.get_instance()
        
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
            warning_alert = alert_templates["camera_warning"]
            error_alert = alert_templates["camera_error"]
        try:
            timestamp = datetime.utcnow().isoformat()
            volts = await self.get_volts()
            watts = await self.get_watts()
            amps = await self.get_amps()
            data = f"Volts: {volts}, Watts: {watts}, Amps: {amps}"
            #if watts < 10: This is the real check
            if watts == 0: # Demo Check (Remove this line in production)
                # Power Loss
                await alert_publisher.publish_alert(
                    source=error_alert["source"],
                    value=data,
                    level=error_alert["level"],
                    timestamp=timestamp,
                    message=error_alert["message"]
                )
                await self.stream_data(volts, watts, amps, timestamp)
            #elif watts < 12 or watts > 18: This is the real check
            elif watts < 0.1 or watts > 1: # Demo Check (Remove this line in production)
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
            await logger.error(f"Error processing data: {e}")
    
    async def stream_data(self, volts, watts, amps, timestamp):
        data = {
            "timestamp": timestamp,
            "volts": volts,
            "watts": watts,
            "amps": amps
        }
        await self.redis.xadd('camera_data', data)
        
    async def run(self):
        await self.async_init()
        while True:
            await self.process_data()
            await asyncio.sleep(self.collection_interval)
            