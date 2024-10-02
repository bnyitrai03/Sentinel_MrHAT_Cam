from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class ICamera(ABC):
    @abstractmethod
    def capture(self) -> Optional[np.ndarray]:
        pass

    @abstractmethod
    def start(self) -> None:
        pass


class Camera(ICamera):
    def __init__(self):
        self._cam = None
        self._height: int = 0
        self._quality: int = 0
        self._width: int = 0

    def _create_base64_image(self, image_array: Optional[np.ndarray]) -> str:
        pass

    def capture(self) -> Optional[np.ndarray]:
        pass

    def start(self) -> None:
        pass
