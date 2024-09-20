import os
import asyncio
from aiologger.loggers.json import JsonLogger # type: ignore
from aiologger.formatters.json import ExtendedJsonFormatter, LINE_NUMBER_FIELDNAME, FILE_PATH_FIELDNAME # type: ignore
from aiologger.handlers.files import AsyncFileHandler # type: ignore

class RotatingAsyncFileHandler(AsyncFileHandler):
    """
    Custom async file handler that performs log rotation based on file size.
    """
    def __init__(self, filename, max_bytes, backup_count, **kwargs):
        super().__init__(filename, **kwargs)
        self.filename = filename
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
    async def _should_rotate(self):
        try:
            if os.path.exists(self.filename):
                file_size = os.path.getsize(self.filename)
                return file_size >= self.max_bytes
        except FileNotFoundError:
            return False
        return False
    
    async def _rotate(self):
        await self.close()
        
        for i in range(self.backup_count - 1, 0, -1):
            old_log = f"{self.filename}.{i}"
            new_log = f"{self.filename}.{i + 1}"
            if os.path.exists(old_log):
                os.rename(old_log, new_log)
        
        new_log = f"{self.filename}.1"
        if os.path.exists(self.filename):
            os.rename(self.filename, new_log)
        
        await self.open()
    
    async def emit(self, record):
        if await self._should_rotate():
            await self._rotate()
        await super().emit(record)

async def setup_logging(log_file=None, log_dir='/var/log/app', max_bytes=5 * 1024 * 1024, backup_count=5):
    """
    Sets up async logging with custom log rotation for an application using aiologger's JsonLogger.

    Parameters:
    - log_file: The log file to write logs to.
    - log_dir: The directory where log files are stored.
    - max_bytes: Maximum size in bytes before rotating the log file.
    - backup_count: Number of backup log files to keep.
    """
    # Ensure the log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # full path for the log file
    log_file_path = os.path.join(log_dir, log_file)
    
    # Create a logger instance
    logger = JsonLogger(level='INFO')
    
    # Create a rotating file handler
    rotating_handler = RotatingAsyncFileHandler(
        filename=log_file_path,
        max_bytes=max_bytes,
        backup_count=backup_count
    )
    
    # Attach the extended JSON formatter to the rotating file handler
    json_formatter = ExtendedJsonFormatter(exclude_fields=[LINE_NUMBER_FIELDNAME, FILE_PATH_FIELDNAME])
    rotating_handler.formatter = json_formatter
    
    # Add the rotating handler to the logger
    logger.add_handler(rotating_handler)
    
    return logger


logger = asyncio.run(setup_logging(log_file='data.log'))  # Initialize the logger