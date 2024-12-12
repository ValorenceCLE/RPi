# main.py
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
from aws.client import start as aws_start, stop as aws_stop

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

async def main():
    """
    Main entry point for the application.
    """
    logger.info("Application started.")
    await setup_certificates()

    logger.info("Validating configuration...")
    config = validate_config()

    # Create and initialize RelayManager once, passing config's relays
    relay_manager = RelayManager(config.relays)
    await relay_manager.init()

    # Start the AWS IoT client
    logger.info("Starting AWS IoT client...")
    await aws_start()
    shadow_manager = ShadowManager()
    with open('/utils/json/shadow.json', 'r') as f:
        initial_state = json.load(f)
        print(initial_state)
    await shadow_manager.update_shadow(initial_state)

    # Initialize tasks based on the validated configuration
    relay_tasks = await initialize_relay_tasks(config, relay_manager)
    general_tasks = await initialize_general_tasks()

    all_tasks = relay_tasks + general_tasks

    if not all_tasks:
        logger.warning("No tasks have been created. Check your configuration.")
    else:
        logger.info("All tasks initialized. Running indefinitely...")
        try:
            await asyncio.gather(*all_tasks)
        except asyncio.CancelledError:
            logger.info("Tasks have been cancelled.")
        except Exception as e:
            logger.error(f"An error occurred in tasks: {e}", exc_info=True)

    # Keep the application running to listen for shadow events
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        # Stop the AWSIoTClient
        await aws_stop()

if __name__ == "__main__":
    logger.info("Starting the relay controller...")
    asyncio.run(main())
