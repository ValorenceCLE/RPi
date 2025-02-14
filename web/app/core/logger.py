
#! -----REFACTORING NOTES-----
#! ----- DELETE THIS FILE -----
#? We should make one standardized logger file

import asyncio 

class LoggerWrapper:
    def __init__(self):
        self._logger = None
        self._lock = asyncio.Lock()
        
    async def setup(self, log_file='web.log'):
        async with self._lock:
            if self._logger is None:
                from core.logging_setup import setup_logging
                self._logger = await setup_logging(log_file=log_file)
                
    def __getattr__(self, name):
        if self._logger is None:
            raise RuntimeError("Logger not set up")
        return getattr(self._logger, name)
    
logger = LoggerWrapper()