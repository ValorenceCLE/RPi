import asyncio
from redis.asyncio import Redis  # type: ignore
import os
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision  # type: ignore
from influxdb_client.client.write_api import ASYNCHRONOUS, WriteOptions  # type: ignore

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
                await self.redis.xgroup_create(stream, self.group_name, id='0', mkstream=True)
                print(f"Group {self.group_name} created for {stream}")
            except Exception as e:
                if "BUSYGROUP" not in str(e):
                    print(f"Error creating group {self.group_name} for {stream}: {e}")
                else:
                    print(f"Group {self.group_name} already exists for {stream}")

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
            print(f"Read response: {response}")
            return response
        except Exception as e:
            print(f"Error reading from streams: {e}")
            return []

    async def write_to_influxdb(self, points):
        try:
            print(f"Writing points: {points}")
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            print("Write to InfluxDB successful")
        except Exception as e:
            print(f"Error writing to InfluxDB: {e}")

    def create_points(self, stream_name, messages):
        points = []
        for message_id, message in messages:
            print(f"Processing message {message_id} from stream {stream_name}: {message}")
            try:
                timestamp = message[b'timestamp'].decode() if b'timestamp' in message else datetime.utcnow().isoformat()
                data = {}
                for key, value in message.items():
                    key = key.decode()
                    value = float(value.decode()) if key != 'timestamp' else value.decode()
                    data[key] = value
                point = Point(stream_name.decode()).tag("source", stream_name.decode()).time(datetime.fromisoformat(timestamp))
                for key, value in data.items():
                    if key != 'timestamp':
                        point = point.field(key, value)
                points.append(point)
                print(f"Created point: {point}")
            except Exception as e:
                print(f"Error processing message {message_id}: {e}")
        return points

    async def process_streams(self):
        await self.setup_groups()
        while True:
            now = datetime.utcnow()
            print(f"Starting a new iteration at {now}")
            response = await self.read_streams()
            if response:
                for stream_name, messages in response:
                    points = self.create_points(stream_name, messages)
                    if points:
                        await self.write_to_influxdb(points)
            later = datetime.utcnow()
            duration = (later - now).total_seconds()
            print(f"Finished processing. Duration: {duration} seconds. Sleeping for {self.collection_interval} seconds.")
            await asyncio.sleep(self.collection_interval)

if __name__ == "__main__":
    streams = ['network_data', 'camera_data']
    reader = SaveData(streams)
    asyncio.run(reader.process_streams())
