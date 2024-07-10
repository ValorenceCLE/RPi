import redis

def subscribe():
    r = redis.Redis(host='redis', port=6379)  # Use the service name as the hostname
    p = r.pubsub()
    p.subscribe('my-channel')
    
    print('Subscribed to my-channel')
    
    for message in p.listen():
        if message['type'] == 'message':
            print(f"Received message: {message['data'].decode('utf-8')}")

if __name__ == "__main__":
    subscribe()
