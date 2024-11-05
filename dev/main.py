import asyncio
from app.validator import load_and_validate_config, Schedule
from app.relay_monitor import RelayMonitor
import logging

logger = logging.getLogger(__name__)

async def main():
    config = load_and_validate_config()
    tasks = []
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
    asyncio.run(main())