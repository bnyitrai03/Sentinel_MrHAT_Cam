import pytest
import json
import logging
from unittest.mock import MagicMock, mock_open, patch
from sentinel_mrhat_cam import Config


@pytest.fixture
def mock_mqtt():
    """Mock the ICommunication interface."""
    mqtt = MagicMock()
    mqtt.connect = MagicMock()
    mqtt.send = MagicMock()
    mqtt.disconnect = MagicMock()
    return mqtt


@pytest.fixture
def valid_config():
    """Provide a valid configuration."""
    return {
        "uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793",
        "quality": "4K",
        "timing": [
            {"period": -1, "start": "00:00:00", "end": "07:00:00"},
            {"period": 30, "start": "07:00:00", "end": "12:00:00"},
            {"period": -1, "start": "12:00:00", "end": "15:00:00"},
            {"period": 30, "start": "15:00:00", "end": "19:00:00"},
            {"period": -1, "start": "19:00:00", "end": "23:59:59"},
        ],
    }


def test_load_valid_config(mock_mqtt, valid_config):
    with patch("builtins.open", mock_open(read_data=json.dumps(valid_config))):
        with patch("os.path.exists", return_value=True):
            config = Config(mock_mqtt)
            assert config._full_config == valid_config
            assert config.active["uuid"] == valid_config["uuid"]
            assert "quality" in config.active


def test_load_invalid_json(mock_mqtt, caplog):
    caplog.set_level(logging.INFO)
    with patch("builtins.open", mock_open(read_data="invalid json")):
        with patch("os.path.exists", return_value=True):
            Config(mock_mqtt)
    assert "Invalid JSON in the config file:" in caplog.text


def test_load_file_not_found(mock_mqtt, caplog):
    caplog.set_level(logging.INFO)
    with patch("builtins.open", side_effect=FileNotFoundError):
        with patch("os.path.exists", return_value=False):
            Config(mock_mqtt)
    assert "Config file not found: " in caplog.text


def test_validate_invalid_uuid():
    invalid_config = {"uuid": "invalid-uuid", "quality": "4K", "timing": []}
    with pytest.raises(ValueError, match="Invalid UUID format in the config."):
        Config.validate_config(invalid_config)


def test_validate_invalid_quality():
    invalid_config = {"uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793", "quality": "Low", "timing": []}
    with pytest.raises(ValueError, match="Invalid quality specified in the config."):
        Config.validate_config(invalid_config)


def test_validate_invalid_timing():
    invalid_config = {
        "uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793",
        "quality": "4K",
        "timing": [
            {"period": 30, "start": "08:00:00", "end": "07:00:00"}
        ]
    }
    with pytest.raises(ValueError, match="Start time must be before end time in each interval."):
        Config.validate_config(invalid_config)


def test_active_config_set(mock_mqtt, valid_config, caplog):
    caplog.set_level(logging.INFO)
    with patch("builtins.open", mock_open(read_data=json.dumps(valid_config))):
        with patch("os.path.exists", return_value=True):
            with patch("sentinel_mrhat_cam.RTC.get_time") as mock_time:
                mock_time.return_value = "10:00:00"
                config = Config(mock_mqtt)
                assert config.active["period"] == 30
                assert config.active["start"] == "07:00:00"
                assert config.active["end"] == "12:00:00"
