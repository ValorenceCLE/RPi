#Network Data from running ping tests
#Naming Convention: Router Serial Number - NET
#i.e: 192F10E882C7-NET

from pythonping import ping
import time

def ping_test():
    for i in range(5):
        ping('8.8.8.8', verbose=True)
        print(ping)
        time.sleep(5)
        

#This should have good error handling but even if the router is offline we should collect this data because it will show that the router was offline
#We just need to make sure that it doesnt run into errors when trying to ping a possibly down router
#Is jitter something we actually need to save?
#Do we save all or some of the packet loss information since most the time it will be 0?
