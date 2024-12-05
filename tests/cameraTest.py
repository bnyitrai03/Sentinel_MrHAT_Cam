import pytest
import numpy as np
import logging
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

    @pytest.fixture(params=[
        {"quality": "4K", "expected_width": 3840, "expected_height": 2160},
        {"quality": "3K", "expected_width": 2560, "expected_height": 1440},
        {"quality": "HD", "expected_width": 1920, "expected_height": 1080},
    ])
    def camera_with_quality(self, request, caplog):
        caplog.set_level(logging.INFO)
        with patch('sentinel_mrhat_cam.Picamera2') as mock_cam:
            mock_instance = MagicMock()
            mock_cam.return_value = mock_instance
            camera = Camera({"quality": request.param["quality"]})
            assert "Camera instance created" in caplog.text
            return {
                "camera": camera,
                "mock_cam": mock_instance,
                "expected_width": request.param["expected_width"],
                "expected_height": request.param["expected_height"]
            }

    def test_camera_initialization(self, camera_with_quality, caplog):
        camera_data = camera_with_quality
        camera = camera_data["camera"]
        assert camera._width == camera_data["expected_width"]
        assert camera._height == camera_data["expected_height"]
        if camera._config["quality"] == "invalid":
            assert "Invalid quality specified" in caplog.text
