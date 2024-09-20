import os 
from datetime import datetime
import asyncio
import aioping # type: ignore
from redis.asyncio import Redis #type: ignore
from logging_setup import logger
# This script also needs better error handling
# Also check the packet loss logic. Some of the data being shown in the database doesnt make sense for data point that is supposed to be a %

class NetworkPing:
    def __init__(self, target_ip='8.8.8.8'):
        self.target_ip = target_ip
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis = Redis.from_url(self.redis_url)
        self.collection_interval = 30  # Interval in seconds between ping tests
        self.ping_count = 5  # Number of pings per test
        
    async def run_ping_test(self):
        try:
            response_list = await asyncio.gather(*[self.ping_host() for _ in range(self.ping_count)])
            packets_lost = response_list.count(None)
            packet_loss_percent = packets_lost / self.ping_count * 100
            avg_rtt = sum(filter(None, response_list)) / len(response_list)
            max_rtt = max(filter(None, response_list))
            min_rtt = min(filter(None, response_list))
            # Save data to Redis stream
            await self.stream_data(avg_rtt, min_rtt, max_rtt, packet_loss_percent)

        except Exception as e:
            await logger.error(f"Failed to perform ping test: {e}")
            
    async def ping_host(self):
        try:
            delay = await aioping.ping(self.target_ip)
            return delay * 1000
        except TimeoutError:
            return None
    
    async def stream_data(self, avg_rtt, min_rtt, max_rtt, packet_loss_percent):
        timestamp = datetime.utcnow().isoformat()
        data = {
            "timestamp": timestamp,
            "avg_rtt": avg_rtt,
            "min_rtt": min_rtt,
            "max_rtt": max_rtt,
            "packet_loss_percent": packet_loss_percent
        }
        await self.redis.xadd('network_data', data)
        
    async def run(self):
        while True:
            await self.run_ping_test()
            await asyncio.sleep(self.collection_interval)
            

        

            