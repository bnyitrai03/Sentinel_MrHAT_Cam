from .system import ISystem
from .rtc import IRTC
from .camera import ICamera
import numpy as np
from PIL import Image
import io
import base64
from .system import System
from .rtc import RTC
import logging
from typing import Dict, Any
import json


class MessageCreator:
    def __init__(self, system: ISystem, rtc: IRTC, camera: ICamera):
        self._camera = camera
        self._rtc = rtc
        self._system = system

    def _create_base64_image(self) -> str:
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
        # Get picture from camera
        image_array = self._camera.capture()

        image: Image.Image = Image.fromarray(image_array)
        image_bytes: io.BytesIO = io.BytesIO()
        image.save(image_bytes, format="JPEG")
        image_data: bytes = image_bytes.getvalue()

        return base64.b64encode(image_data).decode("utf-8")

    def _log_hardware_info(self, hardware_info: Dict[str, Any]) -> None:
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

    def create_message(self) -> str:
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
        """
        try:
            hardware_info = self._system.get_hardware_info()
            timestamp = self._rtc.get_time()
            image = self._create_base64_image()

            message: Dict[str, Any] = {
                "timestamp": timestamp,
                "image": image,
                "cpuTemp": hardware_info["cpu_temperature"],
                "batteryTemp": hardware_info["battery_temperature"],
                "batteryCharge": hardware_info["battery_percentage"],
            }

            # Log hardware info to a file for further analysis
            if hardware_info:
                self._log_hardware_info(hardware_info)

            return json.dumps(message)

        except Exception as e:
            logging.error(f"Problem creating the message: {e}")
            raise
