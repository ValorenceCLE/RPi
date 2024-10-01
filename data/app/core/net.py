import os 
from datetime import datetime
import asyncio
import aioping # type: ignore
from redis.asyncio import Redis #type: ignore
from utils.logging_setup import logger

# This script also needs better error handling

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
            valid_responses = list(filter(None, response_list))
            if valid_responses:
                avg_rtt = sum(valid_responses) / len(valid_responses)
                min_rtt = min(valid_responses)
                max_rtt = max(valid_responses)
            else:
                avg_rtt = None
                min_rtt = None
                max_rtt = None
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
        """Saves the data to Redis."""
        try:
            timestamp = datetime.utcnow().isoformat()
            data = {
                "timestamp": timestamp,
                "avg_rtt": avg_rtt,
                "min_rtt": min_rtt,
                "max_rtt": max_rtt,
                "packet_loss_percent": packet_loss_percent
            }
            await self.redis.xadd('network_data', data)
        except Exception as e:
            logger.error(f"Failed to stream data to Redis: {e}", exc_info=True)
        
    async def run(self):
        while True:
            await self.run_ping_test()
            await asyncio.sleep(self.collection_interval)