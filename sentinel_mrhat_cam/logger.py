import logging
import logging.config
import yaml
import os
import threading
from queue import Queue, Empty
from .static_config import LOGGING_TOPIC, LOG_LEVEL, LOG_CONFIG_PATH
from .mqtt import ICommunication


class Logger(logging.Handler):
    def __init__(self):
        super().__init__()
        self._filepath = LOG_CONFIG_PATH
        self._remote = None
        self._start_event = threading.Event()
        self._log_queue: Queue[str] = Queue()
        # configure the custom log handler
        self.setLevel(LOG_LEVEL)
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.setFormatter(formatter)

    def emit(self, record) -> None:
        try:
            msg = self.format(record)
            self._log_queue.put(msg)
            if self._start_event.is_set():
                self._publish_loop(LOGGING_TOPIC)
        except Exception as e:
            print(f"Error in Logger emit: {e}")

    def _publish_loop(self, topic: str) -> None:
        """
        Continuously retrieves and publishes log messages from the queue to the remote server.

        Parameters
        ----------
        msg : str
            The log message to be published.
        topic : str
            The MQTT topic to which the log message will be published.

        Raises
        ------
        Empty
            If the queue is empty and no message is available within the specified timeout.
            There are no more messages to send.
        Exception
            For any other unexpected exceptions that occur during the process.
        """
        while not self._log_queue.empty():
            try:
                # Do not publish if not connected
                if self._remote.is_connected():
                    msg: str = self._log_queue.get(timeout=1)
                    self._remote.send(msg, topic)
                else:
                    return
            except (Empty, TimeoutError):
                return
            except Exception as e:
                print(f"Error in Logger publish loop: {e}")

    def start_logging(self) -> None:
        try:
            if not os.path.exists(self._filepath):
                raise FileNotFoundError(f"Log configuration file not found: {self._filepath}")
            with open(self._filepath, 'r') as f:
                config = yaml.safe_load(f)
            logging.config.dictConfig(config)
            # add the MQTT handler to the root logger
            logging.getLogger().addHandler(self)
            logging.info("Logging started")
        except Exception as e:
            print(f"Error starting logging: {e}")
            exit(1)

    def start_remote_logging(self, mqtt: ICommunication) -> None:
        self._remote = mqtt
        self._start_event.set()

    def stop_remote_logging(self) -> None:
        self._start_event.clear()
        logging.getLogger().removeHandler(self)
        super().close()
