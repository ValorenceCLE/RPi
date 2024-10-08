
import json
from influxdb_client import Point # type: ignore
from utils.logging_setup import logger
from utils.config import settings
from utils.clients import InfluxWriter, RedisClient

class AlertPublisher:
    def __init__(self):
        self.channel = "alerts"
        self.org = settings.ORG
        self.bucket = settings.BUCKET
        self.write_api = None
        
    # Async Init Function
    async def async_init(self):
        self.redis = await RedisClient.get_instance()
        self.write_api = await InfluxWriter.get_instance()
                
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
        await self.redis.close_instance()
        await self.write_api.close_instance()

# Singleton instance of AlertPublisher
alert_publisher = AlertPublisher()
