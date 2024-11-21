import asyncio
from typing import Dict
from utils.validator import RelayConfig
from core.rules_engine import RulesEngine
from core.schedule_engine import ScheduleEngine
from utils.logging_setup import local_logger as logger
from utils.logging_setup import central_logger as syslog
from utils.singleton import RedisClient
import board
import adafruit_ina260

class RelayMonitor:
    def __init__(self, relay_id: str, relay_config: RelayConfig):
        """
        Initializes the RelayMonitor with the given relay ID and configuration.

        This init needs to be cleaned up and refactored.

        Args:
            relay_id (str): The identifier for the relay.
            relay_config (RelayConfig): The configuration for the relay.
        """
        self.relay_id = relay_id # relay_id (str): The relay identifier, e.g: 'relay1'
        self.config = relay_config # config (RelayConfig): The relay configuration object
        self.name = relay_config.name # name (str): The name of the relay, e.g: 'Router, Aux1...'
        self.pin = relay_config.pin # pin (int): The pin number for the relay(s) (immutable, each relay has a unique/defined pin)
        self.address = int(relay_config.address, 16) #  address (int): The I2C address for the sensor (immutable, each relay has a unique/defined address)
        self.boot_power = relay_config.boot_power # boot_power (bool): Should the relay(s) be powered on boot? (true/false). Maybe remove since schedule can handle this
        self.monitor = relay_config.monitor # monitor (bool): Should the relay(s) be monitored i.e collect data? (true/false)
        self.schedule = relay_config.schedule # schedule (Schedule): The schedule for the relay(s) (if any)
        self.rules = relay_config.rules # rules (Dict[str, Rule]): The rules defined for the relay(s) (if any)
        self.collection_interval = 1 # collection_interval (int): The data collection interval in seconds
        self.rules_engine = RulesEngine(self.relay_id, self.rules) # rules_engine (RulesEngine): The rules engine instance for rule evaluation
        self.schedule_engine = ScheduleEngine(self.relay_id, self.schedule) # schedule_engine (ScheduleEngine): The schedule engine instance for schedule management
        self.state = self.boot_power # state (bool): The current state of the relay(s) (default to boot_power)
        self.i2c = None # i2c (board.I2C): The I2C bus instance for the sensor
        self.sensor = None # sensor (adafruit_ina260.INA260): The sensor instance for the relay(s)
        self.redis = None
    
    async def start(self):
        await self.init_redis()
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
    
    async def init_redis(self):
        try:
            self.redis = await RedisClient.get_instance()
            logger.info("Redis client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client")

    async def manage_schedule(self):
        """
        Manages the relay schedule by checking the desired state from the schedule engine
        and updating the relay state if necessary.

        We dont want it to sleep, this should really just happen once when the server starts that way users can use the relay buttons
        without being overidden by the schedule.
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
        # Implement logic for this here or in a separate function/file
    
    async def collect_data_loop(self):
        """
        Collects data from the sensor in a loop and evaluates rules based on the collected data.
        """
        while True:
            try:
                data = await self.collect_data()
                await self.stream_data(data)
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
        return {"relay": self.relay_id, "volts": volts, "amps": amps, "watts": watts}
    
    async def stream_data(self, data: Dict[str, float]):
        """
        Streams the collected data to Redis for storage and further processing.

        Args:
            data (Dict[str, float]): The data to be streamed.
        """
        if not self.redis:
            logger.error("Redis client not initialized")
            return
        try:
            await self.redis.xadd(self.relay_id, data)
            logger.info(f"Data streamed for relay {self.relay_id}")
        except Exception as e:
            logger.error(f"Error streaming data for relay {self.relay_id}: {e}")
