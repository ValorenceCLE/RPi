import os
import asyncio
from redis.asyncio import Redis

async def listen_to_streams():
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis = Redis.from_url(redis_url)

    streams = {
        'cellular_data': '0-0',  # Start from the beginning of the 'cellular_data' stream
        'network_data': '0-0'    # Start from the beginning of the 'network_data' stream
    }

    while True:
        try:
            # Use xread to read from multiple streams
            response = await redis.xread(streams, block=0)
            if response:
                for stream, messages in response:
                    for message_id, message in messages:
                        print(f"Stream: {stream.decode('utf-8')}")
                        print(f"Message ID: {message_id}")
                        for key, value in message.items():
                            print(f"{key.decode('utf-8')}: {value.decode('utf-8')}")
                        # Update the last ID for the processed stream
                        streams[stream.decode('utf-8')] = message_id
        except Exception as e:
            print(f"Error reading from streams: {e}")
            await asyncio.sleep(1)  # Wait for a bit before retrying

if __name__ == "__main__":
    asyncio.run(listen_to_streams())
