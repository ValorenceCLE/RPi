import asyncio
from utils.validator import validate_config, Schedule
from utils.logging_setup import local_logger as logger
from utils.logging_setup import central_logger as syslog
from utils.certificates import CertificateManager
from core.relay_monitor import RelayMonitor
from core.processor import RelayProcessor, GeneralProcessor
from core.cell import CellularMetrics
from core.net import NetworkPing

# io.init_logging(getattr(io.LogLevel, 'Debug'), 'stderr.log')

async def main():
    logger.info("Application started")
    logger.info("Checking device certificates...")
    if not CertificateManager().certificate_exists():
        logger.info("Generating device certificates...")
        try:
            CertificateManager().create_certificates()
            logger.info("Certificates generated successfully.")
        except Exception as e:
            logger.error(f"Failed to generate certificates: {e}")

    config = validate_config()
    tasks = []
    
    # Initialize collection scripts for the relays
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

    # Initialize collection scripts for other metrics
    net = NetworkPing()
    net_task = asyncio.create_task(net.run())
    tasks.append(net_task)
    cell = CellularMetrics()
    cell_task = asyncio.create_task(cell.run())
    tasks.append(cell_task)
    streams = ['network', 'cellular']
    general_processor = GeneralProcessor(streams)
    general_processor_task = asyncio.create_task(general_processor.run())
    tasks.append(general_processor_task)

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