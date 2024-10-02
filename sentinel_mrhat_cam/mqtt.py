from abc import ABC, abstractmethod
import threading
from typing import Any


class ICommunication(ABC):
    @abstractmethod
    def connect(self) -> Any:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def init(self) -> None:
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    def send(self, message: str) -> None:
        pass


class MQTT(ICommunication):
    def __init__(self):
        self._broker: str = ""
        self._port: int = 0
        self._qos: int = 0
        self._subtopic: str = ""
        self.broker_connect_counter: int = 0
        self.client = None
        self.config_confirm_message: str = ""
        self.config_received_event: threading.Event = threading.Event()

    def _broker_check(self) -> None:
        pass

    def _is_broker_available(self) -> bool:
        pass

    def _publish(self, message: str, topic: str) -> None:
        pass

    def connect(self) -> Any:
        pass

    def disconnect(self) -> None:
        pass

    def init_receive(self) -> None:
        pass

    def is_connected(self) -> bool:
        pass

    def reset_config_received_event(self) -> None:
        pass

    def send(self, message: str) -> None:
        pass
