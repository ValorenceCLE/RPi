import asyncio

from core.cp import INA260Camera
from core.rp import INA260Router
from core.sp import INA260System
from core.env import AHT10
from core.net import NetworkPing
from core.cell import CellularMetrics

from utils.system_info import start_up
from utils.listener import Processor
from utils.dashboard import Dashboard_Setup
from utils.logging_setup import logger

async def main():
    await logger.info("Application started")
    
    # Initial Start up to gather System Info
    await start_up() # Set up System Info
    
    # Initialize Dashboard
    dashboard = Dashboard_Setup()
    await dashboard.run()
    dashboard.close()
    await asyncio.sleep(1) # Make sure System Info is set up
    
    # Initialize collection scripts
    net = NetworkPing() # Network Metrics
    cell = CellularMetrics() # Cellular Metrics
    cp = INA260Camera() # Camera Metrics
    rp = INA260Router() # Router Metrics
    sp = INA260System() # System Metrics
    env = AHT10() # Environmental Metrics
    
    # List the Streams that need to be listened to, pass var to the Processor
    streams = ['network_data', 'camera_data', 'router_data', 'environment_data', 'system_data', 'cellular_data'] #List the Streams that need to be listened too, pass var to the Processor
    prc = Processor(streams) #Saves Data to InfluxDB
    
    tasks = [
        asyncio.create_task(net.run()),
        asyncio.create_task(cp.run()),
        asyncio.create_task(rp.run()),
        asyncio.create_task(sp.run()),
        asyncio.create_task(env.run()),
        asyncio.create_task(cell.cell_run()), #Currently Using demo sim, need to give back
        asyncio.create_task(prc.process_streams())
    ]
    # Run all tasks concurrently
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())