from redis.asyncio import Redis #type: ignore
import json
import os
from influxdb_client import InfluxDBClient, Point # type: ignore
from influxdb_client.client.write_api import ASYNCHRONOUS, WriteOptions # type: ignore
from influxdb_client import QueryApi # type: ignore
class AlertPublisher:
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL')
        self.redis = Redis.from_url(self.redis_url)
        self.channel = "alerts"
        self.token = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
        self.org = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
        self.bucket = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
        self.url = os.getenv('INFLUXDB_URL')
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=WriteOptions(write_type=ASYNCHRONOUS, batch_size=500, flush_interval=10_000))
        
    async def publish_alert(self, source: str, value, level: str, timestamp: str, message: str):
        alert_data = {
            "source": source,
            "value": value,
            "level": level,
            "timestamp": timestamp,
            "message": message
        }
        try:
            message = json.dumps(alert_data)
            await self.redis.publish(self.channel, message)
            print(f"Published alert: {message}")
            await self.write_to_influxdb(alert_data)
        except Exception as e:
            print(f"Error publishing alert: {e}")
    
    async def write_to_influxdb(self, alert_data):
        try:
            point = Point("alerts") \
                .tag("source", alert_data["source"]) \
                .tag("level", alert_data["level"]) \
                .field("value", alert_data["value"]) \
                .tag("message", alert_data["message"]) \
                .time(alert_data["timestamp"])
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
        
        except Exception as e:
            print(f"Error writing to InfluxDB: {e}")
    
    async def close(self):
        await self.redis.close()
        self.client.close()

    def delete(self):
        delete_api = self.client.delete_api()
        delete_api.delete(start='1970-01-01T00:00:00Z', stop='2030-01-01T00:00:00Z', predicate='_measurement="alerts"', bucket=self.bucket, org=self.org)

    def query(self):
        query_api = QueryApi(self.client)
        query = f'from(bucket: "{self.bucket}") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "alerts")'
        tables = query_api.query(query, org=self.org)
        for table in tables:
            for row in table.records:
                print(row.values)

# Singleton instance of AlertPublisher
alert_publisher = AlertPublisher()

if __name__ == "__main__":
    dl = AlertPublisher()
    choice = input("Do you want to delete all alerts? Or Query Alerts? (delete/query): ")
    if choice == "delete":
        dl.delete()
    elif choice == "query":
        dl.query()
    else:
        print("Invalid choice")