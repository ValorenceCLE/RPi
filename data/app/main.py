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
    
    # Initial Start up to gather System Info
    await start_up() # Set up System Info
    await asyncio.sleep(1) # Make sure System Info is set up
    
    # Initialize Dashboard
    dashboard = Dashboard_Setup()
    await dashboard.run()
    
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