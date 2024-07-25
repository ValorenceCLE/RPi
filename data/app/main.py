import asyncio
from cp import INA260Camera
from rp import INA260Router
#from sp import INA260System
from env import AHT10
from net import NetworkPing
from cell import CellularMetrics
from system_info import save

async def main():
    net = NetworkPing()
    #cell = CellularMetrics()
    cp = INA260Camera()
    rp = INA260Router()
    #sp = INA260System()
    env = AHT10()
    
    
    tasks = [
        asyncio.create_task(net.run()),
        asyncio.create_task(cp.run()),
        asyncio.create_task(rp.run()),
        #asyncio.create_task(sp.run()), #Currently No Sensor Connected
        asyncio.create_task(env.run()),
        #asyncio.create_task(cell.cell_run()), #Currently No SIM
    ]
    
    await asyncio.gather(*tasks)
    
    
if __name__ == '__main__':
    asyncio.run(save())
    asyncio.sleep(3)
    asyncio.run(main())