from fastapi import APIRouter, HTTPException #type: ignore
from datetime import datetime, timedelta
import asyncio
from redis.asyncio import Redis #type:ignore
import os
import json

router = APIRouter()

redis = Redis.from_url(os.getenv('REDIS_URL', 'redis://redis:6379'))

# Helper function to fetch data from Redis Streams
async def fetch_data_from_stream(stream_name: str, start_time: str, end_time: str):
    try:
        response = await redis.xrange(stream_name, start_time, end_time)
        return response
    except Exception as e:
        print(f"Error fetching data from Redis: {e}")
        return []

# Helper function to aggregate data
def aggregate_data(data, interval_seconds: int):
    aggregated_data = []
    current_bucket = None
    sum_values = None
    count = 0
    
    print(f"Starting aggregation with interval: {interval_seconds} seconds")

    for item in data:
        timestamp = item[0].decode()  # Decode the timestamp
        dt = datetime.utcfromtimestamp(int(timestamp.split("-")[0]) / 1000.0)
        bucket_time = dt.replace(second=0, microsecond=0) - timedelta(seconds=dt.second % interval_seconds)

        if current_bucket is None or bucket_time != current_bucket:
            if current_bucket is not None and sum_values is not None:
                avg_values = {k: round(v / count, 1) for k, v in sum_values.items()}
                # Append `.000` milliseconds to the timestamp and include the "timestamp" key
                aggregated_data.append({
                    "timestamp": current_bucket.isoformat() + ".000",
                    **avg_values
                })
            current_bucket = bucket_time
            sum_values = {k.decode(): 0.0 for k in item[1].keys() if k.decode() != "timestamp"}
            count = 0
        
        for k, v in item[1].items():
            if k.decode() != "timestamp":  # Skip the timestamp field
                sum_values[k.decode()] += float(v.decode())
        count += 1

    if current_bucket is not None and sum_values is not None:
        avg_values = {k: round(v / count, 1) for k, v in sum_values.items()}
        # Append `.000` milliseconds to the timestamp and include the "timestamp" key
        aggregated_data.append({
            "timestamp": current_bucket.isoformat() + ".000",
            **avg_values
        })
    
    print(f"Aggregation complete. Total aggregated points: {len(aggregated_data)}")
    return aggregated_data


@router.get("/{page_name}/data/{time_frame}")
async def get_aggregated_data(page_name: str, time_frame: str):
    # Map page names to Redis streams
    stream_map = {
        "system": "system_data",
        "router": "router_data",
        "camera": "camera_data",
        "network": "cellular_data"
    }
    stream_name = stream_map.get(page_name)
    if not stream_name:
        raise HTTPException(status_code=400, detail="Invalid Page Name")
    
    # Determine time frame and start/end times
    end_time = datetime.utcnow()
    if time_frame == "15m":
        start_time = end_time - timedelta(minutes=15)
        interval_seconds = 30  # No aggregation
    elif time_frame == "30m":
        start_time = end_time - timedelta(minutes=30)
        interval_seconds = 30  # No aggregation
    elif time_frame == "1h":
        start_time = end_time - timedelta(hours=1)
        interval_seconds = 30  # No aggregation
    elif time_frame == "3h":
        start_time = end_time - timedelta(hours=3)
        interval_seconds = 60 * 2  # Aggregate every 2 minutes (120 seconds)
    elif time_frame == "6h":
        start_time = end_time - timedelta(hours=6)
        interval_seconds = 60 * 4  # Aggregate every 4 minutes (240 seconds)
    else:
        raise HTTPException(status_code=400, detail="Invalid Time Frame")
    
    start_time_str = str(int(start_time.timestamp() * 1000))
    end_time_str = str(int(end_time.timestamp() * 1000))

    print(f"Fetching data for {page_name} from {start_time_str} to {end_time_str} with time frame {time_frame}")
    
    raw_data = await fetch_data_from_stream(stream_name, start_time_str, end_time_str)
    
    if not raw_data:
        print(f"No data available for stream {stream_name}")
        return {"error": "No data available"}
    
    print(f"Fetched {len(raw_data)} entries from stream {stream_name}")

    # Aggregate data only if the interval is greater than 30 seconds
    if interval_seconds > 30:
        aggregated_data = aggregate_data(raw_data, interval_seconds)
        print(f"Returning {len(aggregated_data)} aggregated data points")
    else:
        # No aggregation needed, just format the raw data
        aggregated_data = [
            {
                "timestamp": datetime.utcfromtimestamp(int(item[0].decode().split("-")[0]) / 1000.0).isoformat(),
                **{k.decode(): round(float(v.decode()), 1) for k, v in item[1].items() if k.decode() != "timestamp"}  # Skip timestamp field
            }
            for item in raw_data
        ]
        print(f"Returning {len(aggregated_data)} raw data points")
    
    return {"data": aggregated_data}
