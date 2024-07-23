import asyncio
from redis.asyncio import Redis #type: ignore
import os
from datetime import datetime
from influxdb_client import InfluxDBClient, Point # type: ignore
from influxdb_client.client.write_api import ASYNCHRONOUS, WriteOptions # type: ignore


class SaveData:
    def __init__(self):
        print("Initializing Data Save...")
        self.token = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
        self.org = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
        self.bucket = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
        self.url = os.getenv('INFLUXDB_URL')
        print(f"Connecting to InfluxDB at {self.url}")
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=WriteOptions(write_type=ASYNCHRONOUS, batch_size=100, flush_interval=10_000))
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        print(f"Connecting to Redis at {self.redis_url}")
        self.redis = Redis.from_url(self.redis_url)
        self.group_name = 'data_group'
        self.consumer_name = 'influxdb'
        self.collection_interval = 30  # Pull data every 30 seconds
        
        
    async def setup_groups(self, streams):
        print("Setting up consumer groups for streams...")
        for stream in streams:
            try:
                print(f"Creating consumer group {self.group_name} for stream {stream}")
                await self.redis.xgroup_create(stream, self.group_name, id='0', mkstream=True)
                print(f"Group {self.group_name} created for {stream}")
            except Exception as e:
                if "BUSYGROUP" in str(e):
                    print(f"Group {self.group_name} already exists for {stream}")
                else:
                    print(f"An error occured when creating groups: {e}")
    
    async def read_streams(self, streams):
        print("Reading Streams...")
        streams = {stream: '0' for stream in streams}
        try:
            print(f"Reading from streams: {streams}")
            response = await self.redis.xreadgroup(
                groupname=self.group_name,
                consumername=self.consumer_name,
                streams=streams,
                count=6,
                block=5000,
            ) #This will fetch the last 6 entires, see count. It will also keep trying for 5000 miliseconds (5 Seconds)
            print(f"Read response: {response}")
            return response
        except Exception as e:
            print(f"Error reading from streams: {e}")
            return []
        
    async def write_to_influxdb(self, points):
        print("Writing to InfluxDb")
        try:
            print(f"Writing points: {points}")
            self.write_api.write(self.bucket, self.org, points)
            print("Write to InfluxDB successful")
        except Exception as e:
            print(f"Error writing to InfluxDB: {e}")
            
    def create_points(self, stream_name, messages):
        print(f"Creating points for stream {stream_name}...")
        points = []
        for message_id, message in messages:
            print(f"Processing message ID: {message_id}, message: {message}")
            timestamp = message.get('timestamp')
            data = {key: float(value) for key, value in message.items() if key != 'timestamp'}
            point = Point(stream_name).time(datetime.fromisoformat(timestamp)).fields(data)
            points.append(point)
        print(f"Created points: {points}")
        return points
    async def process_streams(self, streams):
        print("Starting stream processing")
        await self.setup_groups(streams)
        while True:
            now = datetime.utcnow()
            print(f"Starting a new iteration at {now}")
            response = await self.read_streams(streams)
            if response:
                print("Processing stream data...")
                for stream_name, messages in response:
                    points = self.create_points(stream_name, messages)
                    await self.write_to_influxdb(points)
            else:
                print("No new messages found")
            later = datetime.utcnow()
            duration = (later - now).total_seconds()
            print(f"Finished processing. Duration: {duration} seconds. Sleeping for {self.collection_interval} seconds.")
            await asyncio.sleep(self.collection_interval)
            
            
if __name__ == "__main__":
    streams = ['network_data']  # List all your streams here
    reader = SaveData()
    print("Starting StreamToInfluxDB...")
    asyncio.run(reader.process_streams(streams))