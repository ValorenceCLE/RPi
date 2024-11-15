import os
import subprocess
import asyncio
import json
import pexpect
from awscrt import io, mqtt, auth, http
from awsiot import iotshadow, mqtt_connection_builder
from utils.logging_setup import local_logger as logger
from utils.config import settings

class CertificateManager:
    def __init__(self):
        self.cert_dir = settings.CERT_DIR
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
    def __init__(self, cert_manager: CertificateManager):
        self.cert_manager = cert_manager
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
    
    

