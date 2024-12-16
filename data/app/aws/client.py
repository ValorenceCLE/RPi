import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from awsiot import mqtt5_client_builder
from awscrt import mqtt5
from utils.logging_setup import local_logger as logger
from utils.config import settings


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
        self.executor = ThreadPoolExecutor()

    def get_mqtt_connection(self):
        return self.client

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
        """Start the MQTT client asynchronously."""
        await asyncio.get_event_loop().run_in_executor(self.executor, self._start_sync)

    def _start_sync(self):
        """Synchronous start method."""
        try:
            logger.info("Starting AWS IoT client...")
            self.client.start()
            logger.info("AWS IoT client started successfully.")
        except Exception as e:
            logger.error(f"Error starting AWS IoT client: {e}")
            raise

    async def stop(self):
        """Stop the MQTT client asynchronously."""
        await asyncio.get_event_loop().run_in_executor(self.executor, self._stop_sync)

    def _stop_sync(self):
        """Synchronous stop method."""
        try:
            logger.info("Stopping AWS IoT client...")
            self.client.stop()
            logger.info("AWS IoT client stopped successfully.")
        except Exception as e:
            logger.error(f"Error stopping AWS IoT client: {e}")
            raise

    async def publish(self, topic, payload, source=None):
        """Publish a message asynchronously."""
        await asyncio.get_event_loop().run_in_executor(
            self.executor, self._publish_sync, topic, payload, source
        )

    def _publish_sync(self, topic, payload, source=None):
        """Synchronous publish method."""
        if not isinstance(payload, dict):
            logger.error("Payload must be a dictionary.")
            return
        payload["device_id"] = self.device_id
        if source:
            payload["source"] = source
        json_payload = json.dumps(payload)
        prefixed_topic = f"{self.device_id}/{topic}"
        logger.debug(f"Publishing to topic '{prefixed_topic}' with payload: {json_payload}")
        try:
            self.client.publish(
                mqtt5.PublishPacket(
                    topic=prefixed_topic,
                    payload=json_payload.encode("utf-8"),
                    qos=mqtt5.QoS.AT_LEAST_ONCE,
                )
            )
            logger.debug("Publish operation successful.")
        except Exception as e:
            logger.error(f"Error publishing to topic '{topic}': {e}")
            raise

    async def subscribe(self, topic, callback=None):
        """Subscribe to a topic asynchronously."""
        await asyncio.get_event_loop().run_in_executor(
            self.executor, self._subscribe_sync, topic, callback
        )

    def _subscribe_sync(self, topic, callback=None):
        """Synchronous subscribe method."""
        try:
            logger.info(f"Subscribing to topic '{topic}'...")
            self.client.subscribe(
                subscribe_packet=mqtt5.SubscribePacket(
                    subscriptions=[
                        mqtt5.Subscription(
                            topic_filter=f"{self.device_id}/{topic}",
                            qos=mqtt5.QoS.AT_LEAST_ONCE,
                        )
                    ]
                )
            )
            if callback:
                self.client.on_publish_received = callback
            logger.info(f"Subscribed to topic '{topic}' successfully.")
        except Exception as e:
            logger.error(f"Error subscribing to topic '{topic}': {e}")
            raise

    # Callbacks
    def on_publish_received(self, publish_packet_data):
        publish_packet = publish_packet_data.publish_packet
        logger.info(
            f"Received message from topic '{publish_packet.topic}': {publish_packet.payload}"
        )

    def on_lifecycle_stopped(self, lifecycle_stopped_data: mqtt5.LifecycleStoppedData):
        logger.info("MQTT connection stopped")

    def on_lifecycle_connection_success(
        self, lifecycle_connect_success_data: mqtt5.LifecycleConnectSuccessData
    ):
        logger.info("Lifecycle Connection Success")

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
