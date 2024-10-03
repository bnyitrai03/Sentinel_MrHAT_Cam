from .system import ISystem
from .rtc import IRTC
from .camera import ICamera
from typing import Optional
import numpy as np
from PIL import Image
import io
import base64
from .system import System, RTC


class MessageCreator:
    def __init__(self, system: ISystem, rtc: IRTC, camera: ICamera):
        self._camera = camera
        self._rtc = rtc
        self._system = system

    def _create_base64_image(self, image_array: Optional[np.ndarray]) -> str:
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

        image_array = self._camera.capture()
        # If there was an error during image capture, return an error message
        if image_array is None:
            return "Error: Camera was unable to capture the image."

        image: Image.Image = Image.fromarray(image_array)
        image_bytes: io.BytesIO = io.BytesIO()
        image.save(image_bytes, format="JPEG")
        image_data: bytes = image_bytes.getvalue()

        return base64.b64encode(image_data).decode("utf-8")

    def create_message(self) -> str:
        hardware_info = System.gather_hardware_info()

    def log_hardware_info(self) -> None:
        pass

        # image = context.camera.capture()
        # timestamp = context.rtc.get_time()
        # get hardware info
