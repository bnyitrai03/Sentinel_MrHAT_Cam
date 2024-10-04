import logging
import logging.config
from typing import Any

import yaml
import os
import threading
from queue import Queue, Empty
from multiprocessing.pool import ThreadPool
from .old_static_config import LOGGING_TOPIC, LOG_LEVEL


class Logger(logging.Handler):
    """
    A custom logging handler that manages log messages and their publishing through MQTT.

    This class extends the logging.Handler to provide functionality for queueing log messages,
    publishing them via MQTT, and managing the logging process using a thread pool.

    Parameters
    ----------
    filepath : str
        The path to the logging configuration file.

    Attributes
    ----------
    filepath : str
        The path to the logging configuration file.
    log_queue : Queue
        A queue to buffer log messages while there is no connection to the broker.
    mqtt : MQTT
        An instance of the MQTT class for publishing log messages.
    start_event : threading.Event
        An event to signal the start of MQTT logging.
    pool : ThreadPool
        A thread pool for asynchronous publishing of log messages.

    Raises
    ------
    Exception
        For any unexpected errors during logging operations.
    """

    def __init__(self, filepath: str):
        """
        Initialize the Logger.

        Parameters
        ----------
        filepath : str
            The path to the logging configuration file.
        """
        super().__init__()
        self.filepath = filepath
        self.log_queue: Queue[str] = Queue()
        self.mqtt: Any = None
        self.start_event = threading.Event()
        self.pool = ThreadPool(processes=5)

    def start_logging(self) -> None:
        """
        Start the logging process.

        This method loads the logging configuration from the `sentinel_log_config.yaml` file,
        sets up the logging system, and adds the MQTT handler to the root logger.

        Raises
        ------
        Exception
            For any unexpected errors during the logging setup.
        """
        try:
            if not os.path.exists(self.filepath):
                raise FileNotFoundError(f"Log configuration file not found: {self.filepath}")
            with open(self.filepath, 'r') as f:
                config = yaml.safe_load(f)
            logging.config.dictConfig(config)
            # Add the MQTT handler to the root logger
            self.create_mqtt_handler()
            logging.info("Logging started")

        except Exception:
            exit(1)

    def create_mqtt_handler(self) -> None:
        """
        Create and add the MQTT handler to the root logger.

        This method sets up the logging level, formatter, and adds the current
        instance as a handler to the root logger.
        """
        self.setLevel(LOG_LEVEL)
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.setFormatter(formatter)
        logging.getLogger().addHandler(self)

    def start_mqtt_logging(self) -> None:
        """
        Initialize MQTT connection and start MQTT logging.

        This method creates an instance of the MQTT class, connects to the MQTT
        broker, and signals that MQTT logging has started.
        """
        from .old_mqtt import MQTT

        self.mqtt = MQTT()
        self.mqtt.connect()
        self.start_event.set()

    def emit(self, record: logging.LogRecord) -> None:
        """
        Process a log record, format it, and queue it for publishing.

        This method is called for each log record. It formats the record,
        puts it in the log queue, and triggers asynchronous publishing if
        MQTT logging has started.

        Parameters
        ----------
        record : logging.LogRecord
            The log record to be processed.

        Raises
        ------
        Exception
            If an error occurs during the emit process.
        """
        try:
            msg = self.format(record)
            self.log_queue.put(msg)
            if self.start_event.is_set() and self.mqtt.is_connected():
                self.pool.apply_async(self.publish_loop, args=(msg, LOGGING_TOPIC))

        except Exception as e:
            print(f"Error in Logger emit: {e}")

    def publish_loop(self, msg: str, topic: str) -> None:
        """
        Continuously retrieves and publishes log messages from the queue to the logging MQTT topic.

        Parameters
        ----------
        msg : str
            The log message to be published.
        topic : str
            The MQTT topic to which the log message will be published.

        Returns
        -------
        None
            This function does not return any value.

        Raises
        ------
        Empty
            If the queue is empty and no message is available within the specified timeout.
            There are no more messages to send.
        Exception
            For any other unexpected exceptions that occur during the process.
        """
        while not self.log_queue.empty():
            try:
                msg = self.log_queue.get(timeout=1)
                # Do not publish if not connected
                if self.mqtt.is_connected():
                    self.mqtt.client.publish(topic, msg)
                else:
                    return
            except Empty:
                return
            except Exception as e:
                print(f"Error in Logger publish loop: {e}")

    def disconnect_mqtt(self) -> None:
        """
        Close the logger, disconnect MQTT, and clean up resources.

        This method stops the thread pool, disconnects from the MQTT broker
        if connected, and closes the logging handler.
        """
        self.start_event.clear()
        self.pool.close()
        self.pool.join()
        if self.mqtt is not None and self.mqtt.is_connected():
            self.mqtt.disconnect()
        super().close()
