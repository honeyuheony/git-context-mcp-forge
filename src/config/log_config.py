import os
import logging
from typing import Optional

class Logger:
    _instance: Optional['Logger'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.logger = logging.getLogger("MyLogger")

            if not cls._instance.logger.hasHandlers():
                # StreamHandler
                formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
                stream_handler = logging.StreamHandler()
                stream_handler.setFormatter(formatter)

                cls._instance.logger.addHandler(stream_handler)
                if os.getenv("ENV") == "dev":
                    cls._instance.logger.setLevel(logging.DEBUG)
                else:
                    cls._instance.logger.setLevel(logging.INFO)
        return cls._instance

    def __init__(self):
        pass

    def info(self, value: str):
        self.logger.info(f"{value}",)

    def debug(self, value: str):
        self.logger.debug(f"{value}")

    def warning(self, value: str):
        self.logger.warning(f"{value}")

    def error(self, value: str):
        if os.getenv("ENV") == "dev":
            self.logger.error(f"{value}", exc_info=True)
        else:
            self.logger.error(f"{value}")