from abc import ABC, abstractmethod
import time
import logging
from functools import wraps
from typing import Optional, Any, TypeVar, Callable, cast, Union
from .camera import ICamera, Camera
from .mqtt import ICommunication, MQTT
from .rtc import IRTC, RTC
from .system import ISystem, System
from .app_config import Config
from .message import MessageCreator
from .logger import Logger

from .schedule import Schedule
from .static_config import UUID_TOPIC, IMAGE_TOPIC, SHUTDOWN_THRESHOLD, TIME_TO_BOOT_AND_SHUTDOWN
F = TypeVar('F', bound=Callable[..., Any])


class State(ABC):
    @abstractmethod
    def handle(self, app: 'Context') -> None:
        pass


class Context:
    runtime: float = 0.0  # static varibale to measure the accumulated runtime of the application

    def __init__(self, logger: Logger):
        self._state: State = InitState()
        self.communication: ICommunication = MQTT()
        self.rtc: IRTC = RTC()
        self.config: Config = Config(self.rtc, self.communication)
        self.camera: ICamera = Camera(self.config.active)  # !!!!!!!!
        self.system: ISystem = System()
        self.schedule: Schedule = Schedule()

        # self.message_creator: MessageCreator = MessageCreator(self.system, self.rtc, self.camera)
        self.logger = logger
        self.message: str = "Uninitialized message"

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
    @Context.log_and_save_execution_time(operation_name="InitState")
    def handle(self, app: Context) -> None:
        logging.info("In InitState")
        # app.camera.start()  # ha jött egy új config akkor elvileg innen kéne indulni?
        app.set_state(CreateMessageState())


class CreateMessageState(State):
    @Context.log_and_save_execution_time(operation_name="CreateMessageState")
    def handle(self, app: Context) -> None:
        logging.info("In CreateMessageState")
        # app.message = app.message_creator.create_message()

        # Connect to the remote server if not connected already
        if not app.communication.is_connected():
            app.communication.connect()
            app.communication.init_receive()
            app.logger.start_remote_logging(app.communication)

        app.set_state(ConfigCheckState())


class ConfigCheckState(State):
    @Context.log_and_save_execution_time(operation_name="ConfigCheckState")
    def handle(self, app: Context) -> None:
        logging.info("In ConfigCheckState")

        start_time = time.time()
        app.communication.wait_for_config(app.config.active["uuid"], UUID_TOPIC)
        end_time = time.time()
        logging.info(f"Exiting ConfigCheckState after {end_time - start_time:.3f} seconds")

        logging.info(f"Active config: {app.config.active}")
        app.set_state(TransmitState())

        # check if the Pi is not within working hours
        # if app.schedule.should_shutdown(app.config.active["start"], app.config.active["end"]):
        #    app.set_state(ShutdownState())
        # else:


class TransmitState(State):
    @Context.log_and_save_execution_time(operation_name="TransmitState")
    def handle(self, app: Context) -> None:
        logging.info("In TransmitState")
        app.communication.send(app.message, IMAGE_TOPIC)
        app.set_state(ShutdownState())


class ShutdownState(State):
    def handle(self, app: Context) -> None:
        logging.info("In ShutDownState")

        # Debug
        app.set_state(CreateMessageState())

        # Keep this during development
        logging.info(f"Accumulated runtime: {app.runtime}")

        # period: int = app.config.active["period"]  # period of the message sending
        # waiting_time: float = max(period - app.runtime, 0)  # time to wait in between the new message creation
        # self._shutdown_mode(period, waiting_time)

    def _shutdown_mode(self, app: Context, period: int, waiting_time: float) -> None:
        # If the period is negative then we must wake up at the end of this time interval
        if period < 0:
            local_wake_time = app.schedule.adjust_time(app.config.active["end"])
            self._shutdown(app, local_wake_time)

        # If the time to wait is longer than the threshold then the Pi shuts down before taking the next picture
        elif waiting_time > SHUTDOWN_THRESHOLD:
            shutdown_duration = max(waiting_time - TIME_TO_BOOT_AND_SHUTDOWN, 0)
            self._shutdown(app, shutdown_duration)

        # If the time to wait before taking the next image is short, then we sleep that much
        else:
            time.sleep(waiting_time)
            # reset the runtime
            app.runtime = 0
            app.set_state(CreateMessageState())

    def _shutdown(self, app: Context, wake_time: Union[str, int, float]) -> None:
        app.logger.stop_remote_logging()
        app.communication.disconnect()
        app.system.schedule_wakeup(wake_time)
