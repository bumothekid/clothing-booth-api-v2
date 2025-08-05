import logging
import time
import os
from logging.handlers import RotatingFileHandler

# ! stream_handler is used to print logs to console
# ! remove stream_handler to disable console logs (only file logs; useful for production)

class CustomFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = time.strftime(datefmt, ct)
        else:
            s = time.strftime("%Y-%m-%d %H:%M:%S %z", ct)
        return s

    def format(self, record):
        record.asctime = self.formatTime(record, self.datefmt)
        return f"[{record.asctime}] [{record.process}] [{record.levelname}] {record.getMessage()}"

class Logger():
    _logger: logging.Logger = None

    @classmethod
    def getLogger(cls) -> logging.Logger:
        if cls._logger is None:
            
            cls._logger = logging.getLogger()
            cls._logger.setLevel(logging.INFO)
            
            log_filename = f"logs/app.log"
            file_handler = RotatingFileHandler(log_filename, maxBytes=1024*1024, backupCount=5)
            stream_handler = logging.StreamHandler()
            
            formatter = CustomFormatter()
            file_handler.setFormatter(formatter)
            stream_handler.setFormatter(formatter)
            
            cls._logger.addHandler(file_handler)
            cls._logger.addHandler(stream_handler)
        return cls._logger