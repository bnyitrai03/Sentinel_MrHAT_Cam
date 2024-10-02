from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import time
import logging
from functools import wraps
from typing import Optional, Any, TypeVar, Callable, cast
import numpy as np
import threading
from .camera import ICamera, Camera
from .mqtt import ICommunication, MQTT
from .rtc import IRTC, RTC
from .system import ISystem, System
from .app_config import Config
from .message import MessageCreator
from .logger import Logger
from .schedule import Schedule

from .static_config import UUID_TOPIC


class State(ABC):
    @abstractmethod
    def handle(self, context: 'Context') -> None:
        pass


class Context:
    def __init__(self, camera: ICamera, communication: ICommunication, rtc: IRTC, system: ISystem):
        self._state: State = InitState()
        self.config: Config = Config()
        self.camera: ICamera = Camera()
        self.communication: ICommunication = MQTT()
        self.rtc: IRTC = RTC()
        self.system: ISystem = System()
        self.schedule: Schedule = Schedule()
        self.message_creator: MessageCreator = MessageCreator(self.system, self.rtc, self.camera)
        self.logger: Logger = Logger()
        self.message: str

    def request(self) -> None:
        self._state.handle(self)

    def set_state(self, state: State) -> None:
        self._state = state

    F = TypeVar('F', bound=Callable[..., Any])

    def log_execution_time(operation_name: Optional[str] = None) -> Callable[[F], F]:
        def decorator(func: F) -> F:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.perf_counter()
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                execution_time = end_time - start_time

                if operation_name:
                    log_message = f"{operation_name} ({func.__name__}) took {execution_time:.6f} seconds"
                else:
                    log_message = f"{func.__name__} took {execution_time:.6f} seconds"

                logging.info(log_message)
                return result

            return cast(F, wrapper)

        return decorator


class InitState(State):
    def handle(self, context: 'Context') -> None:
        context.camera.start()
        context.communication.connect()
        context.set_state(ConfigCheckState())


class CreateMessageState(State):
    def handle(self, context: 'Context') -> None:
        context.message = context.message_creator.create_message()
        context.communication.connect()
        context.logger.start_remote_logging()
        context.set_state(ConfigCheckState())


class ConfigCheckState(State):

    def handle(self, context: 'Context') -> None:
        context.communication.send(context.config.uuid, UUID_TOPIC)
        context.communication.wait_for_acknowledge()


class TransmitState(State):

    def handle(self, context: 'Context') -> None:
        context.communication.send(context.message)
        waiting_time = context.schedule.calculate_shutdown_duration(context.message_creator.last_operation_time)
        if context.schedule.should_shutdown(waiting_time):
            context.set_state(ShutDownState(waiting_time))
        else:
            context.set_state(ConfigCheckState())


class ShutDownState(State):
    def __init__(self, shutdown_duration: float):
        self.shutdown_duration = shutdown_duration

    def handle(self, context: 'Context') -> None:
        context.communication.disconnect()
        context.logger.disconnect_remote_logging()
        context.system.schedule_wakeup(self.shutdown_duration)
        # The system will shut down here and restart later
