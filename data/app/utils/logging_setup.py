import logging
import sys
from utils.validator import validate_config

# Load the config
config = validate_config()
system_id = config.system.system_id

# Set up a local logger to log messages to the console/file for system-level messages
local_logger = logging.getLogger("local_logger")
local_logger.setLevel(logging.INFO)

# Set up a handler for stdout
console_handler = logging.StreamHandler(sys.stdout)
console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)')
console_handler.setFormatter(console_formatter)
local_logger.addHandler(console_handler)

# Handler for file logging
file_handler = logging.FileHandler("application.log")
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)')
file_handler.setFormatter(file_formatter)
local_logger.addHandler(file_handler)
