import asyncio
import json
from awscrt import mqtt5
from awsiot import mqtt_connection_builder
from utils.logging_setup import local_logger as logger
from utils.config import settings
from utils.certificates import CertificateManager

class AWSIoTClient:
    # Review the AWS IoT SDK Source code to see how they do it to make sure we are doing it the right way
    # And following the best practices.
    def __init__(self):
        self.cert_manager = CertificateManager()
        self.client_id = settings.AWS_CLIENT_ID
        self.endpoint = settings.AWS_ENDPOINT
        self.ROOT_AWS_CA = settings.AWS_ROOT_CA
        self.PKEY = settings.DEVICE_KEY
        self.CERT = settings.DEVICE_COMBINED_CRT
        self.mqtt_connection = None
        self.is_connected = False
        self.lock = asyncio.Lock()
    
    async def connect(self):
        async with self.lock:
            if self.is_connected:
                return
            logger.info("Connecting to AWS IoT Core...")
            try:
                if not self.cert_manager.certificate_exists():
                    self.cert_manager.create_certificates()
            except Exception as e:
                logger.error(f"Failed to create certificates: {e}")
                return 

            self.mqtt_connection = mqtt_connection_builder.mtls_from_path(
                endpoint=self.endpoint,
                cert_filepath=self.CERT,        # Path to deviceCertAndCACert.crt
                pri_key_filepath=self.PKEY,     # Path to deviceCert.key
                client_id=self.client_id,
                ca_filepath=self.ROOT_AWS_CA,   # Path to awsRootCA.pem
                clean_session=False,
                on_connection_interrupted=self.on_connection_interrupted,
                on_connection_resumed=self.on_connection_resumed,
                keep_alive_secs=30,
            )
            connect_future = self.mqtt_connection.connect()
            await asyncio.wrap_future(connect_future)
            self.is_connected = True
            logger.info("Connected to AWS IoT Core.")
        
    def on_connection_interrupted(self, connection, error, **kwargs):
        logger.warning(f"Connection interrupted: {error}")

    def on_connection_resumed(self, connection, return_code, session_present, **kwargs):
        logger.info("Connection resumed.")

    async def publish(self, topic: str, payload:str, qos=mqtt5.QoS.AT_LEAST_ONCE):
        if self.is_connected:
            full_topic = f"{self.client_id}/{topic}"
            publish_future, _ = self.mqtt_connection.publish(
                topic=full_topic,
                payload=payload,
                qos=qos
            )
            await asyncio.wrap_future(publish_future)
            logger.debug(f"Published message to topic {full_topic}")
        else:
            logger.error("Cannot publish message. MQTT connection not established.")


    async def subscribe(self, topic: str, callback, qos=mqtt5.QoS.AT_LEAST_ONCE):
        """
        Subscribes to a topic prefixing with the client ID
        """
        if self.is_connected:
            full_topic = f"{self.client_id}/{topic}"
            subscribe_future, _ = self.mqtt_connection.subscribe(
                topic=full_topic,
                qos=qos,
                callback=callback
            )
            await asyncio.wrap_future(subscribe_future)
            logger.debug(f"Subscribed to topic {full_topic}")
        else:
            logger.error("Cannot subscribe to topic. MQTT connection not established.")

    async def disconnect(self):
        """
        Disconnects from AWS IoT Core
        """
        if self.is_connected:
            disconnect_future = self.mqtt_connection.disconnect()
            await asyncio.wrap_future(disconnect_future)
            self.is_connected = False
            logger.info("Disconnected from AWS IoT Core.")
        else:
            logger.error("Cannot disconnect. MQTT connection not established.")

    async def callback(self, topic, payload, **kwargs):
        logger.info(f"Received message on topic {topic}: {payload}")

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

