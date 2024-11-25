import asyncio
import json
from awscrt import mqtt
from awsiot import mqtt_connection_builder, mqtt5_client_builder
from utils.logging_setup import local_logger as logger
from utils.config import settings
from utils.certificates import CertificateManager

class AWSIoTClient:
    _instance = None
    _lock = asyncio.Lock()

    def __init__(self):
        """
        Private constructor to prevent direct instantiation.
        Use the `get_instance` class method instead.
        """
        if AWSIoTClient._instance is not None:
            raise Exception("This class is a singleton! Use get_instance() method.")

        self.cert_manager = CertificateManager()
        self.client_id = settings.AWS_CLIENT_ID
        self.endpoint = settings.AWS_ENDPOINT
        self.ROOT_AWS_CA = settings.AWS_ROOT_CA
        self.PKEY = settings.DEVICE_KEY
        self.CERT = settings.DEVICE_COMBINED_CRT
        self.mqtt_connection = None
        self.is_connected = False
        self.connection_lock = asyncio.Lock()
        self.loop = None  # Will be set upon connection

    @classmethod
    async def get_instance(cls):
        """
        Asynchronously retrieves the Singleton instance.
        If it doesn't exist, creates it and connects to AWS IoT Core.
        """
        async with cls._lock:
            if cls._instance is None:
                cls._instance = AWSIoTClient()
                await cls._instance.connect()
            return cls._instance
        
    @classmethod
    async def close_instance(cls):
        """
        Asynchronously closes the Singleton instance.
        """
        async with cls._lock:
            if cls._instance:
                await cls._instance.disconnect()
                cls._instance = None

    async def connect(self):
        """
        Establishes the MQTT connection to AWS IoT Core.
        """
        async with self.connection_lock:
            if self.is_connected:
                logger.info("Already connected to AWS IoT Core.")
                return
            logger.info("Connecting to AWS IoT Core...")
            try:
                if not self.cert_manager.certificate_exists():
                    self.cert_manager.create_certificates()
            except Exception as e:
                logger.error(f"Failed to create certificates: {e}")
                return 

            self.loop = asyncio.get_running_loop()  # Capture the main event loop before connecting
            self.mqtt_connection = mqtt_connection_builder.mtls_from_path(
                endpoint=self.endpoint,
                cert_filepath=self.CERT,        # Path to deviceCertAndCACert.crt
                pri_key_filepath=self.PKEY,     # Path to deviceCert.key
                client_id=self.client_id,
                ca_filepath=self.ROOT_AWS_CA,   # Path to awsRootCA.pem
                clean_session=False,
                on_connection_interrupted=self.on_connection_interrupted,
                on_connection_resumed=self.on_connection_resumed
            )
            connect_future = self.mqtt_connection.connect()
            await asyncio.wrap_future(connect_future)
            self.is_connected = True
            logger.info("Connected to AWS IoT Core.")

    def on_connection_interrupted(self, connection, error, **kwargs):
        """
        Callback when the MQTT connection is interrupted.
        Schedules the reconnection coroutine using the main event loop.
        """
        logger.warning(f"Connection interrupted: {error}")
        self.is_connected = False
        if self.loop:
            asyncio.run_coroutine_threadsafe(self.handle_reconnection(), self.loop)

    def on_connection_resumed(self, connection, return_code, session_present, **kwargs):
        """
        Callback when the MQTT connection is resumed.
        """
        logger.info("Connection resumed.")
        self.is_connected = True

    async def handle_reconnection(self):
        """
        Handles reconnection attempts with exponential backoff.
        """
        backoff = 1  # Start with 1 second
        while not self.is_connected:
            try:
                logger.info("Attempting to reconnect to AWS IoT Core...")
                await self.connect()
            except Exception as e:
                logger.error(f"Failed to reconnect to AWS IoT Core: {e}")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)  # Exponential backoff up to 60 seconds

    async def callback(self, topic, payload, **kwargs):
        """
        Callback for incoming MQTT messages.
        """
        logger.info(f"Received message on topic {topic}: {payload}")

    async def publish(self, topic: str, payload: str, qos=mqtt.QoS.AT_LEAST_ONCE):
        """
        Publishes a message to the specified MQTT topic.
        """
        async with self.connection_lock:
            if self.is_connected:
                try:
                    publish_future, _ = self.mqtt_connection.publish(
                        topic=topic,
                        payload=payload,
                        qos=qos
                    )
                    await asyncio.wrap_future(publish_future)
                    logger.info(f"Published message to topic '{topic}': {payload}")
                except Exception as e:
                    logger.error(f"Failed to publish message to topic '{topic}': {e}")
            else:
                logger.warning("MQTT connection is not established. Attempting to reconnect...")
                await self.connect()
                if self.is_connected:
                    try:
                        publish_future, _ = self.mqtt_connection.publish(
                            topic=topic,
                            payload=payload,
                            qos=qos
                        )
                        await asyncio.wrap_future(publish_future)
                        logger.info(f"Published message to topic '{topic}': {payload}")
                    except Exception as e:
                        logger.error(f"Failed to publish message to topic '{topic}': {e}")
                else:
                    logger.error("Failed to reconnect to AWS IoT Core. Cannot publish message.")

    async def subscribe(self, topic: str, callback, qos=mqtt.QoS.AT_LEAST_ONCE):
        """
        Subscribes to a topic.
        """
        async with self.connection_lock:
            if self.is_connected:
                try:
                    subscribe_future, _ = self.mqtt_connection.subscribe(
                        topic=topic,
                        qos=qos,
                        callback=callback
                    )
                    await asyncio.wrap_future(subscribe_future)
                    logger.debug(f"Subscribed to topic '{topic}'")
                except Exception as e:
                    logger.error(f"Failed to subscribe to topic '{topic}': {e}")
            else:
                logger.error("Cannot subscribe to topic. MQTT connection not established.")

    async def disconnect(self):
        """
        Disconnects from AWS IoT Core gracefully.
        """
        async with self.connection_lock:
            if self.is_connected:
                try:
                    disconnect_future = self.mqtt_connection.disconnect()
                    await asyncio.wrap_future(disconnect_future)
                    self.is_connected = False
                    logger.info("Disconnected from AWS IoT Core.")
                except Exception as e:
                    logger.error(f"Failed to disconnect from AWS IoT Core: {e}")
            else:
                logger.warning("MQTT connection is not established.")

class DeviceShadowManager:
    def __init__(self, aws_client: AWSIoTClient):
        self.aws_client = aws_client
        self.client_id = aws_client.client_id
        # Define Shadow topics
        self.shadow_get_topic = f"$aws/things/{self.client_id}/shadow/get"
        self.shadow_get_accepted_topic = f"$aws/things/{self.client_id}/shadow/get/accepted"
        self.shadow_update_topic = f"$aws/things/{self.client_id}/shadow/update"
        self.shadow_update_accepted_topic = f"$aws/things/{self.client_id}/shadow/update/accepted"
        self.shadow_delta_topic = f"$aws/things/{self.client_id}/shadow/update/delta"
        # Initialize shadow client state
        self.reported_state = {}
        self.desired_state = {}
        self.lock = asyncio.Lock()
    
    async def initialize(self):
        """
        Initializes the device shadow by subscribing to necessary topics and fetching the current shadow.
        """
        await self.aws_client.subscribe(self.shadow_get_accepted_topic, self.on_shadow_get_accepted)
        await self.aws_client.subscribe(self.shadow_update_accepted_topic, self.on_shadow_update_accepted)
        await self.aws_client.subscribe(self.shadow_delta_topic, self.on_shadow_delta)

        # Request the current shadow state
        await self.get_shadow()

    async def get_shadow(self):
        """
        Publishes an empty message to the shadow get topic to request the current shadow.
        """
        logger.debug("Requesting current device shadow...")
        await self.aws_client.publish(self.shadow_get_topic, "")

    async def on_shadow_get_accepted(self, topic, payload, **kwargs):
        """
        Callback for when the shadow get request is accepted.
        """
        shadow = json.loads(payload)
        async with self.lock:
            self.reported_state = shadow.get("state", {}).get("reported", {})
            self.desired_state = shadow.get("state", {}).get("desired", {})
        logger.info(f"Shadow get accepted. Reported state: {self.reported_state}, Desired state: {self.desired_state}")

        # Handle any pending updates
        if self.desired_state:
            await self.handle_desired_state(self.desired_state)
    
    async def update_reported_state(self, reported_state: dict):
        """
        Updates the reported state in the device shadow.
        """
        payload = json.dumps({"state": {"reported": reported_state}})
        await self.aws_client.publish(self.shadow_update_topic, payload)
        logger.debug(f"Reported state updated: {reported_state}")
    
    async def on_shadow_update_accepted(self, topic, payload, **kwargs):
        """
        Callback for when the shadow update is accepted.
        """
        shadow = json.loads(payload)
        async with self.lock:
            self.reported_state = shadow.get("state", {}).get("reported", {})
            # Clear desired state if its been fullfilled
            if 'desired' in shadow.get("state", {}):
                self.desired_state = shadow.get("state", {}).get("desired", {})
        logger.info(f"Shadow update accepted. Reported state: {self.reported_state}, Desired state: {self.desired_state}")

    async def on_shadow_delta(self, topic, payload, **kwargs):
        """
        Callback for when the shadow delta is received.
        """
        delta = json.loads(payload)
        desired_state = delta.get("state", {})
        logger.info(f"Shadow delta received. Desired state: {desired_state}")
        await self.handle_desired_state(desired_state)
    
    async def handle_desired_state(self, desired_state: dict):
        """
        Handles the desired state in the device shadow.
        """
        async with self.lock:
           pass

