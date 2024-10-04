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
from .static_config import UUID_TOPIC, IMAGE_TOPIC
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
    # static varibale to measure the accumulated runtime of the application
    runtime: float = 0.0  # need to reset if we don't shut down

    def __init__(self, logger: Logger):
        config = {
            "uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793",
            "quality": "4K",
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
        self.camera: ICamera = Camera(config)
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

    @staticmethod
    def log_and_save_execution_time(operation_name: Optional[str] = None) -> Callable[[F], F]:
        """
        Saves the execution time of the function to the `runtime` variable.

        Args:
            operation_name (Optional[str], optional): Operation description. Defaults to None.

        Returns:
            Callable[[F], F]: Wrapped function with logging.
        """
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

                # Update the class-level runtime
                Context.runtime += execution_time
                # Log the message using logger
                logging.info(log_message)

                return result

            return cast(F, wrapper)

        return decorator


class InitState(State):
    @Context.log_and_save_execution_time(operation_name="InitState handle")
    def handle(self, app: Context) -> None:
        logging.info("In InitState \n")
        app.camera.start()
        app.set_state(CreateMessageState())


class CreateMessageState(State):
    @Context.log_and_save_execution_time(operation_name="CreateMessageState handle")
    def handle(self, app: Context) -> None:
        logging.info("In CreateMessageState \n")
        app.schedule.working_time_check()
        app.message = app.message_creator.create_message()

        # Connect to the remote server
        app.communication.connect()
        app.logger.start_remote_logging()
        app.set_state(ConfigCheckState())


class ConfigCheckState(State):
    @Context.log_and_save_execution_time(operation_name="ConfigCheckState handle")
    def handle(self, app: Context) -> None:
        logging.info("In ConfigCheckState \n")
        # app.communication.wait_for_config(app.config.uuid, UUID_TOPIC)
        app.set_state(TransmitState())


class TransmitState(State):
    @Context.log_and_save_execution_time(operation_name="TransmitState handle")
    def handle(self, app: Context) -> None:
        logging.info("In TransmitState")
        app.communication.send(app.message, IMAGE_TOPIC)
        app.set_state(ShutDownState())


class ShutDownState(State):
    def handle(self, app: Context) -> None:
        logging.info("In ShutDownState")

        # Keep this during development
        logging.info(f"Runtime: {Context.runtime}")

        # This wouldnt work if it were in the TransmitState, because the runtime variable is only updated after the function has ran,
        # so this needs to be in shutdown state
        desired_shutdown_duration = app.schedule.calculate_shutdown_duration(Context.runtime)
        should_we_shut_down = app.schedule.should_shutdown(desired_shutdown_duration)

        if should_we_shut_down:

        else:
            app.set_state(CreateMessageState())

        app.communication.disconnect()
        app.logger.disconnect_remote_logging()
        # The system will shut down here and restart later
