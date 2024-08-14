from fastapi import APIRouter

router = APIRouter()


@router.post("API/signal")
async def signal_quality():
    pass
    #function to get the signal quality from the redis stream and analyze it to determine the quality of the signal in readable words. (Great, Good, Fair, Poor, Bad)
    
@router.get("API/{device}/{state}")
async def relay_control(device: str, state: bool):
    pass
    #Universal function to control the relay logic for the site.
    #Use the device name to specify which relay is going to be modified.
    #use the state to control if it is ON/OFF. True/False 1/0
    #Example: api/camera/0
    #Extra logic is needed in order to make sure the Router comes back online.
    
@router.post("API/guage")
async def live_guages():
    pass
    #Functions to pull the streams from Redis and push the data into the guages
    #Ideally set this up so that this function and ONE JS file can be used universally for all the guages.