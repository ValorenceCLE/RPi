import asyncio
from redis.asyncio import Redis  # type: ignore
import os
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, Point, WriteOptions

class StreamToInfluxDB:
    def __init__(self):
        print("Initializing StreamToInfluxDB class...")
        self.redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
        self.influxdb_url = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
        self.influxdb_token = os.getenv('INFLUXDB_TOKEN', 'your-token')
        self.influxdb_org = os.getenv('INFLUXDB_ORG', 'your-org')
        self.influxdb_bucket = os.getenv('INFLUXDB_BUCKET', 'your-bucket')
        
        print(f"Connecting to Redis at {self.redis_url}")
        self.redis = Redis.from_url(self.redis_url)
        
        print(f"Connecting to InfluxDB at {self.influxdb_url}")
        self.influxdb_client = InfluxDBClient(url=self.influxdb_url, token=self.influxdb_token, org=self.influxdb_org)
        
        self.group_name = 'data_group'
        self.consumer_name = 'consumer_1'
        self.collection_interval = 300  # Pull data every 5 minutes

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
                    print(f"Error creating group {self.group_name} for {stream}: {e}")

    async def read_streams(self, streams):
        print("Reading streams...")
        try:
            response = await self.redis.xreadgroup(
                groupname=self.group_name,
                consumername=self.consumer_name,
                streams=streams,
                count=10,  # Fetch the last 10 entries
                block=5000
            )
            print(f"Read response: {response}")
            return response
        except Exception as e:
            print(f"Error reading from streams: {e}")
            return []

    async def write_to_influxdb(self, points):
        print("Writing to InfluxDB...")
        write_api = self.influxdb_client.write_api(write_options=WriteOptions(batch_size=500, flush_interval=10_000))
        try:
            print(f"Writing points: {points}")
            write_api.write(bucket=self.influxdb_bucket, org=self.influxdb_org, record=points)
            print("Write to InfluxDB successful")
        except Exception as e:
            print(f"Error writing to InfluxDB: {e}")

    def create_points(self, stream_name, messages):
        print(f"Creating points for stream {stream_name}...")
        points = []
        for message_id, message in messages:
            print(f"Processing message ID: {message_id}, message: {message}")
            timestamp = message.get('timestamp', datetime.utcnow().isoformat())
            data = {key: float(value) for key, value in message.items() if key != 'timestamp'}
            point = Point(stream_name).time(datetime.fromisoformat(timestamp)).fields(data)
            points.append(point)
        print(f"Created points: {points}")
        return points

    async def process_streams(self, streams):
        print("Starting stream processing...")
        await self.setup_groups(streams)
        while True:
            now = datetime.utcnow()
            print(f"Starting new iteration at {now}")
            response = await self.read_streams(streams)
            if response:
                print("Processing stream data...")
                for stream_name, messages in response:
                    points = self.create_points(stream_name, messages)
                    await self.write_to_influxdb(points)
            else:
                print("No new messages read from streams.")
            later = datetime.utcnow()
            duration = (later - now).total_seconds()
            print(f"Finished processing. Duration: {duration} seconds. Sleeping for {self.collection_interval} seconds.")
            await asyncio.sleep(self.collection_interval)

if __name__ == "__main__":
    streams = ['network_data']  # List all your streams here
    reader = StreamToInfluxDB()
    print("Starting StreamToInfluxDB...")
    asyncio.run(reader.process_streams(streams))
