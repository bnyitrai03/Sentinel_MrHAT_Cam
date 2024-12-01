import pytest
import numpy as np
import base64
import logging
from typing import Dict, Any
from unittest.mock import mock_open, patch, MagicMock, Mock
from sentinel_mrhat_cam import MessageCreator


@pytest.fixture
def sample_hardware_info() -> Dict[str, Any]:
    """Fixture providing a complete sample hardware information dictionary."""
    return {
        'battery_temperature': 35.5,
        'battery_percentage': 85,
        'cpu_temperature': 65.2,
        'battery_voltage_now': 4.2,
        'battery_voltage_avg': 4.1,
        'battery_current_now': 500,
        'battery_current_avg': 450,
        'charger_voltage_now': 5.0,
        'charger_current_now': 1000
    }


@pytest.fixture
def mock_system():
    """Fixture to create a mock system object"""
    system_mock = MagicMock()
    system_mock.get_hardware_info.return_value = {
        "cpu_temperature": 45.5,
        "battery_temperature": 30.2,
        "battery_percentage": 85
    }
    return system_mock


@pytest.fixture
def mock_rtc():
    """Fixture to create a mock RTC object"""
    rtc_mock = MagicMock()
    rtc_mock.get_time.return_value = "2024-01-15T12:30:45Z"
    return rtc_mock


@pytest.fixture
def mock_image():
    raw_image = np.full((100, 100, 3), 128, dtype=np.uint8)
    base64_image = base64.b64decode(raw_image).decode("utf-8")
    return base64_image


@pytest.fixture
def message_creator(mock_system, mock_rtc, mock_image):
    """Fixture to create a message creator instance with mocked dependencies"""
    message_creator = MagicMock()
    message_creator._system = mock_system
    message_creator._rtc = mock_rtc
    message_creator._create_base64_image.return_value = mock_image
    message_creator.create_message = Mock(wraps=message_creator.create_message)
    return message_creator


# Megy szakdogába :D
def test_create_base64_image_succes():
    test_instance = MessageCreator(camera=MagicMock(), rtc=MagicMock(), system=MagicMock())
    test_image_array = np.full((100, 100, 3), 128, dtype=np.uint8)
    test_instance._camera.capture.return_value = test_image_array

    result = test_instance._create_base64_image()
    assert isinstance(result, str)
    try:
        base64.b64decode(result)
    except Exception as e:
        pytest.fail(f"Base64 encoding failed: {e}")


def test_create_base64_image_no_image():
    test_instance = MessageCreator(camera=MagicMock(), rtc=MagicMock(), system=MagicMock())
    test_instance._camera.capture.return_value = None

    result = test_instance._create_base64_image()
    assert result == "Error: Camera was unable to capture the image."


def test_log_hardware_info_file_writing(sample_hardware_info):
    expected_log_entry = ", ".join(f"{k}={v}" for k, v in sample_hardware_info.items())
    test_instance = MessageCreator(camera=MagicMock(), rtc=MagicMock(), system=MagicMock())
    with patch("builtins.open", mock_open()) as mock_file:
        test_instance._log_hardware_info(sample_hardware_info)

        mock_file.assert_called_once_with("hardware_log.txt", "a")
        mock_file().write.assert_called_once_with(f"{expected_log_entry}\n")


def test_log_hardware_info_logging(sample_hardware_info, caplog):
    test_instance = MessageCreator(camera=MagicMock(), rtc=MagicMock(), system=MagicMock())
    caplog.set_level(logging.INFO)
    test_instance._log_hardware_info(sample_hardware_info)

    log_records = [record.message for record in caplog.records]
    # Verify specific log messages
    assert f"battery_temperature: {sample_hardware_info['battery_temperature']}" in log_records
    assert f"battery_percentage: {sample_hardware_info['battery_percentage']}" in log_records
    assert f"cpu_temperature: {sample_hardware_info['cpu_temperature']}" in log_records
    assert f"battery_voltage_now: {sample_hardware_info['battery_voltage_now']}" in log_records
    assert f"battery_voltage_avg: {sample_hardware_info['battery_voltage_avg']}" in log_records
    assert f"battery_current_now: {sample_hardware_info['battery_current_now']}" in log_records
    assert f"battery_current_avg: {sample_hardware_info['battery_current_avg']}" in log_records
    assert f"charger_voltage_now: {sample_hardware_info['charger_voltage_now']}" in log_records
    assert f"charger_current_now: {sample_hardware_info['charger_current_now']}" in log_records


def test_log_hardware_info_missing_key(sample_hardware_info):
    test_instance = MessageCreator(camera=MagicMock(), rtc=MagicMock(), system=MagicMock())
    # Remove a key from the sample hardware info
    incomplete_hardware_info = sample_hardware_info.copy()
    del incomplete_hardware_info['battery_temperature']
    with pytest.raises(KeyError):
        test_instance._log_hardware_info(incomplete_hardware_info)


def test_create_message_success(message_creator):
    message_creator.create_message()
