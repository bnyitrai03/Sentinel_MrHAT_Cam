from abc import ABC, abstractmethod
from typing import Optional
import numpy as np
from unittest.mock import MagicMock
try:
    from libcamera import controls
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = MagicMock()
    controls = MagicMock()
import logging


class ICamera(ABC):
    @abstractmethod
    def capture(self) -> Optional[np.ndarray]:
        pass

    @abstractmethod
    def start(self) -> None:
        pass


class Camera(ICamera):
    def __init__(self, config: dict[str, str]) -> None:
        self._quality = 95
        self._cam = Picamera2()
        self._config = config

        # Set the premade settings
        if self._config["quality"] == "4K":
            self._width = 3840
            self._height = 2160
        elif self._config["quality"] == "3K":
            self._width = 2560
            self._height = 1440
        elif self._config["quality"] == "HD":
            self._width = 1920
            self._height = 1080
        # If the specified quality is not found, default to 3K quality
        else:
            self._width = 2560
            self._height = 1440
            logging.error(f"Invalid quality specified: {self._config['quality']}. Defaulting to 3K quality.")
        logging.info("Camera instance created")

        # Test logging
        logging.info(f"Config quality: {self._config['quality']}")

    def start(self) -> None:
        """
        Configures and starts the camera with the settings from the config file.

        This function sets up the camera configuration based on the _width and _height
        attributes, applies the quality setting, and sets the autofocus mode to continuous.
        Finally, it starts the camera.

        Parameters
        ----------
        None
        """
        config = self._cam.create_still_configuration({"size": (self._width, self._height)})
        self._cam.configure(config)
        self._cam.options["quality"] = self._quality
        self._cam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        self._cam.start(show_preview=False)
        logging.info("Camera started")

    def capture(self) -> Optional[np.ndarray]:
        """
        Captures an image from the camera and returns it as numpy array.

        Returns
        -------
        ndarray
            The captured image as a numpy array.
        """
        try:
            image = self._cam.capture_array()
        except Exception as e:
            logging.error(f"Error during image capture: {e}")
            return None
        return image

    def update_configuration(self, config: dict[str, str]) -> None:
        self._config = config
