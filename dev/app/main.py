import asyncio
from awscrt import io
from utils.validator import validate_config, Schedule
from core.relay_monitor import RelayMonitor
from utils.logging_setup import local_logger as logger
from utils.logging_setup import central_logger as syslog
from core.aws import AWSIoTClient
from core.processor import RelayProcessor, GeneralProcessor

# io.init_logging(getattr(io.LogLevel, 'Debug'), 'stderr.log')

async def main():
    config = validate_config()
    tasks = []

    # Initialize the AWS IoT client
    aws_client = AWSIoTClient()
    try:
        await aws_client.connect()
        logger.info("Connected to AWS IoT Core.")

        # Publish a test message
        await aws_client.publish("test/topic", "Hello from relay controller")
        logger.info("Test message published.")
    except Exception as e:
        logger.error(f"Failed to connect or publish: {e}")
        return
    
    for relay_id, relay_config in config.relays.items():
        # Decide whether to create a RelayMonitor instance based on monitoring or scheduling
        should_monitor = relay_config.monitor
        has_schedule = isinstance(relay_config.schedule, Schedule) and relay_config.schedule.enabled
        if should_monitor or has_schedule:
            monitor = RelayMonitor(relay_id, relay_config)
            monitor_task = asyncio.create_task(monitor.start())
            tasks.append(monitor_task) # Collect data/monitor the relays

            processor = RelayProcessor(relay_id)
            processor_task = asyncio.create_task(processor.run())
            tasks.append(processor_task) # Save/process data from monitoring the relays to InfluxDB
        else:
            logger.info(f"No monitoring or scheduling configured for {relay_id}.")

    if tasks:
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            logger.info("Tasks have been cancelled.")
    else:
        logger.warning("No relays are configured for monitoring or scheduling.")
        
if __name__ == "__main__":
    logger.info("Starting the relay controller.")
    syslog.info("Starting the relay controller.")
    asyncio.run(main())