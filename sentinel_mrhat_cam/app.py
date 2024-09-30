import logging
from .mqtt import MQTT
from .camera import Camera
from .app_config import Config
from .utils import log_execution_time
from .static_config import CONFIGACKTOPIC
from .schedule import Schedule
from .logger import Logger
from .transmit import Transmit
from .system import System


class App:
    """
    Main application class for managing camera operations and MQTT communication.

    This class handles the image capture, message creation and sending, and periodic execution of
    the tasks based on the provided configuration. Based on the provided configuration,
    the application either sleeps or shuts down the device between the image captures.

    Parameters
    ----------
    config_path : str
        Path to the configuration file.
    logger : Logger
        Logger instance for handling log messages.

    Attributes
    ----------
    config : Config
        Configuration object containing application settings.
    camera : Camera
        Camera object for capturing images.
    mqtt : MQTT
        MQTT client for message publishing and receiving.
    schedule : Schedule
        Schedule the running of the application, and handle the shut down timing.
    logger : Logger
        Logger instance for handling log messages.
    transmit : Transmit
        Transmitter object for creating and sending messages.
    """

    def __init__(self, config_path: str, logger: Logger) -> None:
        """
        Initialize the App with configuration and logger.

        Parameters
        ----------
        config_path : str
            Path to the configuration file.
        logger : Logger
            Logger instance for handling log messages.
        """
        self.config = Config(config_path)
        self.camera = Camera(self.config.data)
        self.mqtt = MQTT()
        # self.schedule = Schedule(period=self.config.data["period"])
        self.logger = logger
        # self.transmit = Transmit(self.camera, self.logger, self.schedule, self.mqtt)

    @log_execution_time("Starting the app")
    def start(self) -> None:
        """
        Check if the current time is in the range of the working hours specified in the
        config file and start the camera.
        """
        self.schedule.working_time_check(self.config.data["wakeUpTime"], self.config.data["shutDownTime"])
        self.camera.start()

    @log_execution_time("Taking a picture and sending it")
    def run(self) -> None:
        """
        Captures and sends an image, then exits the script.
        """
        self.transmit.transmit_message()

    def run_always(self) -> None:
        """
        Taking pictures and sending them over MQTT ASAP and forever.
        """
        while True:
            self.run()

    def run_periodically(self) -> None:
        """
        Periodically takes pictures and sends them over MQTT, based on the period it will
        either shut down between sending two pictures, or just wait within the script.

        This method runs an infinite loop that periodically captures and transmits images based on the
        application's configuration. It checks for a new configuration update before each iteration
        and updates the application's settings if necessary. The method determines whether the device
        should shut down or sleep between image captures based on the time elapsed during transmission
        and the configured period.

        Workflow
        --------
        - Check if a new configuration has been received by the MQTT client.
        - If a new configuration is detected, update the application's settings and acknowledge the receipt.
        - Capture an image and transmit it via MQTT.
        - Measure the time taken to complete the transmission.
        - Determine whether the device should shut down or simply wait for the remainder of the period
        based on the transmission time.
        - If a shutdown is required, manage boot data, initiate the shutdown, and log relevant information.
        - If no shutdown is needed, wait for the remaining time or until a new configuration is received.

        Raises
        ------
        SystemExit
            If an exception occurs during the periodic loop, the application will log the error and exit.
        """
        try:
            while True:
                self.schedule.working_time_check(self.config.data["wakeUpTime"], self.config.data["shutDownTime"])
                # Check if a new configuration has been received
                config_received = self.mqtt.config_received_event.is_set()
                self.check_config_received_event(config_received)

                # Send an image and measure how long it took to send
                waiting_time = self.transmit.transmit_message_with_time_measure()
                logging.info(f"Waiting time is: {waiting_time} seconds")

                if self.schedule.should_shutdown(waiting_time):
                    shutdown_duration = self.schedule.calculate_shutdown_duration(waiting_time)
                    logging.info(f"Shutdown duration is: {shutdown_duration} seconds")
                    System.schedule_wakeup(int(shutdown_duration))
                else:
                    logging.info(f"Sleeping for {waiting_time} seconds")
                    config_received = self.mqtt.config_received_event.wait(timeout=waiting_time)

        except Exception as e:
            logging.error(f"An error occurred while running the periodic loop: {e}")
            exit(1)

    def acknowledge_config(self) -> None:
        """
        Acknowledge the receipt of a new configuration by publishing a confirmation message.
        """
        message = self.mqtt.config_confirm_message
        self.mqtt.publish(message, CONFIGACKTOPIC)
        self.mqtt.reset_config_received_event()

    def update_values(self) -> None:
        """
        Update the application's operational parameters based on the latest configuration data.

        Configuration Parameters
        ------------------------
        - `wakeUpTime` and `shutDownTime`: Define the working hours during which the application is active.
        - `period`: Determines the interval between consecutive image captures and transmissions.
        - `quality`: Sets the quality of images captured by the camera.
        """
        self.schedule.period = self.config.data["period"]
        self.camera.quality = self.config.data["quality"]

    def check_config_received_event(self, config_received: bool) -> None:
        """
        Check if a new configuration has been received and update the application accordingly.

        This method is responsible for detecting when a new configuration has been received via MQTT.
        If a new configuration is detected, the application reloads its settings, acknowledges the
        receipt of the configuration, and updates its operational parameters to reflect the changes.

        Parameters
        ----------
        config_received : bool
            A boolean flag indicating whether a new configuration has been received.
        """
        if config_received:
            self.config.load()
            self.acknowledge_config()
            self.update_values()
            logging.info("Updated configuration")
