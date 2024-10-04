import logging
import json
import io
from typing import Dict, Any, Optional
from PIL import Image
import base64
from datetime import datetime
import numpy as np
from .old_utils import log_execution_time
from .old_static_config import IMAGETOPIC, MINIMUM_WAIT_TIME
from .old_system import System, RTC
from .old_camera import Camera
from .old_mqtt import MQTT
from .old_schedule import Schedule
from .old_logger import Logger


class Transmit:
    """
    A class responsible for capturing images, encoding them, and transmitting
    these images with some extra telemetry over an MQTT connection.

    Attributes
    ----------
    camera : Camera
        An instance of the Camera class used to capture images.
    logger : Logger
        An instance of the Logger class used for logging information.
    schedule : Schedule
        An instance of the Schedule class used to manage operation schedules.
    mqtt : MQTT
        An instance of the MQTT class used to handle MQTT communication.
    """

    def __init__(self, camera: Camera, logger: Logger, schedule: Schedule, mqtt: MQTT) -> None:
        """
        Initializes the Transmit class with instances of Camera, Logger,
        Schedule, and MQTT classes.

        Parameters
        ----------
        camera : Camera
            An instance of the Camera class used to capture images.
        logger : Logger
            An instance of the Logger class used for logging information.
        schedule : Schedule
            An instance of the Schedule class used to manage transmission schedules.
        mqtt : MQTT
            An instance of the MQTT class used to handle MQTT communication.
        """
        self.camera = camera
        self.logger = logger
        self.schedule = schedule
        self.mqtt = mqtt

    def log_hardware_info(self, hardware_info: Dict[str, Any]) -> None:
        """
        Logs the provided hardware information to a file.
        This file will be the input of a Matlab script which plots the system metrics.

        Parameters
        ----------
        hardware_info : Dict[str, Any]
            A dictionary containing hardware information such as CPU temperature,
            battery temperature, and other system metrics.
        """
        log_entry = ", ".join(f"{k}={v}" for k, v in hardware_info.items())
        with open("hardware_log.txt", "a") as log_file:
            log_file.write(f"{log_entry}\n")

        logging.info(f"battery_voltage_now: {hardware_info['battery_voltage_now']}")
        logging.info(f"battery_voltage_avg: {hardware_info['battery_voltage_avg']}")
        logging.info(f"battery_current_now: {hardware_info['battery_current_now']}")
        logging.info(f"battery_current_avg: {hardware_info['battery_current_avg']}")
        logging.info(f"charger_voltage_now: {hardware_info['charger_voltage_now']}")
        logging.info(f"charger_current_now: {hardware_info['charger_current_now']}")

    def create_base64_image(self, image_array: Optional[np.ndarray]) -> str:  # type: ignore
        """
        Converts a numpy array representing an image into a base64-encoded JPEG string.

        This method is used to transform raw image data, stored as a numpy array.
        The image data is first converted into a PIL Image object,
        then encoded into JPEG format, and finally converted into a base64 string
        for transmission.

        Parameters
        ----------
        image_array : numpy.ndarray
            The image data as a numpy array.

        Returns
        -------
        str
            The base64-encoded string representation of the JPEG image. This string
            can be used in the JSON message, which requires text-based image encoding.

        Raises
        ------
        ValueError
            If the input image_array is not in a valid format that can be converted
            into a JPEG image.

        Notes
        -----
        - If the provided image array is `None`, then there was an error with the camera during the
        image capture process. Since the connection to the MQTT broker is not established yet,
        the image capturing function will provide `None` as the return value.
        This way we can log the error through MQTT when it connects.
        """
        # If there was an error during image capture, return an error message
        if image_array is None:
            return "Error: Camera was unable to capture the image."

        image: Image.Image = Image.fromarray(image_array)
        image_bytes: io.BytesIO = io.BytesIO()
        image.save(image_bytes, format="JPEG")
        image_data: bytes = image_bytes.getvalue()

        return base64.b64encode(image_data).decode("utf-8")

    @log_execution_time("Creating the json message")
    def create_message(self, image_array: Optional[np.ndarray], timestamp: str) -> str:  # type: ignore
        """
        Creates a JSON message containing image data, timestamp, CPU temperature,
        battery temperature, and battery charge percentage.

        Parameters
        ----------
        image_array : numpy.ndarray
            The image data as a numpy array. This data is converted into a base64-encoded
            JPEG string before being included in the JSON message.
        timestamp : str
            The timestamp in ISO 8601 format.

        Returns
        -------
        str
            The whole JSON message as a string.

        Raises
        ------
        Exception
            If any error occurs during the process of creating the message, such as
            failing to retrieve system information or converting the image to base64.
            The exception is logged, and the error is re-raised.

        Notes
        -----
        - The function also logs additional hardware information to a separate file for further analysis.
        - This method is decorated with `@log_execution_time`, which logs the time taken to execute the method.
        """
        try:
            battery_info = System.get_battery_info()
            hardware_info = System.gather_hardware_info()
            cpu_temp: float = System.get_cpu_temperature()

            logging.info(
                f"Battery temp: {battery_info['temperature']}°C, "
                f"percentage: {battery_info['percentage']} %, "
                f"CPU temp: {cpu_temp}°C"
            )
            message: Dict[str, Any] = {
                "timestamp": timestamp,
                "image": self.create_base64_image(image_array),
                "cpuTemp": cpu_temp,
                "batteryTemp": battery_info["temperature"],
                "batteryCharge": battery_info["percentage"],
            }

            # Log hardware info to a file for further analysis
            if hardware_info:
                self.log_hardware_info(hardware_info)

            return json.dumps(message)

        except Exception as e:
            logging.error(f"Problem creating the message: {e}")
            raise

    def connect_mqtt(self) -> None:
        """
        Connect to the MQTT broker and initialize message receiving.
        """
        self.mqtt.connect()
        self.mqtt.init_receive()

    def get_message(self) -> str:
        """
        This method integrates the process of capturing an image, obtaining the
        current system time, and gathering additional system data into a single
        JSON message.

        Returns
        -------
        str
            A JSON string containing the image data, timestamp, CPU temperature, battery temperature,
            and battery charge percentage as a string.
        """
        image_raw = self.camera.capture()
        timestamp = RTC.get_time()
        message = self.create_message(image_raw, timestamp)
        return message

    @log_execution_time("Taking a picture and sending it")
    def transmit_message(self) -> None:
        """
        Sends the message over MQTT.

        This method orchestrates the entire process of capturing an image, gathering
        system data, creating a message, and transmitting it to a predefined MQTT topic.
        If the MQTT client is not already connected, the method attempts to establish
        the connection in a blocking manner to ensure the message is sent successfully.

        Raises
        ------
        Exception
            If any error occurs during the process, whether it be in capturing the image,
            creating the message, or transmitting it via MQTT. The exception is logged,
            and the error is re-raised.

        Notes
        -----
        - The method ensures that the MQTT client is connected before attempting to
        publish the message.
        - If MQTT logging is not already initialized, the method triggers its start
        to ensure that all communication is logged appropriately.
        - This method is decorated with `@log_execution_time`, which logs the time
        taken to execute the method.
        """
        try:
            message: str = self.get_message()

            if not self.mqtt.client.is_connected():
                self.connect_mqtt()
            if self.logger.mqtt is None:
                self.logger.start_mqtt_logging()

            self.mqtt.publish(message, IMAGETOPIC)

        except Exception as e:
            logging.error(f"Error in run method: {e}")
            raise

    def transmit_message_with_time_measure(self) -> float:
        """
        Run the `transmit_message` method while timing how long it takes to complete.
        The total elapsed time is then used to calculate how long the system should wait
        before the next execution, ensuring that the image sending happens acording to `period`.

        Returns
        -------
        float
            The waiting time (in seconds) until the next execution, which
            is the `period` minus the elapsed time.
        """
        try:
            start_time: str = RTC.get_time()
            self.transmit_message()
            end_time: str = RTC.get_time()
            elapsed_time: float = (
                datetime.fromisoformat(end_time) - datetime.fromisoformat(start_time)
            ).total_seconds()
            waiting_time = self.schedule.period - elapsed_time
            return max(waiting_time, MINIMUM_WAIT_TIME)
        except Exception as e:
            logging.error(f"Error in run_with_time_measure method: {e}")
            raise e
