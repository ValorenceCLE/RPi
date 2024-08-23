import asyncio
from cp import INA260Camera
from rp import INA260Router
from sp import INA260System
from env import AHT10
from net import NetworkPing
from cell import CellularMetrics
from system_info import start_up
from listener import Processor
from dashboard import Dashboard_Setup


async def main():
    net = NetworkPing() 
    cell = CellularMetrics()
    cp = INA260Camera()
    rp = INA260Router()
    sp = INA260System()
    env = AHT10()
    streams = ['network_data', 'camera_data', 'router_data', 'environment_data', 'system_data', 'cellular_data'] #List the Streams that need to be listened too, pass var to the Processor
    prc = Processor(streams) #Saves Data to InfluxDB
    dashboard = Dashboard_Setup()

    
    
    tasks = [
        asyncio.create_task(net.run()),
        asyncio.create_task(cp.run()),
        asyncio.create_task(rp.run()),
        asyncio.create_task(sp.run()), #Currently No Sensor Connected
        asyncio.create_task(env.run()),
        asyncio.create_task(cell.cell_run()), #Currently Using demo sim, need to give back
        asyncio.create_task(prc.process_streams())
    ]
    await start_up() # Set up System Info
    await dashboard.run()
    await asyncio.sleep(3) # Make sure System Info is set up
    await asyncio.gather(*tasks)
    
    
if __name__ == '__main__':
    asyncio.run(main())