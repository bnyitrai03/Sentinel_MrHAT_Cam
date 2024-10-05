import logging
import logging.config
import yaml
import os
from .static_config import LOGGING_TOPIC, LOG_LEVEL, LOG_CONFIG_PATH
from .mqtt import ICommunication


class Logger(logging.Handler):
    def __init__(self):
        super().__init__()
        self._filepath = LOG_CONFIG_PATH
        self._remote = None
        self._mqtt_enabled = False
        self.setLevel(LOG_LEVEL)
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.setFormatter(formatter)

    def start_logging(self) -> None:
        try:
            if not os.path.exists(self._filepath):
                raise FileNotFoundError(f"Log configuration file not found: {self._filepath}")
            with open(self._filepath, 'r') as f:
                config = yaml.safe_load(f)
            logging.config.dictConfig(config)
            print("Logging started")
        except Exception as e:
            print(f"Error starting logging: {e}")
            exit(1)

    def start_remote_logging(self, mqtt: ICommunication) -> None:
        self._remote = mqtt
        self._mqtt_enabled = True
        logging.getLogger().addHandler(self)  # Add this handler to the root logger
        print("Remote logging initialized")

    def emit(self, record) -> None:

        try:
            msg = self.format(record)
            if self._mqtt_enabled and self._remote and self._remote.is_connected():
                self._remote.send(msg, LOGGING_TOPIC)
        except Exception as e:
            print(f"Error in Logger emit: {e}")

    def stop_remote_logging(self) -> None:
        self._mqtt_enabled = False
        logging.getLogger().removeHandler(self)
        print("Remote logging stopped")
