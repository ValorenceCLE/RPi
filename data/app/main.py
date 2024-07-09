from cp import INA260Camera
from rp import INA260Router
from env import AHT10
from net import NetworkPingTest
from cell import cell
from system_info import save
#env = AHT10()
cp = INA260Camera()
rp = INA260Router()
net = NetworkPingTest()
def main():
    save()
    rp.rp_run()
    cp.cp_run()
    #env.env_run()
    cell()
    net.net_run()
        
if __name__ == "__main__":
    main()