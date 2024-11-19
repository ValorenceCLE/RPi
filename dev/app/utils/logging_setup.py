import logging
import logging.handlers
import sys
import socket
import time
from utils.validator import validate_config

# Load the config
config = validate_config()
system_id = config.system.system_id
syslog_server = config.system.syslog_server

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

# Central logger to log specific messages to the AWS EC2 rsyslog server
central_logger = logging.getLogger("central_logger")
central_logger.setLevel(logging.INFO)

class CustomSysLogHandler(logging.handlers.SysLogHandler):
    def __init__(self, address=('localhost', 514), facility=logging.handlers.SysLogHandler.LOG_USER, hostname=None):
        super().__init__(address=address, facility=facility, socktype=socket.SOCK_DGRAM)
        self.hostname = hostname or socket.gethostname()
        # Explicitly create the socket to avoid any issues with delayed initialization
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def emit(self, record):
        try:
            # Format the message according to RFC 3164
            msg = self.format(record)
            # PRI part
            pri = '<%d>' % self.encodePriority(self.facility, self.mapPriority(record.levelname))
            # Timestamp in the format: 'Mmm dd HH:MM:SS'
            timestamp = time.strftime('%b %d %H:%M:%S', time.localtime(record.created))
            # Hostname (system_id)
            hostname = self.hostname
            # App name (logger name)
            app_name = record.name
            # Message content
            message = msg

            # Full syslog message in RFC 3164 format
            syslog_message = f"{pri}{timestamp} {hostname} {app_name}: {message}\n"

            # Ensure message is in bytes format for transmission
            if isinstance(syslog_message, str):
                syslog_message = syslog_message.encode('utf-8')

            # Send the message to the syslog server
            self.socket.sendto(syslog_message, self.address)
        except Exception as e:
            self.handleError(record)
            # Log to local logger in case of errors
            local_logger.error(f"Failed to send syslog message: {e}")

    def close(self):
        if self.socket:
            self.socket.close()
        super().close()

# Set up the central logger handler using CustomSysLogHandler
udp_handler = CustomSysLogHandler(
    address=(syslog_server, 514),
    hostname=system_id
)

# Set the formatter for the central logger handler
udp_formatter = logging.Formatter('%(message)s')
udp_handler.setFormatter(udp_formatter)
central_logger.addHandler(udp_handler)

