import redis # type: ignore

def publish_message():
    r = redis.Redis(host='redis', port=6379)  # Use the service name as the hostname
    while True:
        message = input("Enter a message to publish: ")
        r.publish('my-channel', message)
        print(f"Published message: {message}")

if __name__ == "__main__":
    publish_message()
