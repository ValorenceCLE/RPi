from cp import INA260Camera
from rp import INA260Router
from env import AHT10
from net import ping_test #Needs root permissions to run
from cell import cell
from system_info import save
env = AHT10()
cp = INA260Camera()
rp = INA260Router()

def main():
    save()
    rp.rp_test()
    cp.cp_test()
    env.env_test()
    cell()
    #ping_test()
        
if __name__ == "__main__":
    main()