from fastapi import APIRouter #type: ignore
from redis.asyncio import Redis #type: ignore
from core.config import settings
from core.logger import logger

router = APIRouter()
redis = Redis.from_url(settings.REDIS_URL)

def evaluate_rsrp(value):
    if value > -80:
        return 4
    elif value in range(-80, -90):
        return 3
    elif value in range(-90, -100):
        return 2
    else:
        return 1
    
def evaluate_rsrq(value):
    if value > -10:
        return 4
    elif value in range(-10, -15):
        return 3
    elif value in range(-15, -20):
        return 2
    else:
        return 1
    
def evaluate_sinr(value):
    if value >= 20:
        return 4
    elif value in range(13, 20):
        return 3
    elif value in range(0, 13):
        return 2
    else:
        return 1

def results(rsrp_score, rsrq_score, sinr_score):
    rsrp_weight = 0.5
    rsrq_weight = 0.3
    sinr_weight = 0.2
    weighted_score = (rsrp_score * rsrp_weight) + (rsrq_score * rsrq_weight) + (sinr_score * sinr_weight)
    if weighted_score >= 3.5:
        return "Excellent"
    elif weighted_score >= 2.5:
        return "Good"
    elif weighted_score >= 1.5:
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
            await logger.warning(f"No data found in stream {stream}")
            return None
    except Exception as e:
        await logger.error(f"Error reading from Redis stream: {stream}, Error: {e}")
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