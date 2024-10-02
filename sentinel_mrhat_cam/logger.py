class Logger:
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
