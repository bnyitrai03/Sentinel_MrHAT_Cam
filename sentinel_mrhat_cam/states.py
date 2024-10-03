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
    def handle(self, app: 'Context') -> None:
        pass


dummy_config = {
    "quality": "3K",
    "mode": "periodic",
    "period": 15,
    "wakeUpTime": "00:01:00",
    "shutDownTime": "21:59:00"
}


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
        self.config: Config = Config()
        self.camera: ICamera = Camera(dummy_config)
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
    def handle(self, app: Context) -> None:
        logging.info("In InitState")
        app.camera.start()
        app.set_state(CreateMessageState())


class CreateMessageState(State):
    def handle(self, app: Context) -> None:
        logging.info("In CreateMessageState")
        app.set_state(InitState())

        app.message = app.message_creator.create_message()

        # Connect to the remote server
        app.communication.connect()
        app.logger.start_remote_logging()
        app.set_state(ConfigCheckState())


class ConfigCheckState(State):
    def handle(self, app: Context) -> None:
        app.communication.send(app.config.uuid, UUID_TOPIC)
        app.communication.wait_for_acknowledge()


class TransmitState(State):
    def handle(self, app: Context) -> None:
        app.communication.send(app.message)

        waiting_time = app.schedule.calculate_shutdown_duration()
        if app.schedule.should_shutdown(waiting_time):
            app.set_state(ShutDownState())
        else:
            app.set_state(ConfigCheckState())


class ShutDownState(State):
    def handle(self, app: Context) -> None:
        app.communication.disconnect()
        app.logger.disconnect_remote_logging()
        # The system will shut down here and restart later
