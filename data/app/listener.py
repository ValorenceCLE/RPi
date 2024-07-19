import asyncio
from redis.asyncio import Redis  # type: ignore
import os
from datetime import datetime

class StreamReader:
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
        self.redis = Redis.from_url(self.redis_url)
        self.cell_stream = 'cellular_data'
        self.net_stream = 'network_data'
        self.group_name = 'data_group'
        self.consumer_name = 'consumer_1'
        self.collection_interval = 180  # 3 minutes

    async def setup_groups(self):
        # try:
        #     await self.redis.xgroup_create(self.cell_stream, self.group_name, id='0', mkstream=True)
        # except Exception as e:
        #     if "BUSYGROUP" in str(e):
        #         print(f"Group {self.group_name} already exists for {self.cell_stream}")

        try:
            await self.redis.xgroup_create(self.net_stream, self.group_name, id='0', mkstream=True)
        except Exception as e:
            if "BUSYGROUP" in str(e):
                print(f"Group {self.group_name} already exists for {self.net_stream}")

    async def read_streams(self):
        streams = {self.cell_stream: '>', self.net_stream: '>'}
        try:
            response = await self.redis.xreadgroup(
                groupname=self.group_name, 
                consumername=self.consumer_name, 
                streams=streams, 
                count=6,  # Fetch the last 6 entries
                block=5000
            )
            if not response:
                print("No new messages in the streams.")
            for stream_name, messages in response:
                for message_id, message in messages:
                    print(f"Stream: {stream_name}, ID: {message_id}, Data: {message}")
                    # Acknowledge the message
                    await self.redis.xack(stream_name, self.group_name, message_id)
        except Exception as e:
            print(f"Error reading from streams: {e}")

    async def print_stream_info(self):
        #cell_stream_length = await self.redis.xlen(self.cell_stream)
        net_stream_length = await self.redis.xlen(self.net_stream)
        #print(f"Cellular Data Stream Length: {cell_stream_length}")
        print(f"Network Data Stream Length: {net_stream_length}")
        
        #cell_stream_info = await self.redis.xinfo_stream(self.cell_stream)
        net_stream_info = await self.redis.xinfo_stream(self.net_stream)
        #print(f"Cellular Data Stream Info: {cell_stream_info}")
        print(f"Network Data Stream Info: {net_stream_info}")

    async def run(self):
        await self.setup_groups()
        while True:
            now = datetime.utcnow()
            print(f"Starting Listener: {now}")
            await self.print_stream_info()
            await self.read_streams()
            later = datetime.utcnow()
            duration = (later - now).total_seconds()
            print(f"Finished listening. Took {duration} seconds\n\nBeginning Sleep Cycle")
            await asyncio.sleep(self.collection_interval)

if __name__ == "__main__":
    reader = StreamReader()
    print("Starting...")
    asyncio.run(reader.run())
