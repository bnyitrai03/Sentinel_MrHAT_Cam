import pytest
import json
import logging
from unittest.mock import MagicMock, mock_open, patch
from sentinel_mrhat_cam import Config, MINIMUM_WAIT_TIME, MAXIMUM_WAIT_TIME


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


def test_validate_period_valid_values():
    """Test period validation with valid values."""
    valid_configs = [
        {"uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793", "quality": "4K", "timing": [
            {"period": -1, "start": "00:00:00", "end": "23:59:59"}
        ]},
        {"uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793", "quality": "4K", "timing": [
            {"period": MINIMUM_WAIT_TIME, "start": "00:00:00", "end": "23:59:59"}
        ]},
        {"uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793", "quality": "4K", "timing": [
            {"period": MAXIMUM_WAIT_TIME, "start": "00:00:00", "end": "23:59:59"}
        ]}
    ]
    for config in valid_configs:
        try:
            Config.validate_config(config)
        except Exception as e:
            pytest.fail(f"Valid config {config} raised an unexpected exception: {e}")


def test_validate_period_invalid_values():
    """Test period validation with invalid values."""
    invalid_configs = [
        {"uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793", "quality": "4K", "timing": [
            {"period": "30", "start": "00:00:00", "end": "07:00:00"}
        ]},
        {"uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793", "quality": "4K", "timing": [
            {"period": MINIMUM_WAIT_TIME - 1, "start": "00:00:00", "end": "07:00:00"}
        ]},
        {"uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793", "quality": "4K", "timing": [
            {"period": MAXIMUM_WAIT_TIME + 1, "start": "00:00:00", "end": "07:00:00"}
        ]}
    ]
    for config in invalid_configs:
        with pytest.raises((TypeError, ValueError),
                           match=r"Period must be an integer\.|Period must be -1 or between"):
            Config.validate_config(config)


def test_validate_time_format():
    """Test time format validation."""
    valid_times = ["00:00:00"]
    invalid_times = [
        "24:00:00",  # Invalid hour
        "12:60:00",  # Invalid minute
        "12:34:60",  # Invalid second
        "1:23:45",   # Missing leading zero
        "12:3:45",   # Missing leading zero
        "12:34:5",   # Missing leading zero
        "12-34-56",  # Wrong separator
        "12:34"      # Missing seconds
    ]
    # Valid times should not raise any exceptions
    for time in valid_times:
        config = {
            "uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793",
            "quality": "4K",
            "timing": [{"period": 30, "start": time, "end": "23:59:59"}]
        }
        try:
            Config.validate_config(config)
        except Exception as e:
            pytest.fail(f"Valid time {time} raised an unexpected exception: {e}")
    # Invalid times should raise ValueError
    for time in invalid_times:
        config = {
            "uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793",
            "quality": "4K",
            "timing": [{"period": 30, "start": time, "end": "23:59:59"}]
        }
        with pytest.raises(ValueError, match="Invalid time format"):
            Config.validate_config(config)


def test_validate_interval_coverage(mock_mqtt):
    """Test interval coverage validation."""
    valid_interval_configs = [
        # Full day coverage with continuous intervals
        {"uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793", "quality": "4K", "timing": [
            {"period": -1, "start": "00:00:00", "end": "07:00:00"},
            {"period": 30, "start": "07:00:00", "end": "12:00:00"},
            {"period": -1, "start": "12:00:00", "end": "15:00:00"},
            {"period": 30, "start": "15:00:00", "end": "19:00:00"},
            {"period": -1, "start": "19:00:00", "end": "23:59:59"}
        ]}
    ]
    invalid_interval_configs = [
        # First interval doesn't start at 00:00:00
        {"uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793", "quality": "4K", "timing": [
            {"period": -1, "start": "01:00:00", "end": "07:00:00"}
        ]},
        # Last interval doesn't end at 23:59:59
        {"uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793", "quality": "4K", "timing": [
            {"period": -1, "start": "00:00:00", "end": "23:00:00"}
        ]},
        # Gaps between intervals
        {"uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793", "quality": "4K", "timing": [
            {"period": -1, "start": "00:00:00", "end": "07:00:00"},
            {"period": 30, "start": "08:00:00", "end": "12:00:00"}
        ]}
    ]
    # Valid interval configurations
    for config in valid_interval_configs:
        try:
            Config.validate_config(config)
        except Exception as e:
            pytest.fail(f"Valid interval config raised an unexpected exception: {e}")
    # Invalid interval configurations
    for config in invalid_interval_configs:
        with pytest.raises(
            ValueError,
            match=(
                r"First interval must start at 00:00:00|"
                r"Last interval must end at 23:59:59|"
                r"Intervals must be contiguous"
            )
        ):
            Config.validate_config(config)


def test_set_active_config_various_times(mock_mqtt):
    """Test _set_active_config with different times."""
    valid_config = {
        "uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793",
        "quality": "4K",
        "timing": [
            {"period": -1, "start": "00:00:00", "end": "07:00:00"},
            {"period": 30, "start": "07:00:00", "end": "12:00:00"},
            {"period": -1, "start": "12:00:00", "end": "15:00:00"},
            {"period": 30, "start": "15:00:00", "end": "19:00:00"},
            {"period": -1, "start": "19:00:00", "end": "23:59:59"},
        ]
    }
    test_cases = [
        ("06:59:59", -1, "00:00:00", "07:00:00"),
        ("10:00:00", 30, "07:00:00", "12:00:00"),
        ("14:59:59", -1, "12:00:00", "15:00:00"),
        ("17:00:00", 30, "15:00:00", "19:00:00"),
        ("22:00:00", -1, "19:00:00", "23:59:59")
    ]
    for test_time, expected_period, expected_start, expected_end in test_cases:
        with patch("sentinel_mrhat_cam.RTC.get_time", return_value=test_time):
            with patch("builtins.open", mock_open(read_data=json.dumps(valid_config))):
                config = Config(mock_mqtt)
                assert config.active["period"] == expected_period
                assert config.active["start"] == expected_start
                assert config.active["end"] == expected_end


def test_get_default_config():
    """Test the _get_default_config method."""
    default_config = Config._get_default_config()
    # Assert keys exist
    assert "uuid" in default_config
    assert "quality" in default_config
    assert "timing" in default_config
    # Validate default config
    try:
        Config.validate_config(default_config)
    except Exception as e:
        pytest.fail(f"Default config failed validation: {e}")
