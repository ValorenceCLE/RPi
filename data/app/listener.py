import asyncio
from redis.asyncio import Redis
from datetime import datetime, timedelta
import os

class StreamReader:
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')  # Update this as needed
        self.redis = Redis.from_url(self.redis_url)
        self.cell_stream = 'cellular_data'
        self.net_stream = 'network_data'
        self.group_name = 'data_group'
        self.consumer_name = 'consumer_1'
        self.collection_interval = 180  # 3 minutes

    async def read_streams(self):
        while True:
            try:
                now = datetime.utcnow()
                three_minutes_ago = now - timedelta(minutes=3)
                streams = {self.cell_stream: three_minutes_ago.isoformat(), self.net_stream: three_minutes_ago.isoformat()}
                
                response = await self.redis.xreadgroup(
                    groupname=self.group_name, 
                    consumername=self.consumer_name, 
                    streams=streams, 
                    count=100,  # Adjust count as needed
                    block=5000
                )
                for stream_name, messages in response:
                    for message_id, message in messages:
                        print(f"Stream: {stream_name}, ID: {message_id}, Data: {message}")
                        # Acknowledge the message
                        await self.redis.xack(stream_name, self.group_name, message_id)
            except Exception as e:
                print(f"Error reading from streams: {e}")
            await asyncio.sleep(self.collection_interval)

    def run(self):
        asyncio.run(self.read_streams())

if __name__ == "__main__":
    reader = StreamReader()
    reader.run()
