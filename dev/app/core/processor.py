import asyncio
from datetime import datetime, timezone
from influxdb_client import Point
from utils.logging_setup import local_logger as logger
from utils.config import settings
from utils.singleton import InfluxWriter, RedisClient

class RelayProcessor:
    def __init__(self, relay_id: str):
        self.relay_id = relay_id
        self.redis = None
        self.write_api = None
        self.collection_interval = 60
        self.bucket = settings.BUCKET
        self.org = settings.ORG
        self.group_name = f'relay_group_{self.relay_id}'
        self.consumer_name = f'processor_{self.relay_id}'
    
    async def async_init(self):
        self.redis = await RedisClient.get_instance()
        self.write_api = await InfluxWriter.get_instance()
        await self.setup_groups()

    async def setup_groups(self):
        try:
            await self.redis.xgroup_create(self.relay_id, self.group_name, id='0', mkstream=True)
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                logger.critical(f"Error creating group {self.group_name} for {self.relay_id}: {e}")
            else:
                logger.debug(f"Group {self.group_name} already exists for {self.relay_id}")

    async def process_relay_stream(self):
        try:
            message = await self.redis.xreadgroup(
                groupname=self.group_name,
                consumername=self.consumer_name,
                streams={self.relay_id: '>'},
                count=60,
                block=1000
            )
            if message:
                await self.process_data(message)
        except Exception as e:
            logger.error(f"Error reading stream {self.relay_id}: {e}")
    
    async def process_data(self, message):
        _volts=0.0
        _watts=0.0
        _amps=0.0
        msgs = message[0][1]
        count=0
        for message_id, message in msgs:
            try:
                _volts += float(message[b'volts'])
                _watts += float(message[b'watts'])
                _amps += float(message[b'amps'])
                count += 1
            except Exception as e:
                logger.error(f"Error processing message {message_id}: {e}")
        if count > 0:
            avg_volts = round(_volts / count,2)
            avg_watts = round(_watts / count,2)
            avg_amps = round(_amps / count,2)
            point = Point(self.relay_id)\
                .tag("source", self.relay_id)\
                .field("volts", avg_volts)\
                .field("watts", avg_watts)\
                .field("amps", avg_amps)\
                .time(datetime.now(timezone.utc).astimezone().isoformat())
            await self.write_to_influxdb(point)

    async def write_to_influxdb(self,point):
        try:
            await self.write_api.write(bucket=self.bucket, org=self.org, record=point)
        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {e}")

    async def run(self):
        await self.async_init()
        while True:
            await asyncio.sleep(self.collection_interval)
            await self.process_relay_stream()


class GeneralProcessor:
    def __init__(self):
        self.redis = None
        self.write_api = None
        self.collection_interval = 300
        self.bucket = settings.BUCKET
        self.org = settings.ORG
        self.group_name = 'general_group'
        self.consumer_name = 'general_processor'
        self.streams = ['cellular', 'network', 'environment']

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
                    logger.critical(f"Error creating group {self.group_name} for {stream}: {e}")
                else:
                    logger.debug(f"Group {self.group_name} already exists for {stream}")

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
            logger.error(f"Error reading stream {stream_name}: {e}")
            return []

    async def write_to_influxdb(self, points):
        try:
            await self.write_api.write(bucket=self.bucket, org=self.org, record=points)
        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {e}")

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
                logger.error(f"Error processing message {message_id}: {e}")
        return points
    
    async def process_single_stream(self, stream_name):
        response = await self.read_single_stream(stream_name)
        if response:
            for stream_name, messages in response:
                points = await self.create_points(stream_name, messages)
                if points:
                    await self.write_to_influxdb(points)

    async def run(self):
        await self.async_init()
        while True:
            await asyncio.sleep(self.collection_interval)
            tasks = [asyncio.create_task(self.process_single_stream(stream)) for stream in self.streams]
            await asyncio.gather(*tasks)