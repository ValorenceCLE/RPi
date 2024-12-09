import asyncio
from awsiot import mqtt5_client_builder
from awscrt import mqtt5
from utils.logging_setup import local_logger as logger
from utils.config import settings
import json

class AWSIoTClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True
        self.client = self._initialize_client()
        self.device_id = settings.AWS_CLIENT_ID
        self.TIMEOUT = 100
    
    def _initialize_client(self):
        logger.info("Initializing AWS IoT client...")
        return mqtt5_client_builder.mtls_from_path(
            endpoint=settings.AWS_ENDPOINT,
            port=8883,
            cert_filepath=settings.DEVICE_COMBINED_CRT,
            pri_key_filepath=settings.DEVICE_KEY,
            ca_filepath=settings.AWS_ROOT_CA,
            http_proxy_options=None,
            on_publish_received=self.on_publish_received,
            on_lifecycle_stopped=self.on_lifecycle_stopped,
            on_lifecycle_connection_success=self.on_lifecycle_connection_success,
            on_lifecycle_connection_failure=self.on_lifecycle_connection_failure,
            client_id=settings.AWS_CLIENT_ID,
        )

    async def start(self):
        try:
            logger.info("Starting AWS IoT client...")
            self.future_connection_success = asyncio.Future()
            self.client.start()
            await asyncio.wait_for(self.future_connection_success, timeout=self.TIMEOUT)
        except asyncio.TimeoutError:
            logger.error("Timeout while starting AWS IoT client.")
            raise
        except Exception as e:
            logger.error(f"Error starting AWS IoT client: {e}")
            raise
    
    async def stop(self):
        try:
            logger.info("Stopping AWS IoT client...")
            self.future_stopped = asyncio.Future()
            self.client.stop()
            await asyncio.wait_for(self.future_stopped, timeout=self.TIMEOUT)
        except asyncio.TimeoutError:
            logger.error("Timeout while stopping AWS IoT client.")
            raise
        except Exception as e:
            logger.error(f"Error stopping AWS IoT client: {e}")
            raise

    async def publish(self, topic, payload, source=None):
        if not isinstance(payload, dict):
            logger.error("Payload must be a dictionary.")
            return
        payload["device_id"] = self.device_id
        if source:
            payload["source"] = source
        json_payload = json.dumps(payload)
        prefixed_topic = f"{self.device_id}/{topic}"
        logger.debug(f"Publishing to topic '{prefixed_topic}' with payload: {json_payload}")
        publish_future = self.client.publish(
            mqtt5.PublishPacket(
                topic=prefixed_topic,
                payload=json_payload.encode("utf-8"),
                qos=mqtt5.QoS.AT_LEAST_ONCE,
            )
        )
        await self._wrap_future(publish_future)

    async def subscribe(self, topic, callback=None):
        try:
            logger.info(f"Subscribing to topic '{topic}'...")
            subscribe_future = self.client.subscribe(
                subscribe_packet=mqtt5.SubscribePacket(
                    subscriptions=[
                        mqtt5.Subscription(
                            topic_filter=f"{self.device_id}/{topic}",
                            qos=mqtt5.QoS.AT_LEAST_ONCE,
                        )
                    ]
                )
            )
            await self._wrap_future(subscribe_future)
            if callback:
                self.client.on_publish_received = callback
        except Exception as e:
            logger.error(f"Error subscribing to topic '{topic}': {e}")
            raise
    
    def _wrap_future(self, sdk_future):
        """
        Converts a concurrent.futures.Future into an asyncio.Future.
        """
        asyncio_future = asyncio.Future()

        def callback(_sdk_future):
            try:
                result = _sdk_future.result()
                asyncio_future.set_result(result)
            except Exception as e:
                asyncio_future.set_exception(e)

        sdk_future.add_done_callback(callback)
        return asyncio_future

    # Callbacks
    def on_publish_received(self, publish_packet_data):
        publish_packet = publish_packet_data.publish_packet
        logger.info(
            f"Received message from topic '{publish_packet.topic}': {publish_packet.payload}"
        )

    def on_lifecycle_stopped(self, lifecycle_stopped_data: mqtt5.LifecycleStoppedData):
        logger.info("MQTT connection stopped")
        self.future_stopped.set_result(lifecycle_stopped_data)

    def on_lifecycle_connection_success(
        self, lifecycle_connect_success_data: mqtt5.LifecycleConnectSuccessData
    ):
        logger.info("Lifecycle Connection Success")
        self.future_connection_success.set_result(lifecycle_connect_success_data)

    def on_lifecycle_connection_failure(
        self, lifecycle_connection_failure: mqtt5.LifecycleConnectFailureData
    ):
        logger.error(
            f"Connection failed with exception: {lifecycle_connection_failure.exception}"
        )

# Plain Functions for Easy Usage
_client_instance = None
def _get_client_instance():
    global _client_instance
    if _client_instance is None:
        _client_instance = AWSIoTClient()
    return _client_instance


async def start():
    await _get_client_instance().start()


async def stop():
    await _get_client_instance().stop()


async def publish(topic, payload, source=None):
    await _get_client_instance().publish(topic, payload, source)


async def subscribe(topic, callback=None):
    await _get_client_instance().subscribe(topic, callback)
