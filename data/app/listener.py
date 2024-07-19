import asyncio
from redis.asyncio import Redis
import os

class StreamReader:
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
        self.redis = Redis.from_url(self.redis_url)
        #self.cell_stream = 'cellular_data'
        self.net_stream = 'network_data'
        self.group_name = 'data_group'
        self.consumer_name = 'consumer_1'
        self.collection_interval = 180  # 3 minutes

    async def setup_groups(self):
        # Ensure the consumer group exists for both streams
        #try:
            #await self.redis.xgroup_create(self.cell_stream, self.group_name, id='0', mkstream=True)
        #except Exception as e:
            #if "BUSYGROUP" in str(e):
                #print(f"Group {self.group_name} already exists for {self.cell_stream}")

        try:
            await self.redis.xgroup_create(self.net_stream, self.group_name, id='0', mkstream=True)
        except Exception as e:
            if "BUSYGROUP" in str(e):
                print(f"Group {self.group_name} already exists for {self.net_stream}")

    async def read_streams(self):
        streams = {self.cell_stream: '0', self.net_stream: '0'}
        
        try:
            response = await self.redis.xreadgroup(
                groupname=self.group_name, 
                consumername=self.consumer_name, 
                streams=streams, 
                count=6,  # Fetch the last 6 entries
                block=5000
            )
            for stream_name, messages in response:
                for message_id, message in messages:
                    print(f"Stream: {stream_name}, ID: {message_id}, Data: {message}")
                    # Acknowledge the message
                    await self.redis.xack(stream_name, self.group_name, message_id)
        except Exception as e:
            print(f"Error reading from streams: {e}")

    async def run(self):
        await self.setup_groups()
        while True:
            await self.read_streams()
            await asyncio.sleep(self.collection_interval)

if __name__ == "__main__":
    reader = StreamReader()
    asyncio.run(reader.run())
