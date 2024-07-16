#This is a dumy script provided by Chat GPT
import os
import asyncio
from redis.asyncio import Redis
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

class DataAggregator:
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis = Redis.from_url(self.redis_url)
        self.influx_url = os.getenv('INFLUX_URL', 'http://localhost:8086')
        self.influx_token = os.getenv('INFLUX_TOKEN', 'your-influxdb-token')
        self.influx_org = os.getenv('INFLUX_ORG', 'your-organization')
        self.influx_bucket = os.getenv('INFLUX_BUCKET', 'network_data')
        self.influx_client = InfluxDBClient(url=self.influx_url, token=self.influx_token, org=self.influx_org)
        self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
        self.aggregation_interval = 300  # 5 minutes

    async def listen_and_aggregate(self):
        last_id = '0-0'
        while True:
            try:
                results = await self.redis.xread({'network_data': last_id}, count=100, block=0)
                for _, messages in results:
                    for message_id, data in messages:
                        last_id = message_id
                        await self.process_data(data)
            except Exception as e:
                print(f"Error processing stream: {e}")
                await asyncio.sleep(5)

    async def process_data(self, data):
        timestamp = data[b'timestamp'].decode('utf-8')
        avg_rtt = float(data[b'avg_rtt'])
        min_rtt = float(data[b'min_rtt'])
        max_rtt = float(data[b'max_rtt'])
        packet_loss_percent = float(data[b'packet_loss_percent'])

        point = Point("network_metrics") \
            .tag("target_ip", "8.8.8.8") \
            .field("avg_rtt", avg_rtt) \
            .field("min_rtt", min_rtt) \
            .field("max_rtt", max_rtt) \
            .field("packet_loss_percent", packet_loss_percent) \
            .time(timestamp)

        self.write_api.write(bucket=self.influx_bucket, record=point)

    async def run(self):
        await self.listen_and_aggregate()

if __name__ == "__main__":
    aggregator = DataAggregator()
    asyncio.run(aggregator.run())