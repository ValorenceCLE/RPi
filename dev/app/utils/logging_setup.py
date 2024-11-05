import logging
import asyncio
import sys

# Set up a local logger to log messages to the console/file for more system level messages
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

# Central logger to log specific messages to a AWS EC2 instance set up as a rsylog server
central_logger = logging.getLogger("central_logger")
central_logger.setLevel(logging.INFO)

# Asynchronous handler for sending messages to the central logger over UDP
class AsyncUDPSyslogHandler(logging.Handler):
    def __init__(self, host, port, loop):
        super().__init__()
        self.host = host
        self.port = port
        self.loop = loop
        self.transport = None
        self.ready = asyncio.Event()
        
        # Start the UDP connection
        asyncio.create_task(self._connect())
    
    async def _connect(self):
        transport, protocol = await self.loop.create_datagram_endpoint(
            lambda: asyncio.DatagramProtocol(),
            remote_addr=(self.host, self.port)
        )
        self.transport = transport
        self.ready.set()
    
    def emit(self, record):
        try:
            msg = self.format(record)
            if not self.transport:
                # Wait until the transport is ready
                asyncio.create_task(self._wait_and_send(msg))
            else:
                self.transport.sendto(msg.encode('utf-8'))
        except Exception:
            self.handleError(record)
                
    async def _wait_and_send(self, msg):
        await self.ready.wait()
        self.transport.sendto(msg.encode('utf-8'))
    
    def close(self):
        if self.transport:
            self.transport.close()
        super().close()
        
# Set up the central logger handler
loop = asyncio.get_event_loop()
udp_handler = AsyncUDPSyslogHandler('44.223.77.239', 514, loop)
udp_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
udp_handler.setFormatter(udp_formatter)
central_logger.addHandler(udp_handler)
