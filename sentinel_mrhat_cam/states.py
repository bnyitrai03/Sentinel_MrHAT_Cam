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
    def reset_runtime()-> None:
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
                # Log the message using logger
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
        app.communication.wait_for_config(app.config.active["uuid"], UUID_TOPIC)
        app.config.load()

        app.set_state(TransmitState())

    @Context.log_and_save_execution_time(function_name="ConfigLoad")
    def _load_new_config(self, app: Context) -> None:
        app.config.load()

    @Context.log_and_save_execution_time(function_name="ConfigAcknowledge")
    def _wait_for_config(self, app: Context) -> None:
        app.communication.wait_for_config(app.config.active["uuid"], UUID_TOPIC)


class TransmitState(State):
    @Context.log_and_save_execution_time(function_name="TransmitState")
    def handle(self, app: Context) -> None:
        logging.info("In TransmitState")
        app.communication.send(app.message, IMAGE_TOPIC)
        app.set_state(IdleState ())


class IdleState (State):
    def handle(self, app: Context) -> None:
        logging.info("In IdleState")

        period: int = app.config.active["period"]  # period of the message sending
        waiting_time: float = max(period - app.runtime, 0)  # time to wait in between the new message creation
        
        logging.info(f"period: {period}")
        logging.info(f"waiting time: {waiting_time}")
        logging.info(f"run time: {app.runtime}")
        
        self._schedule_next_cycle(app, period, waiting_time)

    def _schedule_next_cycle(self, app: Context, period: int, waiting_time: float) -> None:
        # If the period is negative then we must wake up at the end of this time interval
        if period < 0:
            local_wake_time = app.rtc.localize_time(app.config.active["end"])
            logging.info("Pi shutting down")
            self._shutdown(app, local_wake_time)

        # If the time to wait is longer than the threshold then the Pi shuts down before taking the next picture
        elif waiting_time > SHUTDOWN_THRESHOLD:
            shutdown_duration = max(waiting_time - TIME_TO_BOOT_AND_SHUTDOWN, 0)
            logging.info("Pi shutting down")
            self._shutdown(app, shutdown_duration)

        # If the time to wait before taking the next image is short, then we sleep that much
        else:
            logging.info(f"sleeping for {waiting_time} seconds")
            time.sleep(waiting_time)
            # reset the runtime
            app.reset_runtime()
            app.set_state(CreateMessageState())

    def _shutdown(self, app: Context, wake_time: Union[str, int, float]) -> None:
        logging.info(f"Wake time is: {wake_time}")
        app.logger.stop_remote_logging()
        app.communication.disconnect()
        app.system.schedule_wakeup(wake_time)
