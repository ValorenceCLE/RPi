import asyncio
from utils.validator import validate_config, Schedule
from core.relay_monitor import RelayMonitor
from utils.logging_setup import local_logger as logger
from utils.logging_setup import central_logger as syslog
from core.aws import AWSIoTClient
async def main():
    config = validate_config()
    tasks = []
    aws=AWSIoTClient()
    await aws.connect()
    await aws.publish("test", "Hello from relay controller")

    for relay_id, relay_config in config.relays.items():
        # Decide whether to create a RelayMonitor instance based on monitoring or scheduling
        should_monitor = relay_config.monitor
        has_schedule = isinstance(relay_config.schedule, Schedule) and relay_config.schedule.enabled
        if should_monitor or has_schedule:
            monitor = RelayMonitor(relay_id, relay_config)
            task = asyncio.create_task(monitor.start())
            tasks.append(task)
        else:
            logger.info(f"No monitoring or scheduling configured for {relay_id}.")

    if tasks:
        await asyncio.gather(*tasks)
    else:
        logger.warning("No relays are configured for monitoring or scheduling.")
if __name__ == "__main__":
    logger.info("Starting the relay controller.")
    syslog.info("Starting the relay controller.")
    asyncio.run(main())