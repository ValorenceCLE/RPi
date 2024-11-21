from utils.config import settings
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync 
from influxdb_client.client.write_api_async import WriteApiAsync 
from influxdb_client.client.query_api_async import QueryApiAsync
from redis.asyncio import Redis
import asyncio 
from utils.logging_setup import local_logger as logger

class InfluxClient:
    _instance = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        raise RuntimeError("Use 'InfluxDBClient.get_instance()' to get the instance.")

    @classmethod
    async def get_instance(cls):
        async with cls._lock:
            if cls._instance is None:
                token = settings.TOKEN
                org = settings.ORG
                url = settings.INFLUXDB_URL
                try:
                    client = InfluxDBClientAsync(url=url, token=token, org=org)
                    cls._instance = client
                    logger.info("InfluxDB Client Created")
                except Exception as e:
                    logger.critical(f"Failed to create InfluxDB Client: {e}")
                    raise e
            return cls._instance
    @classmethod
    async def close_instance(cls):
        async with cls._lock:
            if cls._instance:
                await cls._instance.__aexit__(None, None, None)
                cls._instance = None


class InfluxWriter:
    _instance = None
    _lock = asyncio.Lock()
    
    @classmethod
    async def get_instance(cls):
        async with cls._lock:
            if cls._instance is None:
                client = await InfluxClient.get_instance()
                cls._instance = WriteApiAsync(client)
            return cls._instance
        
    @classmethod
    async def close_instance(cls):
        async with cls._lock:
            if cls._instance:
                await cls._instance.__aexit__(None, None, None)
                cls._instance = None
                
                
class InfluxQuery:
    _instance = None
    _lock = asyncio.Lock()
    
    @classmethod
    async def get_instance(cls):
        async with cls._lock:
            if cls._instance is None:
                client = await InfluxClient.get_instance()
                cls._instance = QueryApiAsync(client)
            return cls._instance
        
    @classmethod
    async def close_instance(cls):
        async with cls._lock:
            if cls._instance:
                await cls._instance.__aexit__(None, None, None)
                cls._instance = None

class RedisClient:
    _instance = None
    _lock = asyncio.Lock()
    
    @classmethod
    async def get_instance(cls):
        async with cls._lock:
            if cls._instance is None:
                redis_url = settings.REDIS_URL
                cls._instance = Redis.from_url(redis_url)
            return cls._instance
    @classmethod
    async def close_instance(cls):
        async with cls._lock:
            if cls._instance:
                await cls._instance.close()
                cls._instance = None