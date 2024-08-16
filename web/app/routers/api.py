from fastapi import APIRouter, HTTPException #type: ignore
import RPi.GPIO as GPIO
import asyncio
from datetime import datetime, timedelta
router = APIRouter()

RELAYS = {
    "router": 13,  # GPIO pin for Router
    "camera": 17,  # GPIO pin for Camera
    "strobe": 5,  # GPIO pin for Strobe
    "fan": 27     # GPIO pin for Fan
}

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)  # Disable warnings

# Initialize GPIO pins
for name, pin in RELAYS.items():
    GPIO.setup(pin, GPIO.OUT)

# Ensure Router and Camera are always on at startup
GPIO.output(RELAYS["router"], GPIO.HIGH)
GPIO.output(RELAYS["camera"], GPIO.HIGH)

# Functions to handle relay control
relay_states = {name: {"status": "off", "timer_end": None} for name in RELAYS}

@router.post("/relay/{name}/{action}")
async def control_relay(name: str, action: str):
    if name not in RELAYS:
        raise HTTPException(status_code=404, detail="Relay not found")
    
    pin = RELAYS[name]
    
    if name == "router" and action == "restart":
        GPIO.output(pin, GPIO.LOW)  # Turn off router
        await asyncio.sleep(10)  # Wait 10 seconds
        GPIO.output(pin, GPIO.HIGH)  # Turn router back on
        # Update the status in your storage mechanism to reflect the change
        # Set status back to 'on'
        return {"status": "success", "relay": name, "action": "restarted"}
    
    if action == "on":
        GPIO.output(pin, GPIO.HIGH)
        # Update your status mechanism here if needed
    elif action == "off":
        GPIO.output(pin, GPIO.LOW)
        # Update your status mechanism here if needed
    elif action == "run_5_min":
        GPIO.output(pin, GPIO.HIGH)
        # Update your status mechanism to 'running'
        await asyncio.sleep(300)  # Run for 5 minutes
        GPIO.output(pin, GPIO.LOW)
        # Update your status mechanism to 'off'
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    return {"status": "success", "relay": name, "action": action}


@router.get("/relay/status")
async def get_relay_status():
    current_time = datetime.now()
    
    for name, state in relay_states.items():
        # Check if the relay is in a timed "running" state
        if state["timer_end"] and current_time < state["timer_end"]:
            relay_states[name]["status"] = "running"
        else:
            # Update the status based on the actual GPIO pin state
            if GPIO.input(RELAYS[name]) == GPIO.HIGH:
                relay_states[name]["status"] = "on"
            else:
                relay_states[name]["status"] = "off"
            relay_states[name]["timer_end"] = None  # Reset the timer if it's done

    # Return the current status of all relays
    return {name: state["status"] for name, state in relay_states.items()}

    
@router.post("API/guage")
async def live_guages():
    pass
    #Functions to pull the streams from Redis and push the data into the guages
    #Ideally set this up so that this function and ONE JS file can be used universally for all the guages.
    
@router.post("API/graph")
async def graph_data():
    pass
    #Pull the live data from Redis and graph it.
    #Graph all values
    #One hour time frame. Else Route to InfluxDB dashboard
    