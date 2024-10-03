from abc import ABC, abstractmethod
import time
import logging
from functools import wraps
from typing import Optional, Any, TypeVar, Callable, cast
from .camera import ICamera, Camera
from .mqtt import ICommunication, MQTT
from .rtc import IRTC, RTC
from .system import ISystem, System
from .app_config import Config
from .message import MessageCreator
from .logger import Logger

from .schedule import Schedule
from .static_config import UUID_TOPIC, LOG_CONFIG_PATH
F = TypeVar('F', bound=Callable[..., Any])


class State(ABC):
    @abstractmethod
    def handle(self, context: 'Context') -> None:
        pass


class Context:
    def __init__(self, logger: Logger):
        config = {
            "uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793",
            "quality": "3K",
            "timing": [
                {
                    "period": -1,
                    "start": "00:00:00",
                    "end": "07:00:00"
                },
                {
                    "period": 30,
                    "start": "07:00:00",
                    "end": "12:00:00"
                },
                {
                    "period": -1,
                    "start": "12:00:00",
                    "end": "15:00:00"
                },
                {
                    "period": 30,
                    "start": "15:00:00",
                    "end": "19:00:00"
                },
                {
                    "period": -1,
                    "start": "19:00:00",
                    "end": "23:59:59"
                }
            ]
        }
        self._state: State = InitState()
        self.config: Config = Config(config)
        self.camera: ICamera = Camera()
        self.communication: ICommunication = MQTT()
        self.rtc: IRTC = RTC()
        self.system: ISystem = System()
        self.schedule: Schedule = Schedule()

        self.message_creator: MessageCreator = MessageCreator(self.system, self.rtc, self.camera)
        self.logger = logger
        self.message: str = None

    def request(self) -> None:
        self._state.handle(self)

    def set_state(self, state: State) -> None:
        self._state = state

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
    def handle(self, context: Context) -> None:
        logging.info("In InitState")
        context.camera.start()
        context.set_state(CreateMessageState())


class CreateMessageState(State):
    def handle(self, context: Context) -> None:
        logging.info("In CreateMessageState")
        context.set_state(InitState())  # to debug
        context.message = context.message_creator.create_message()
        context.communication.connect()
        context.logger.start_remote_logging()
        context.set_state(ConfigCheckState())


class ConfigCheckState(State):
    def handle(self, context: Context) -> None:
        # context.communication.send(context.config.uuid, UUID_TOPIC)
        # context.communication.wait_for_acknowledge()
        exit(1)


class TransmitState(State):
    def handle(self, context: Context) -> None:
        context.communication.send(context.message)

        waiting_time = context.schedule.calculate_shutdown_duration()
        if context.schedule.should_shutdown(waiting_time):
            context.set_state(ShutDownState())
        else:
            context.set_state(ConfigCheckState())


class ShutDownState(State):
    def handle(self, context: Context) -> None:
        context.communication.disconnect()
        context.logger.disconnect_remote_logging()
        # The system will shut down here and restart later
