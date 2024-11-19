import os
import subprocess
import asyncio
import json
import pexpect
from awscrt import io, mqtt, auth, http
from awsiot import iotshadow, mqtt_connection_builder
from utils.logging_setup import local_logger as logger
from utils.config import settings
from utils.validator import SystemConfig


class CertificateManager:
    def __init__(self, system_config: SystemConfig):
        self.cert_dir = settings.CERT_DIR
        self.system_config = system_config
        self.client_id = settings.AWS_CLIENT_ID
        self.ROOT_KEY = settings.DEVICE_ROOT_KEY
        self.ROOT_PEM = settings.DEVICE_ROOT_PEM
        self.DEVICE_KEY = settings.DEVICE_KEY
        self.DEVICE_CSR = settings.DEVICE_CSR
        self.DEVICE_CRT = settings.DEVICE_CRT
        self.CERTIFICATE = settings.COMBINED_CERTIFICATE

        # Certificate subject attributes
        self.CN = settings.COUNTRY_NAME
        self.SN = settings.STATE_NAME
        self.LN = settings.LOCALITY_NAME
        self.ON = settings.ORGANIZATION_NAME
        self.OU = settings.ORGANIZATIONAL_UNIT_NAME
    
    def certificate_exists(self):
        return os.path.exists(self.CERTIFICATE) and os.path.exists(self.DEVICE_KEY)
    
    def generate_private_key(self):
        if not os.path.exists(self.DEVICE_KEY):
            logger.info("Generating private key...")
            subprocess.run(
                ['openssl', 'genrsa', '-out', self.DEVICE_KEY, '2048'],
                check=True
            )
        else:
            logger.debug("Private key already exists.")
            
    def generate_csr(self):
        if not os.path.exists(self.DEVICE_CSR):
            logger.info("Generating CSR...")
            child = pexpect.spawn(f"openssl req -new -key {self.DEVICE_KEY} -out {self.DEVICE_CSR}")

            # Automate the interactive prompts with pexpect
            child.expect("Country Name .*:")
            child.sendline(self.CN)
            child.expect("State or Province Name .*:")
            child.sendline(self.SN)
            child.expect("Locality Name .*:")
            child.sendline(self.LN)
            child.expect("Organization Name .*:")
            child.sendline(self.ON)
            child.expect("Organizational Unit Name .*:")
            child.sendline(self.OU)
            child.expect("Common Name .*:")
            child.sendline(self.client_id)
            child.expect("Email Address .*:")
            child.sendline("") # Empty email address

            # Handle optional prompts
            try:
                child.expect("A challenge password .*:")
                child.sendline("")  # Empty challenge password
                child.expect("An optional company name .*:")
                child.sendline("")  # Empty optional company name
            except pexpect.exceptions.EOF:
                pass

            # Wait for process to complete
            child.expect(pexpect.EOF)
            logger.debug("CSR generated successfully.")
        else:
            logger.debug("CSR already exists.")

    def generate_device_certificate(self):
        if not os.path.exists(self.DEVICE_CRT):
            logger.info("Signing CSR to create device certificate...")
            cmd = [
                "openssl", "x509", "-req",
                "-in", self.DEVICE_CSR,
                "-CA", self.ROOT_PEM,
                "-CAkey", self.ROOT_KEY,
                "-CAcreateserial",
                "-out", self.DEVICE_CRT,
                "-days", "365",
                "-sha256"
            ]
            subprocess.run(cmd, check=True)
            logger.info("Device certificate generated successfully.")
        else:
            logger.debug("Device certificate already exists.")
    
    def combine_certificates(self):
        if not os.path.exists(self.CERTIFICATE):
            logger.info("Combing device certificate with CA certificate...")
            cmd = ["cat", self.DEVICE_CRT, self.ROOT_PEM, ">", self.CERTIFICATE]
            subprocess.run(cmd, check=True)
            logger.info("Certificates combined successfully.")
        else:
            logger.debug("Combined certificate already exists.")

    def create_certificates(self):
        """
        Orchestrates the certificate creation process
        """
        self.generate_private_key()
        self.generate_csr()
        self.generate_device_certificate()
        self.combine_certificates()



class AWSIoTClient:
    def __init__(self, cert_manager=CertificateManager, system_config=SystemConfig):
        self.cert_manager = cert_manager
        self.system_config = system_config
        self.client_id = settings.AWS_CLIENT_ID
        self.endpoint = settings.AWS_ENDPOINT
        self.ROOT_AWS_CA = settings.AWS_ROOT_CA
        self.PKEY = settings.DEVICE_KEY
        self.CERT = settings.COMBINED_CERTIFICATE
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

            self.connection = mqtt_connection_builder.mtls_from_path(
                endpoint=self.endpoint,
                cert_filepath=self.CERT,
                pri_key_filepath=self.PKEY,
                client_id=self.client_id,
                ca_filepath=self.ROOT_AWS_CA,
                clean_session=False,
                on_connection_interrupted=self.on_connection_interrupted,
                on_connection_resumed=self.on_connection_resumed,
                keep_alive_secs=30,
            )
            connect_future = self.connection.connect()
            await asyncio.wrap_future(connect_future)
            self.is_connected = True
            logger.info("Connected to AWS IoT Core.")
        
    def on_connection_interrupted(self, connection, error, **kwargs):
        logger.warning(f"Connection interrupted: {error}")

    def on_connection_resumed(self, connection, return_code, session_present, **kwargs):
        logger.info("Connection resumed.")

    async def publish(self, topic: str, payload:str, qos=mqtt.QoS.AT_LEAST_ONCE):
        """
        Publishes a messagetoa topic prefixing with the client ID
        """
        if self.is_connected:
            full_topic = f"{self.client_id}/{topic}"
            publish_future = self.mqtt_connection.publish(
                topic=full_topic,
                payload=payload,
                qos=qos
            )
            await asyncio.wrap_future(publish_future)
            logger.debug(f"Published message to topic {full_topic}")
        else:
            logger.error("Cannot publish message. MQTT connection not established.")

    async def subscribe(self, topic: str, callback, qos=mqtt.QoS.AT_LEAST_ONCE):
        """
        Subscribes to a topic prefixing with the client ID
        """
        if self.is_connected:
            full_topic = f"{self.client_id}/{topic}"
            subscribe_future, packet_id = self.mqtt_connection.subscribe(
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


aws=AWSIoTClient()
aws.connect()
aws.publish("test", "Hello World")
aws.subscribe("test", lambda x: print(x))