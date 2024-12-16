import json
import time
import os
import asyncio
import boto3
import aiohttp
from awsiot import iotjobs
from awscrt import mqtt5
from awsiot.iotjobs import (
    JobExecutionsChangedSubscriptionRequest,
    StartNextPendingJobExecutionSubscriptionRequest,
    UpdateJobExecutionSubscriptionRequest,
    DescribeJobExecutionSubscriptionRequest,
    DescribeJobExecutionRequest,
    UpdateJobExecutionRequest,
    JobStatus,
)
from utils.config import settings
from utils.logging_setup import local_logger as logger
from aws.client import _get_client_instance


class IoTJobManager:
    def __init__(self):
        self.mqtt_connection = None
        self.jobs_client = None
        self.thing_name = settings.AWS_CLIENT_ID
        self.session = boto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self.s3_client = self.session.client('s3')
        self._job_semaphore = asyncio.Semaphore(5)
        self.http_session = None

    async def initialize(self, mqtt_connection=None):
        """Initialize async components."""
        self.http_session = aiohttp.ClientSession()
        if mqtt_connection:
            self.mqtt_connection = mqtt_connection
            self.jobs_client = iotjobs.IotJobsClient(self.mqtt_connection)
            await self.subscribe_to_job_notifications()
        else:
            await self.connect()

    async def connect(self):
        """Establishes a connection to AWS IoT Core using the MQTT5 client."""
        try:
            client_instance = _get_client_instance()
            if not client_instance:
                raise ValueError("AWS IoT Client instance not initialized")
                
            self.mqtt_connection = client_instance.get_mqtt_connection()
            if not self.mqtt_connection:
                raise ValueError("MQTT connection not available")
                
            self.jobs_client = iotjobs.IotJobsClient(self.mqtt_connection)
            logger.info("Connected to AWS IoT Core for jobs.")
        except Exception as e:
            logger.error(f"Failed to connect to AWS IoT Core: {e}")
            raise

    async def cleanup(self):
        """Cleanup async resources."""
        if self.http_session:
            await self.http_session.close()
        # Don't stop the MQTT connection as it's shared
        self.mqtt_connection = None
        self.jobs_client = None

    async def connect(self):
        """Establishes a connection to AWS IoT Core using the MQTT5 client."""
        try:
            self.mqtt_connection = _get_client_instance().get_mqtt_connection()
            await self.mqtt_connection.start()
            logger.info("Started MQTT5 connection to AWS IoT Core.")
            self.jobs_client = iotjobs.IotJobsClient(self.mqtt_connection)
        except Exception as e:
            logger.error(f"Failed to connect to AWS IoT Core: {e}")
            raise

    async def subscribe_to_job_notifications(self):
        """Subscribes to job-related MQTT topics."""
        try:
            # Subscribe to job executions changes
            request = JobExecutionsChangedSubscriptionRequest(thing_name=self.thing_name)
            self.jobs_client.subscribe_to_job_executions_changed_events(
                request, qos=1, callback=self.on_job_executions_changed
            )

            # Subscribe to other job-related topics
            await self._subscribe_to_job_topics()
            
            logger.info("Successfully subscribed to all job notifications")
        except Exception as e:
            logger.error(f"Failed to subscribe to job notifications: {e}")
            raise

    async def _subscribe_to_job_topics(self):
        """Helper method to subscribe to various job-related topics."""
        try:
            # Start next job subscriptions
            start_request = StartNextPendingJobExecutionSubscriptionRequest(thing_name=self.thing_name)
            self.jobs_client.subscribe_to_start_next_pending_job_execution_accepted(
                start_request, qos=1, callback=self.on_start_next_job_accepted
            )
            self.jobs_client.subscribe_to_start_next_pending_job_execution_rejected(
                start_request, qos=1, callback=self.on_start_next_job_rejected
            )

            # Update job subscriptions
            update_request = UpdateJobExecutionSubscriptionRequest(
                thing_name=self.thing_name, job_id="+"
            )
            self.jobs_client.subscribe_to_update_job_execution_accepted(
                update_request, qos=1, callback=self.on_update_job_accepted
            )
            self.jobs_client.subscribe_to_update_job_execution_rejected(
                update_request, qos=1, callback=self.on_update_job_rejected
            )

            # Describe job subscriptions
            describe_request = DescribeJobExecutionSubscriptionRequest(
                thing_name=self.thing_name, job_id="+"
            )
            self.jobs_client.subscribe_to_describe_job_execution_accepted(
                describe_request, qos=1, callback=self.on_describe_job_accepted
            )
            self.jobs_client.subscribe_to_describe_job_execution_rejected(
                describe_request, qos=1, callback=self.on_describe_job_rejected
            )

        except Exception as e:
            logger.error(f"Failed to subscribe to job topics: {e}")
            raise
        # Add callback methods
    def on_job_executions_changed(self, event):
        """Callback when job executions change."""
        logger.info(f"✓ Received job notification: {event}")
        
        # Check if there are any pending jobs
        if hasattr(event, 'jobs') and event.jobs:
            logger.info(f"Number of jobs received: {len(event.jobs)}")
            for job in event.jobs:
                logger.info(f"Job ID: {job.job_id}, Status: {job.status}")
        
        # Start the next pending job execution
        self.start_next_pending_job()

    def on_start_next_job_accepted(self, response):
        """Callback for accepted start next job."""
        logger.info(f"Start next job accepted: {response}")

    def on_start_next_job_rejected(self, error):
        """Callback for rejected start next job."""
        logger.error(f"Start next job rejected: {error}")

    def on_update_job_accepted(self, response):
        """Callback for accepted job update."""
        logger.info(f"Job update accepted: {response}")

    def on_update_job_rejected(self, error):
        """Callback for rejected job update."""
        logger.error(f"Job update rejected: {error}")

    def on_describe_job_accepted(self, response):
        """Callback for accepted job description."""
        logger.info(f"Job description accepted: {response}")

    def on_describe_job_rejected(self, error):
        """Callback for rejected job description."""
        logger.error(f"Job description rejected: {error}")

    async def on_job_executions_changed(self, event):
        """Async callback when job executions change."""
        logger.info(f"Job executions changed: {event}")
        asyncio.create_task(self.start_next_pending_job())

    async def start_next_pending_job(self):
        """Starts the next pending job execution."""
        try:
            request = {
                "thingName": self.thing_name,
                "clientToken": f"{self.thing_name}-{int(time.time())}"
            }
            self.jobs_client.publish_start_next_pending_job_execution(
                request, qos=mqtt5.QoS.AT_LEAST_ONCE
            )
            logger.info("Published request to start next pending job")
        except Exception as e:
            logger.error(f"Failed to start next pending job: {e}")

    async def process_job(self, job_document, job_id):
        """Process a job asynchronously."""
        async with self._job_semaphore:
            try:
                operation = job_document.get('operation')
                if not operation:
                    raise ValueError("Job document missing 'operation' field")

                handlers = {
                    'config_update': self.handle_config_update,
                    'file_download': self.handle_file_download,
                    'reboot': self.handle_reboot
                }

                handler = handlers.get(operation)
                if not handler:
                    raise ValueError(f"Unsupported operation: {operation}")

                success = await handler(job_document)
                
                if success:
                    await self.update_job_status(
                        job_id, 
                        JobStatus.SUCCEEDED,
                        {"completion_time": time.strftime("%Y-%m-%d %H:%M:%S")}
                    )
                else:
                    raise Exception(f"Operation {operation} failed")

            except Exception as e:
                logger.error(f"Job processing failed: {e}")
                await self.update_job_status(
                    job_id,
                    JobStatus.FAILED,
                    {"error": str(e), "failure_time": time.strftime("%Y-%m-%d %H:%M:%S")}
                )

    async def update_job_status(self, job_id, status, status_details):
        """Update job execution status asynchronously."""
        try:
            request = UpdateJobExecutionRequest(
                thing_name=self.thing_name,
                job_id=job_id,
                status=status,
                status_details=status_details
            )
            await self.jobs_client.publish_update_job_execution(request)
        except Exception as e:
            logger.error(f"Failed to update job status: {e}")

    # Add your handler methods here with async/await
    async def handle_file_download(self, job_document):
        """Async handler for file download operation."""
        try:
            if 'url' not in job_document:
                raise ValueError("File download missing 'url' parameter")

            url = job_document['url']
            destination = job_document.get('destination', '/tmp')
            filename = job_document.get('filename', 'downloaded_file')
            
            os.makedirs(destination, exist_ok=True)
            full_path = os.path.join(destination, filename)

            if 's3.amazonaws.com' in url:
                # Parse S3 URL and download
                parsed_url = url.replace('https://', '').split('/')
                bucket = parsed_url[0].split('.')[0]
                key = '/'.join(parsed_url[1:])
                
                # Use aioboto3 for async S3 operations if needed
                await asyncio.to_thread(
                    self.s3_client.download_file,
                    bucket, key, full_path
                )
            else:
                async with self.http_session.get(url) as response:
                    response.raise_for_status()
                    with open(full_path, 'wb') as f:
                        while True:
                            chunk = await response.content.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)

            logger.info(f"✓ File downloaded successfully to {full_path}")
            return True

        except Exception as e:
            logger.error(f"File download failed: {e}")
            return False

    async def handle_reboot(self, job_document):
        """Async handler for reboot operation."""
        try:
            logger.info("Executing reboot operation...")
            
            # Get optional parameters
            delay = job_document.get('delay', 0)  # Delay in seconds before reboot
            force = job_document.get('force', False)  # Force reboot without checks
            
            if delay > 0:
                logger.info(f"Waiting {delay} seconds before reboot...")
                await asyncio.sleep(delay)
            
            # Perform pre-reboot checks if not forced
            if not force:
                # Check if any critical processes are running
                if not await self._is_safe_to_reboot():
                    raise ValueError("Unsafe to reboot - critical processes running")
            
            # Perform cleanup before reboot
            await self._prepare_for_reboot()
            
            logger.info("Initiating system reboot...")
            # Schedule the actual reboot command
            asyncio.create_task(self._execute_command('sudo reboot'))
            
            logger.info("✓ Reboot command initiated")
            return True
            
        except Exception as e:
            logger.error(f"Reboot operation failed: {e}")
            return False

    async def _is_safe_to_reboot(self):
        """Check if it's safe to reboot the system."""
        try:
            # Add your safety checks here
            # For example, check if any critical processes are running
            await asyncio.sleep(1)  # Simulate checking
            return True
        except Exception as e:
            logger.error(f"Reboot safety check failed: {e}")
            return False

    async def _prepare_for_reboot(self):
        """Prepare system for reboot."""
        try:
            # Add cleanup tasks here
            # For example: close connections, save state, etc.
            await asyncio.sleep(1)  # Simulate preparation
        except Exception as e:
            logger.error(f"Reboot preparation failed: {e}")
            raise

    async def _execute_command(self, command):
        """Execute a system command asynchronously."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                raise RuntimeError(f"Command failed: {stderr.decode()}")
            return stdout.decode()
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise
