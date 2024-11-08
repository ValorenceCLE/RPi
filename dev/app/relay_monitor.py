import asyncio
from typing import Dict
from app.validator import RelayConfig
from app.rules_engine import RulesEngine
from app.schedule_engine import ScheduleEngine
from app.utils.logging_setup import local_logger as logger
from app.utils.logging_setup import central_logger as syslog

# Import the sensor libraries
import board
import adafruit_ina260

class RelayMonitor:
    """
    A class to monitor and manage a relay(s) based on the configuration provided in the config file.
    
    Attributes:
        relay_id (str): The relay identifier, e.g: 'relay1'
        config (RelayConfig): The relay configuration object
        pin (int): The pin number for the relay(s) (immutable, each relay has a unique/defined pin)
        address (int): The I2C address for the sensor (immutable, each relay has a unique/defined address)
        boot_power (bool): Should the relay(s) be powered on boot? (true/false)
        monitor (bool): Should the relay(s) be monitored? (true/false)
        schedule (Schedule): The schedule for the relay(s) (if any)
        rules (Dict[str, Rule]) see config file to see the expected format: The rules defined for the relay(s) (if any)
        collection_interval (int): The data collection interval in seconds
        rules_engine (RulesEngine): The rules engine instance for rule evaluation, dynamically initialized and managed for each relay(s)
        schedule_engine (ScheduleEngine): The schedule engine instance for schedule management, dynamically initialized and managed for each relay(s)
        state (bool): The current state of the relay(s)
        i2c (board.I2C): The I2C bus instance for the sensor
        sensor (adafruit_ina260.INA260): The sensor instance for the relay(s)
    """
    def __init__(self, relay_id: str, relay_config: RelayConfig):
        """
        Initializes the RelayMonitor with the given relay ID and configuration.

        Args:
            relay_id (str): The identifier for the relay.
            relay_config (RelayConfig): The configuration for the relay.
        """
        self.relay_id = relay_id # Use relay identifier, e.g: 'relay1'
        self.config = relay_config
        self.name = relay_config.name
        self.pin = relay_config.pin
        self.address = int(relay_config.address, 16)
        self.boot_power = relay_config.boot_power
        self.monitor = relay_config.monitor
        self.schedule = relay_config.schedule
        self.rules = relay_config.rules
        self.collection_interval = 30
        self.rules_engine = RulesEngine(self.relay_id, self.rules)
        self.schedule_engine = ScheduleEngine(self.relay_id, self.schedule)
        self.state = self.boot_power
        self.i2c = None
        self.sensor = None
    
    async def start(self):
        tasks = []
        if self.schedule_engine.is_enabled():
            tasks.append(self.manage_schedule())
        else:
            logger.debug(f"Schedule disabled for {self.relay_id}")
        if self.monitor:
            try:
                self.i2c = board.I2C()
                self.sensor = adafruit_ina260.INA260(self.i2c, address=self.address)
                tasks.append(self.collect_data_loop())
            except ValueError as e:
                logger.error(f"Error initializing sensor for relay {self.relay_id}: {e}")
                self.monitor = False # Disable monitoring if sensor initialization fails
        else:
            logger.debug(f"Monitoring disabled for {self.relay_id}")
        if tasks:
            await asyncio.gather(*tasks)
        else:
            logger.warning(f"No tasks running for relay {self.relay_id}")
    
    async def manage_schedule(self):
        """
        Manages the relay schedule by checking the desired state from the schedule engine
        and updating the relay state if necessary.
        """
        while True:
            try:
                new_state = self.schedule_engine.get_desired_state()
                if new_state != self.state:
                    await self.set_relay_state(new_state)
            except Exception as e:
                logger.error(f"Error managing schedule for relay {self.relay_id}: {e}")
            await asyncio.sleep(60) # Check every minute
    
    async def set_relay_state(self, state: bool):
        self.state = state
        logger.info(f"Relay {self.relay_id} state set to {state}")
    
    async def collect_data_loop(self):
        """
        Collects data from the sensor in a loop and evaluates rules based on the collected data.
        """
        while True:
            try:
                data = await self.collect_data()
                await self.rules_engine.evaluate_rules(data)
            except Exception as e:
                logger.error(f"Error collecting data for relay {self.relay_id}: {e}")
            await asyncio.sleep(self.collection_interval)
    
    async def collect_data(self) -> Dict[str, float]:
        """
        Collects voltage, power, and current data from the sensor.

        Returns:
            Dict[str, float]: A dictionary containing the collected data.
        """
        volts = await asyncio.to_thread(lambda: round(self.sensor.voltage, 2))
        watts = await asyncio.to_thread(lambda: round(self.sensor.power / 1000, 2))
        amps = await asyncio.to_thread(lambda: round(self.sensor.current / 1000, 2))
        syslog.info(f"{self.name} data collected: Volts={volts}, Watts={watts}, Amps={amps}")
        return {"relay": self.relay_id, "volts": volts, "amps": amps, "watts": watts}