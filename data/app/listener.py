import asyncio
import os
from redis.asyncio import Redis

class StreamPrinter:
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis = Redis.from_url(self.redis_url)
        self.group_name = 'stream_group'
        self.consumer_name = 'consumer_1'
        self.cell_stream = 'cellular_data'
        self.net_stream = 'network_data'
        
    async def create_group(self):
        try:
            await self.redis.xgroup_create(self.cell_stream, self.group_name, id='$', mkstream=True)
        except Exception as e:
            print(f"Group {self.group_name} for {self.cell_stream} already exists")

        try:
            await self.redis.xgroup_create(self.net_stream, self.group_name, id='$', mkstream=True)
        except Exception as e:
            print(f"Group {self.group_name} for {self.net_stream} already exists")
            
    async def read_streams(self):
        while True:
            try:
                streams = {self.cell_stream: '>', self.net_stream: '>'}
                response = await self.redis.xreadgroup(groupname=self.group_name, consumername=self.consumer_name, streams=streams, count=10, block=5000)
                for stream_name, messages in response:
                    for message_id, message in messages:
                        print(f"Stream: {stream_name}, ID: {message_id}, Data: {message}")
                        # Acknowledge the message
                        await self.redis.xack(stream_name, self.group_name, message_id)
            except Exception as e:
                print(f"Error reading from streams: {e}")
            
    async def run(self):
        await self.create_group()
        await self.read_streams()
            
if __name__ == "__main__":
    sp = StreamPrinter()
    asyncio.run(sp.run())
