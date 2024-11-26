from abc import ABC, abstractmethod
import time
import logging
from functools import wraps
from typing import Any, TypeVar, Callable, cast, Union
from .camera import ICamera, Camera
from .mqtt import ICommunication, MQTT
from .system import ISystem, System
from .rtc import IRTC, RTC
from .app_config import Config
from .message import MessageCreator
from .logger import Logger
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
        self.config: Config = Config(self.communication)
        self.camera: ICamera = Camera(self.config.active)
        self.system: ISystem = System()
        self.rtc: IRTC = RTC()
        self.message_creator: MessageCreator = MessageCreator(self.camera, self.rtc, self.system)
        self.logger = logger
        self.message: str = "Uninitialized message"

    def request(self) -> None:
        self._state.handle(self)

    def set_state(self, state: State) -> None:
        self._state = state

    @staticmethod
    def reset_runtime() -> None:
        Context.runtime = 0.0

    @staticmethod
    def log_and_save_execution_time(function_name: str) -> Callable[[F], F]:
        """
        Saves the execution time of the function to the `runtime` variable.

        Args:
            function_name (Optional[str], optional): Operation description. Defaults to None.

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
                log_message = f"{function_name} took {execution_time:.6f} seconds"

                # Update the class-level runtime
                Context.runtime += execution_time
                logging.info(log_message)

                return result

            return cast(F, wrapper)

        return decorator


class InitState(State):
    @Context.log_and_save_execution_time(function_name="InitState")
    def handle(self, app: Context) -> None:
        logging.info("In InitState")
        app.camera.start()
        app.set_state(CreateMessageState())


class CreateMessageState(State):
    @Context.log_and_save_execution_time(function_name="CreateMessageState")
    def handle(self, app: Context) -> None:
        logging.info("In CreateMessageState")
        app.message = app.message_creator.create_message()
        logging.info("After creating message")

        # Connect to the remote server if not connected already
        if not app.communication.is_connected():
            app.communication.connect()
            app.logger.start_remote_logging(app.communication)

        app.set_state(ConfigCheckState())


class ConfigCheckState(State):
    @Context.log_and_save_execution_time(function_name="ConfigCheckState")
    def handle(self, app: Context) -> None:
        logging.info("In ConfigCheckState")
        # Send the current config uuid
        app.communication.clear_config_received()
        app.communication.send(app.config.active["uuid"], UUID_TOPIC)
        # If new config is received load it
        if app.communication.wait_for_config() is True:
            app.config.load()

        app.set_state(TransmitState())


class TransmitState(State):
    @Context.log_and_save_execution_time(function_name="TransmitState")
    def handle(self, app: Context) -> None:
        logging.info("In TransmitState")
        app.communication.send(app.message, IMAGE_TOPIC)
        app.set_state(IdleState())


class IdleState (State):
    def handle(self, app: Context) -> None:
        logging.info("In IdleState")

        period: int = app.config.active["period"]  # period of the message sending
        waiting_time: float = max(period - app.runtime, 0)  # time to wait in between the new message creation
        if waiting_time == 0:
            logging.warning("The current period is too fast")

        logging.info(f"period: {period}")
        logging.info(f"waiting time: {waiting_time}")
        logging.info(f"run time: {app.runtime}")

        self._schedule_next_cycle(app, period, waiting_time)

    def _schedule_next_cycle(self, app: Context, period: int, waiting_time: float) -> None:
        if period == -1:
            local_wake_time = app.rtc.localize_time(app.config.active["end"])
            logging.info("Pi shutting down")
            self._shutdown(app, local_wake_time)

        elif waiting_time > SHUTDOWN_THRESHOLD:
            shutdown_duration = max(waiting_time - TIME_TO_BOOT_AND_SHUTDOWN, 0)
            logging.info("Pi shutting down")
            self._shutdown(app, shutdown_duration)

        else:
            logging.info(f"sleeping for {waiting_time} seconds")
            time.sleep(waiting_time)
            app.reset_runtime()
            app.set_state(CreateMessageState())

    def _shutdown(self, app: Context, wake_time: Union[str, int, float]) -> None:
        logging.info(f"Wake time is: {wake_time}")
        app.logger.stop_remote_logging()
        app.communication.disconnect()
        app.system.schedule_wakeup(wake_time)
