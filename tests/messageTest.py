import pytest
import numpy as np
from PIL import Image
import io
import base64
from unittest.mock import MagicMock
from sentinel_mrhat_cam import MessageCreator


# Megy szakdogába :D
def test_create_base64_image():
    test_instance = MessageCreator(camera=MagicMock(), rtc=MagicMock(), system=MagicMock())
    test_image_array = np.full((100, 100, 3), 128, dtype=np.uint8)
    test_instance._camera.capture.return_value = test_image_array

    result = test_instance._create_base64_image()
    assert isinstance(result, str)
    try:
        Image.open(io.BytesIO(base64.b64decode(result)))
    except Exception as e:
        pytest.fail(f"Image is not encoded error: {e}")
