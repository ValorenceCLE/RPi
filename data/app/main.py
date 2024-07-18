# import asyncio
# from cp import INA260Camera
# from rp import INA260Router
# from env import AHT10
# from net import NetworkPingTest
# from cell import CellularMetrics
# from system_info import save
# env = AHT10()
# cp = INA260Camera()
# rp = INA260Router()
# net = NetworkPingTest()
# #cell = CellularMetrics()
# async def main():
#     save()
#     await asyncio.gather(net.net_run())
#     rp.rp_run()
#     cp.cp_run()
#     env.env_run()
#     #cell.cell_run() Cellular collection is working. Turning off to return SIM card
        
# if __name__ == "__main__":
#     asyncio.run(main())

import asyncio
from cp import INA260Camera
from rp import INA260Router
from env import AHT10
from net import NetworkPing
from cell import CellularMetrics
#from system_info import save

env = AHT10()
cp = INA260Camera()
rp = INA260Router()
net = NetworkPing()
cell = CellularMetrics()

async def run_synchronous_task(task_func):
    """Run a synchronous task in a separate thread."""
    await asyncio.to_thread(task_func)

async def main():
    # Run the asynchronous network ping test
    async_tasks = [
        net.net_run(),
        cell.cell_run()
    ]

    # Run the synchronous tasks using asyncio.to_thread
    sync_tasks = [
        run_synchronous_task(rp.rp_run),
        run_synchronous_task(cp.cp_run),
        run_synchronous_task(env.env_run),
    ]

    # Combine both async and sync tasks
    await asyncio.gather(*async_tasks, *sync_tasks)

if __name__ == "__main__":
    #save()
    asyncio.get_event_loop().run_until_complete(cell.cell_run())