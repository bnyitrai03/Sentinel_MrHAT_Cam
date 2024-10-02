import logging
import logging.config
import yaml
import os
import threading
from queue import Queue, Empty
from multiprocessing.pool import ThreadPool
from .static_config import LOGGING_TOPIC, LOG_LEVEL, LOG_CONFIG_PATH


class Logger(logging.Handler):
    """
    A custom logging handler that manages logging locally and remote.

    This class extends the logging.Handler to provide functionality for queueing log messages,
    publishing them via MQTT, and managing the logging process using a thread pool.

    Attributes
    ----------
    _filepath : str
        The path to the logging configuration file.
    _log_queue : Queue
        A queue to buffer log messages which then can be sent to the broker.
    _remote : ICommunication
        An interface for publishing log messages to a remote log server.
    _start_event : threading.Event
        An event to signal the start of the remote logging.
    _pool : ThreadPool
        A thread pool for asynchronous publishing of log messages.

    Raises
    ------
    Exception
        For any unexpected errors during logging operations.
    """
    def __init__(self):
        """
        Initialize the Logger.
        """
        super().__init__()
        self._filepath = LOG_CONFIG_PATH
        self._log_queue: Queue[str] = Queue()
        self._pool = ThreadPool(processes=5)
        self._start_event = threading.Event()

    def _create_communication_handler(self) -> None:
        """
        Create and add the communication handler to the root logger.

        This method sets up the logging level, formatter, and adds the current
        instance as a handler to the root logger.
        """
        self.setLevel(LOG_LEVEL)
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.setFormatter(formatter)
        logging.getLogger().addHandler(self)

    def _publish_loop(self, msg: str, topic: str) -> None:
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
                msg = self._log_queue.get(timeout=1)
                # Do not publish if not connected
                if self._remote.is_connected():
                    self._remote.send(topic, msg)
                else:
                    return
            except Empty:
                return
            except Exception as e:
                print(f"Error in Logger publish loop: {e}")

    def disconnect_remote_logging(self) -> None:
        """
        Close the logger, and clean up resources.

        This method stops the thread pool, disconnects from the MQTT broker
        if connected, and closes the logging handler.
        """
        self._start_event.clear()
        self._pool.close()
        self._pool.join()
        if self._remote is not None and self._remote.is_connected():
            self._remote.disconnect()
        super().close()

    def emit(self, record) -> None:
        """
        Process a log record, format it, and queue it for publishing.

        This method is called for each log record. It formats the record,
        puts it in the log queue, and triggers asynchronous publishing if
        remote logging has started.

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
            self._log_queue.put(msg)
            if self._start_event.is_set() and self._remote.is_connected():
                self._pool.apply_async(self._publish_loop, args=(msg, LOGGING_TOPIC))

        except Exception as e:
            print(f"Error in Logger emit: {e}")

    def start_logging(self) -> None:
        """
        Start the logging process.

        This method loads the logging configuration from the `sentinel_log_config.yaml` file,
        sets up the logging system, and adds the remote log handler to the root logger.

        Raises
        ------
        Exception
            For any unexpected errors during the logging setup.
        """
        try:
            if not os.path.exists(self._filepath):
                raise FileNotFoundError(f"Log configuration file not found: {self._filepath}")
            with open(self._filepath, 'r') as f:
                config = yaml.safe_load(f)
            logging.config.dictConfig(config)
            # Add the remote handler to the root logger
            self._create_communication_handler()
            logging.info("Logging started")

        except Exception:
            exit(1)

    def start_remote_logging(self) -> None:
        """
        Initialize connection and start remote logging.

        This method uses the ICommunication interface to connect to the MQTT
        broker, and signals that the remote logging has started.
        """
        from .mqtt import MQTT, ICommunication

        self._remote: ICommunication = MQTT()
        self._remote.connect()
        self._start_event.set()
