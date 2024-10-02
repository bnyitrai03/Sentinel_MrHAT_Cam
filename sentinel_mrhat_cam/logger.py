import logging
import logging.config
from typing import Any
import yaml
import os
import threading
from queue import Queue, Empty
from multiprocessing.pool import ThreadPool
from .static_config import LOGGING_TOPIC, LOG_LEVEL


class Logger(logging.Handler):
    def __init__(self):
        self._filepath: str = ""
        self._log_queue: Queue[str] = Queue()
        self._mqtt: Any = None
        self._pool = None
        self._start_event: threading.Event = threading.Event()

    def _create_communication_handler(self) -> None:
        pass

    def _publish_loop(self, msg: str, topic: str) -> None:
        pass

    def disconnect_remote_logging(self) -> None:
        pass

    def emit(self, record) -> None:
        pass

    def start_logging(self) -> None:
        pass

    def start_remote_logging(self) -> None:
        pass
