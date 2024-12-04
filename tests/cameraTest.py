import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from sentinel_mrhat_cam import Camera


class CameraTest:
    @pytest.fixture
    def camera(self):
        with patch('sentinel_mrhat_cam.Picamera2') as mock_cam:
            mock_instance = MagicMock()
            mock_cam.return_value = mock_instance
        camera = Camera({"quality": "invalid"})
        return camera


    def test_invalid_camera_start(self, camera):
        camera.start()
        camera._cam.create_still_configuration.assert_called_once_with({"size": (2560, 1440)})
        camera._cam.configure.assert_called_once()
        camera._cam.start.assert_called_once_with(show_preview=False)


    def test_camera_capture_success(self, camera):
        mock_image = np.random.randint(0, 255, (2560, 1440, 3), dtype=np.uint8)
        camera._cam.capture_array.return_value = mock_image
        result = camera.capture()
        camera._cam.capture_array.assert_called_once()
        assert isinstance(result, np.ndarray)
        assert result.shape == (2560, 1440, 3)
        np.testing.assert_array_equal(result, mock_image)

    def test_camera_capture_failure(self, camera):
        camera._cam.capture_array.side_effect = Exception("Capture failed")
        result = camera.capture()
        assert result is None
