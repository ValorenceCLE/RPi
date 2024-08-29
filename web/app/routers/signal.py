from fastapi import APIRouter #type: ignore
from redis.asyncio import Redis #type: ignore
import os

router = APIRouter()
redis = Redis.from_url(os.getenv('REDIS_URL'))

def evaluate_rsrp(value):
    if value >= -80:
        return 4
    elif value >= -90:
        return 3
    elif value >= -100:
        return 2
    else:
        return 1
    
def evaluate_rsrq(value):
    if value >= -9:
        return 3
    elif value >= -12:
        return 2
    else:
        return 1
    
def evaluate_sinr(value):
    if value >= 10:
        return 4
    elif value >= 5:
        return 3
    elif value >= 0:
        return 2
    else:
        return 1

def results(rsrp_score, rsrq_score, sinr_score):
    score = rsrp_score + rsrq_score + sinr_score
    if score >= 10:
        return "Strong"
    elif score >= 8:
        return "Good"
    elif score >= 6:
        return "Fair"
    else:
        return "Poor"

# Function to pull the most recent data from redis from the cellular stream
async def fetch_info(stream: str):
    try:
        response = await redis.xrevrange(stream, count=1)
        if response:
            _, data = response[0]
            # Decode and round values, Skip timestamp
            decoded_data = {k.decode(): round(float(v.decode()), 1) if k.decode() != "timestamp" else v.decode() for k, v in data.items()}
            return decoded_data
        else:
            print(f"No data found in stream {stream}")
            return None
    except Exception as e:
        print(f"Error reading from Redis stream: {stream}, Error: {e}")
        return None
    
# Evaluate the cellular data
# Handle -9999 values as Errors
async def evaluate_signal():
    data = await fetch_info("cellular_data")
    if not data:
        return {"status": "ERROR: No Data"}
    
    rsrp = data.get("rsrp", None)
    rsrq = data.get("rsrq", None)
    sinr = data.get("sinr", None)
    
    if rsrp is None or rsrq is None or sinr is None:
        return {"status": "ERROR: Incomplete"}
    
    rsrp_score = evaluate_rsrp(rsrp)
    rsrq_score = evaluate_rsrq(rsrq)
    sinr_score = evaluate_sinr(sinr)
    
    quality = results(rsrp_score, rsrq_score, sinr_score)
    return {"RSRP": rsrp, "RSRQ": rsrq, "SINR": sinr, "Quality": quality}

@router.get("/cellular")
async def signal_quality():
    results = await evaluate_signal()
    return results