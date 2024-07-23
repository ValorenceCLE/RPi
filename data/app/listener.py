import asyncio
from redis.asyncio import Redis #type: ignore
import os
from datetime import datetime
from influxdb_client import InfluxDBClient, Point # type: ignore
from influxdb_client.client.write_api import ASYNCHRONOUS, WriteOptions # type: ignore

class SaveData:
    def __init__(self, streams):
        print("Initializing Data Save...")
        self.token = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
        self.org = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
        self.bucket = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
        self.url = os.getenv('INFLUXDB_URL')
        print(f"Connecting to InfluxDB at {self.url}")
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=WriteOptions(write_type=ASYNCHRONOUS, batch_size=500, flush_interval=10_000))
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        print(f"Connecting to Redis at {self.redis_url}")
        self.redis = Redis.from_url(self.redis_url)
        self.group_name = 'data_group'
        self.consumer_name = 'influxdb'
        self.collection_interval = 30  # Pull data every 30 seconds
        self.streams = streams
        
    async def setup_groups(self):
        for stream in self.streams:
            try:
                await self.redis.xgroup_create(stream, self.group_name, id='0',mkstream=True)
            except Exception as e:
                if "BUSYGROUP" not in str(e):
                    print(f"Error creating group {self.group_name} for {stream}: {e}")
    
    async def read_streams(self):
        streams = {stream: '>' for stream in self.streams}
        try:
            response = await self.redis.xreadgroup(
                groupname=self.group_name,
                consumername=self.consumer_name,
                streams=streams,
                count=10,
                block=1000 
            )
            return response
        except Exception as e:
            print(f"Error reading from streams: {e}")
            return []
    
    async def write_to_influxdb(self, points):
        try:
            self.write_api.write(bucket=self.influxdb_bucket, org=self.influxdb_org, record=points)
        except Exception as e:
            print(f"Error writting to InfluxDB: {e}")
            
    def create_points(self, stream_name, messages):
        points =[]
        for message_id, message in messages:
            timestamp = message.get('timestamp', datetime.utcnow().isoformat())
            data = {key: float(value) for key, value in message.items() if key != 'timestamp'}
            point = Point(stream_name).time(datetime.fromisoformat(timestamp)).fields(data)
            points.append(point)
        return points
    
    async def process_streams(self):
        await self.setup_groups()
        while True:
            response = await self.read_streams()
            if response:
                for stream_name, messages in response:
                    points = self.create_points(stream_name, messages)
                    await self.write_to_influxdb(points)
            await asyncio.sleep(self.collection_interval)
            
            
if __name__ == "__main__":
    streams = ['network_data']
    reader = SaveData(streams)
    asyncio.run(reader.process_streams())