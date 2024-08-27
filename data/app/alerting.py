from redis.asyncio import Redis #type: ignore
import json
import os

class AlertPublisher:
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL')
        self.redis = Redis.from_url(self.redis_url)
        self.channel = "alerts"
    
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
            print(f"Published alert: {message}")
        except Exception as e:
            print(f"Error publishing alert: {e}")
    
    async def close(self):
        await self.redis.close()

# Singleton instance of AlertPublisher
alert_publisher = AlertPublisher()