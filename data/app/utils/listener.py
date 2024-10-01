import asyncio
from redis.asyncio import Redis  # type: ignore
from datetime import datetime
from influxdb_client import Point # type: ignore
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync # type: ignore
from influxdb_client.client.write_api_async import WriteApiAsync # type: ignore
from utils.logging_setup import logger # Custom Async Logger ==> logging_setup.py
from utils.config import settings
from utils.clients import InfluxWriter, RedisClient

class Processor:
    def __init__(self, streams):
        """
        Initialize the Listener class.

        Args:
            streams (list): A list of stream names to listen to.
                Passed in main.py
        """
        self.streams = streams
        self.group_name = 'data_group'
        self.consumer_name = 'influxdb'
        self.bucket = settings.BUCKET
        self.org = settings.ORG
        self.collection_interval = 300  # Pull data every 5 minutes
        self.batch_points = []
        self.client = None
        self.write_api = None
        
    # Async Init Function
    async def async_init(self):
        self.redis = await RedisClient.get_instance()
        self.write_api = await InfluxWriter.get_instance()
        await self.setup_groups()
    
    async def setup_groups(self):
        # Create a consumer group for each stream
        for stream in self.streams:
            try:
                await self.redis.xgroup_create(stream, self.group_name, id='0', mkstream=True)
            except Exception as e:
                if "BUSYGROUP" not in str(e):
                    await logger.critical(f"Error creating group {self.group_name} for {stream}: {e}")
                else:
                    await logger.debug(f"Group {self.group_name} already exists for {stream}")

    async def read_single_stream(self, stream_name):
        try:
            response = await self.redis.xreadgroup(
                groupname=self.group_name,
                consumername=self.consumer_name,
                streams={stream_name: '>'},
                count=10,
                block=1000
            )
            return response
        except Exception as e:
            await logger.error(f"Error reading stream {stream_name}: {e}")
            return []

    async def write_to_influxdb(self, points):
        try:
            await self.write_api.write(bucket=self.bucket, org=self.org, record=points)
        except Exception as e:
            await logger.error(f"Error writing to InfluxDB: {e}")

    async def create_points(self, stream_name, messages):
        points = []
        for message_id, message in messages:
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
            except Exception as e:
                await logger.error(f"Error processing message {message_id}: {e}")
        return points

    async def process_single_stream(self, stream_name):
        response = await self.read_single_stream(stream_name)
        if response:
            for stream_name, messages in response:
                points = await self.create_points(stream_name, messages)
                if points:
                    await self.write_to_influxdb(points)
    
    async def process_streams(self):
        """
        Process all streams concurrently.
        Each stream is handled by its own task, which runs in parallel using asyncio.
        After processing all streams, wait for `self.collection_interval` before the next iteration.
        """
        await self.async_init()
        await self.setup_groups()
        while True:
            await asyncio.sleep(self.collection_interval)
            tasks = [asyncio.create_task(self.process_single_stream(stream)) for stream in self.streams]
            await asyncio.gather(*tasks)

            
if __name__ == "__main__":
    streams = ['network_data', 'camera_data', 'router_data', 'environment_data']
    reader = Processor(streams)
    asyncio.run(reader.process_streams())
