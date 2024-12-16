import json
import asyncio
from utils.validator import validate_config, Schedule
from utils.logging_setup import local_logger as logger
from core.relay_monitor import RelayMonitor
from core.processor import RelayProcessor, GeneralProcessor
from core.cell import CellularData
from core.net import NetworkData
from core.env import EnvironmentalData
from core.relay_manager import RelayManager
from aws.shadow import ShadowManager
from aws.certificates import CertificateManager
from aws.client import start as aws_start, stop as aws_stop, AWSIoTClient
from aws.jobs import IoTJobManager

async def setup_certificates():
    """
    Check if device certificates exist; if not, generate them.
    """
    logger.info("Checking device certificates...")
    cert_manager = CertificateManager()
    if not cert_manager.certificate_exists():
        logger.info("No device certificates found. Generating new certificates...")
        try:
            cert_manager.create_certificates()
            logger.info("Certificates generated successfully.")
        except Exception as e:
            logger.error(f"Failed to generate certificates: {e}")
    else:
        logger.debug("Device certificates already exist.")

async def initialize_relay_tasks(config, relay_manager):
    """
    Initialize tasks for relay monitoring and processing based on the provided configuration.

    Args:
        config: The validated configuration object.
        relay_manager (RelayManager): The initialized RelayManager instance.

    Returns:
        A list of asyncio tasks for relay monitoring and processing.
    """
    tasks = []
    for relay_id, relay_config in config.relays.items():
        should_monitor = relay_config.monitor
        has_schedule = isinstance(relay_config.schedule, Schedule) and relay_config.schedule.enabled

        if should_monitor or has_schedule:
            monitor = RelayMonitor(relay_id, relay_config, relay_manager=relay_manager)
            monitor_task = asyncio.create_task(monitor.start())
            tasks.append(monitor_task)

            processor = RelayProcessor(relay_id)
            processor_task = asyncio.create_task(processor.run())
            tasks.append(processor_task)
            logger.debug(f"Relay {relay_id}: monitoring and processing tasks created.")
        else:
            logger.info(f"No monitoring or scheduling configured for relay {relay_id}.")
    return tasks

async def initialize_general_tasks():
    """
    Initialize tasks for general data collection and processing (cellular, network).

    Returns:
        A list of asyncio tasks for general metric collection and processing.
    """
    tasks = []

    # Network Data Collection
    net = NetworkData()
    net_task = asyncio.create_task(net.run())
    tasks.append(net_task)
    logger.debug("Network data collection task created.")

    # Cellular Data Collection
    cell = CellularData()
    cell_task = asyncio.create_task(cell.run())
    tasks.append(cell_task)
    logger.debug("Cellular data collection task created.")

    # Environmental Data Collection
    env = EnvironmentalData()
    env_task = asyncio.create_task(env.run())
    tasks.append(env_task)
    logger.debug("Environmental data collection task created.")

    # Streams for the GeneralProcessor
    streams = ['network', 'cellular', 'environmental']
    general_processor = GeneralProcessor(streams=streams)
    general_processor_task = asyncio.create_task(general_processor.run())
    tasks.append(general_processor_task)
    logger.debug("General processor task created for streams: network, cellular, environmental.")

    return tasks

async def initialize_job_manager(mqtt_client):
    """
    Initialize the IoT Job Manager with existing MQTT connection.
    """
    try:
        job_manager = IoTJobManager()
        await job_manager.initialize(mqtt_client)
        logger.info("IoT Job Manager initialized successfully")
        return job_manager
    except Exception as e:
        logger.error(f"Failed to initialize IoT Job Manager: {e}")
        raise

async def main():
    """
    Main entry point for the application.
    """
    tasks = []
    job_manager = None
    
    try:
        logger.info("Application started.")
        await setup_certificates()

        logger.info("Validating configuration...")
        config = validate_config()

        # Create and initialize RelayManager once
        relay_manager = RelayManager(config.relays)
        await relay_manager.init()

        logger.info("Starting AWS IoT client...")
        await aws_start()
        mqtt_client = AWSIoTClient().get_mqtt_connection()
        
        # Initialize Shadow Manager
        shadow_manager = ShadowManager(mqtt_client)
        with open('/utils/json/shadow.json', 'r') as f:
            initial_state = json.load(f)
        await shadow_manager.update_shadow(initial_state)

        # Initialize Job Manager with existing MQTT connection
        logger.info("Initializing IoT Job Manager...")
        job_manager = await initialize_job_manager(mqtt_client)
        
        # Initialize all tasks
        relay_tasks = await initialize_relay_tasks(config, relay_manager)
        general_tasks = await initialize_general_tasks()
        
        # Combine all tasks
        tasks.extend(relay_tasks)
        tasks.extend(general_tasks)

        if not tasks:
            logger.warning("No tasks have been created. Check your configuration.")
        else:
            logger.info("All tasks initialized. Running indefinitely...")
            await asyncio.gather(*tasks)

    except asyncio.CancelledError:
        logger.info("Tasks have been cancelled.")
    except Exception as e:
        logger.error(f"An error occurred in main: {e}", exc_info=True)
    finally:
        # Cleanup
        if tasks:
            for task in tasks:
                if not task.done():
                    task.cancel()
            # Wait for tasks to cancel
            await asyncio.gather(*tasks, return_exceptions=True)
        
        if job_manager:
            await job_manager.cleanup()
        
        await aws_stop()
        logger.info("Application shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user.")
    except Exception as e:
        logger.error(f"Application crashed: {e}", exc_info=True)
