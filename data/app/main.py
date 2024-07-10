from cp import INA260Camera
from rp import INA260Router
from env import AHT10
from net import NetworkPingTest
from cell import CellularMetrics
from system_info import save

import os
import redis

env = AHT10()
cp = INA260Camera()
rp = INA260Router()
net = NetworkPingTest()
#cell = CellularMetrics()

class RedisSubscriber:
    def __init__(self):
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis = redis.Redis(host=redis_host, port=6379, db=0)

    def subscribe_to_channel(self, channel):
        pubsub = self.redis.pubsub()
        pubsub.subscribe(channel)
        return pubsub

    def listen(self, channel):
        pubsub = self.subscribe_to_channel(channel)
        for message in pubsub.listen():
            if message['type'] == 'message':
                print(f"Received message: {message['data']}")

def main():
    save()
    rp.rp_run()
    cp.cp_run()
    env.env_run()
    #cell.cell_run() Cellular collection is working. Turning off to return SIM card
    net.net_run()
        
if __name__ == "__main__":
    subscriber = RedisSubscriber()
    subscriber.listen('test_channel')
    main()