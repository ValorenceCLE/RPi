import asyncio
import smbus2 # type: ignore
import os
from redis.asyncio import Redis  # type: ignore
from datetime import datetime
import time
from alerting import alert_publisher
import aiofiles #type: ignore
import json
from logging_setup import logger

class AHT10:
    def __init__(self, i2c_bus=1, address=0x38):
        try:
            self.bus = smbus2.SMBus(i2c_bus)
        except Exception as e:
            self.bus = None
        self.address = address
        if self.bus:
            self.init_sensor()
        self.null = -9999
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis = Redis.from_url(self.redis_url)
        self.collection_interval = 30  # Interval in seconds between data collections
        self.alert_file = 'alerts.json'

    def init_sensor(self):
        if self.bus:
            self.bus.write_i2c_block_data(self.address, 0xE1, [0x08, 0x00])
            time.sleep(0.01)
    
    # There may be issues with it returning None
    async def read_humidity(self):
        data = await self._read_raw_data()
        if data:
            return round(((data[1] << 12) | (data[2] << 4) | (data[3] >> 4)) * 100 / 1048576, 1)
        return None

    async def read_temperature(self):
        data = await self._read_raw_data()
        if data:
            temperature_c = (((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]) * 200 / 1048576 - 50
            return round(temperature_c * 9 / 5 + 32, 1)
        return None

    async def _read_raw_data(self):
        if self.bus:
            await asyncio.to_thread(self.bus.write_i2c_block_data, self.address, 0xAC, [0x33, 0x00])
            await asyncio.sleep(0.05)
            return await asyncio.to_thread(self.bus.read_i2c_block_data, self.address, 0x00, 6)
        return None
    # Entry Point
    async def process_data(self):
        async with aiofiles.open(self.alert_file, 'r') as file:
            alert_templates = await file.read()
            alert_templates = json.loads(alert_templates)
            alert_template = alert_templates["high_temperature"]
        try:
            temperature = await self.read_temperature()
            humidity = await self.read_humidity()
            timestamp = datetime.utcnow().isoformat()
            if temperature >= 110:
                await alert_publisher.publish_alert(
                    source=alert_template["source"],
                    value=temperature,
                    level=alert_template["level"],
                    timestamp=timestamp,
                    message=alert_template["message"]
                )
                await self.stream_data(temperature=temperature, humidity=humidity, timestamp=timestamp)
            else:
                await self.stream_data(temperature=temperature, humidity=humidity, timestamp=timestamp)
        except BaseException as e:
            await logger.error(f"Error processing data: {e}")

    async def stream_data(self, temperature, humidity, timestamp):
        data = {
            "timestamp": timestamp,
            "temperature": temperature,
            "humidity": humidity
        }
        await self.redis.xadd('environment_data', data)

    async def run(self):
        while True:
            await self.process_data()
            await asyncio.sleep(self.collection_interval)

