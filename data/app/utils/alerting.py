from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync # type: ignore
from influxdb_client.client.write_api_async import WriteApiAsync # type: ignore
from redis.asyncio import Redis #type: ignore
import json
import os
from influxdb_client import Point # type: ignore
from utils.logging_setup import logger

class AlertPublisher:
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL')
        self.redis = Redis.from_url(self.redis_url)
        self.channel = "alerts"
        self.token = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
        self.org = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
        self.bucket = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
        self.url = os.getenv('INFLUXDB_URL')
        self.client = None
        self.write_api = None
        
    # Async Init Function
    async def async_init(self):
        if not self.client:
            self.client = InfluxDBClientAsync(url=self.url, token=self.token, org=self.org)
            self.write_api = WriteApiAsync(self.client)
                
    async def publish_alert(self, source: str, value, level: str, timestamp: str, message: str):
        alert_data = {
            "source": source,
            "value": value,
            "level": level,
            "timestamp": timestamp,
            "message": message
        }
        try:
            message = json.dumps(alert_data)
            await self.redis.publish(self.channel, message)
            await logger.info(f"Published alert: {message}")
            await self.write_to_influxdb(alert_data)
        except Exception as e:
            await logger.error(f"Error publishing alert: {e}")
    
    async def write_to_influxdb(self, alert_data):
        await self.async_init()
        try:
            point = Point("alerts") \
                .tag("source", alert_data["source"]) \
                .tag("level", alert_data["level"]) \
                .field("value", alert_data["value"]) \
                .time(alert_data["timestamp"])
            await self.write_api.write(bucket=self.bucket, org=self.org, record=point)
        
        except Exception as e:
            await logger.error(f"Error writing to InfluxDB: {e}")
    
    async def close(self):
        await self.redis.close()
        await self.client.close()

# Singleton instance of AlertPublisher
alert_publisher = AlertPublisher()
