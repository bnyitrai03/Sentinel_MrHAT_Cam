from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import numpy as np
import logging
from .camera import ICamera, Camera
from .mqtt import ICommunication, MQTT
from .rtc import IRTC, RTC
from .system import ISystem, System
from .app_config import Config
from .message import MessageCreator
from .logger import Logger
from .schedule import Schedule


class State(ABC):
    @abstractmethod
    def handle(self, context: 'Context') -> None:
        pass


class Context:
    def __init__(self):
        self._state: State = InitState()
        self.config: Config = Config()
        self.camera: ICamera = Camera()
        self.communication: ICommunication = MQTT()
        self.rtc: IRTC = RTC()
        self.system: ISystem = System()
        self.schedule: Schedule = Schedule()
        self.message_creator: MessageCreator = MessageCreator(self.system, self.rtc, self.camera)
        self.logger: Logger = Logger()
        print("Initializing Context completed")

    def request(self) -> None:
        self._state.handle(self)

    def set_state(self, state: State) -> None:
        self._state = state


class InitState(State):
    def handle(self, context: Context) -> None:
        print("In InitState")
        """ context.config.load()
        context.camera.start()
        context.communication.connect()
        context.logger.start_logging() """
        context.set_state(ConfigCheckState())


class ConfigCheckState(State):
    def handle(self, context: Context) -> None:
        print("In ConfigCheckState")
        """ context.config.check_for_new_config()
        if context.communication.config_received_event.is_set():
            self.handle_new_config(context)
        context.set_state(CreateMessageState()) """
        context.set_state(InitState())

    def handle_new_config(self, context: Context) -> None:
        context.config.load()
        self.send_uuid(context)
        context.communication.reset_config_received_event()

    def send_uuid(self, context: Context) -> None:
        context.communication.send(f"config-ok|{context.config.uuid}")


class CreateMessageState(State):
    def handle(self, context: Context) -> None:
        image = context.camera.capture()
        timestamp = context.rtc.get_time()
        message = context.message_creator.create_message(image, timestamp)
        context.set_state(TransmitState(message))


class TransmitState(State):
    def __init__(self, message: str):
        self.message = message

    def handle(self, context: Context) -> None:
        context.communication.send(self.message)
        waiting_time = context.schedule.calculate_shutdown_duration(context.message_creator.last_operation_time)
        if context.schedule.should_shutdown(waiting_time):
            context.set_state(ShutDownState(waiting_time))
        else:
            context.set_state(ConfigCheckState())


class ShutDownState(State):
    def __init__(self, shutdown_duration: float):
        self.shutdown_duration = shutdown_duration

    def handle(self, context: Context) -> None:
        context.communication.disconnect()
        context.logger.disconnect_remote_logging()
        context.system.schedule_wakeup(self.shutdown_duration)
        # The system will shut down here and restart later
