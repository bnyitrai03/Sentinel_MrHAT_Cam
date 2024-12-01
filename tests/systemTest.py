import pytest
import subprocess
from unittest.mock import patch, Mock, MagicMock
from sentinel_mrhat_cam import System


def test_schedule_wakeup_invalid_wake_time_type():
    test = System()
    with pytest.raises(ValueError, match="wake_time must be a str, int, or float"):
        test.schedule_wakeup([])


@patch("subprocess.run")
def test_schedule_wakeup_subprocess_error(mock_run, caplog):
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd="sudo mrhat-rtcwake -d rtc0 -t $(date +%s -d 'today 06:00')",
        stderr="Error executing rtcwake"
    )
    test = System()
    with pytest.raises(SystemExit):
        test.schedule_wakeup(3600)
    assert "Failed to set RTC wake-up alarm" in caplog.text
    assert "Error executing rtcwake" in caplog.text


@pytest.mark.parametrize("wake_time, expected_cmd", [
    # Test string time input
    ("22:00", "sudo mrhat-rtcwake -d rtc0 -t $(date +%s -d 'today 22:00')"),
    # Test integer seconds input
    (40, "sudo mrhat-rtcwake -d rtc0 -s 40"),
    # Test float seconds input
    (36.5, "sudo mrhat-rtcwake -d rtc0 -s 36.5")
])
def test_schedule_wakeup_valid_wake_time_inputs(wake_time, expected_cmd):
    test = System()
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock()
        test.schedule_wakeup(wake_time)
        mock_run.assert_called_once_with(
            expected_cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )


def test_schedule_wakeup_logging():
    test = System()
    with patch('subprocess.run') as mock_run, \
         patch('logging.error') as mock_log_error:

        mock_error = subprocess.CalledProcessError(
            returncode=1, 
            cmd="sudo mrhat-rtcwake", 
            stderr="Detailed error message"
        )
        mock_run.side_effect = mock_error
        with pytest.raises(SystemExit):
            test.schedule_wakeup(3600)
        
        assert mock_log_error.call_count == 2
        first_call = mock_log_error.call_args_list[0][0][0]
        assert "Failed to set RTC wake-up alarm" in first_call
        second_call = mock_log_error.call_args_list[1][0][0]
        assert "rtcwake error output: Detailed error message" in second_call


def test_get_battery_info_subprocess_error():
    test = System()
    with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'cat')):
        with pytest.raises(subprocess.CalledProcessError):
            test._get_battery_info()


def test_get_battery_info_invalid_uevent_data_format():
    mock_battery_uevent = b"""Invalid data format"""
    with patch('subprocess.run') as mock_run:
        test = System()
        # First call (cat uevent)
        first_call = MagicMock()
        first_call.stdout = mock_battery_uevent
        mock_run.side_effect = first_call
        result = test._get_battery_info()
        assert isinstance(result, dict)


def test_get_battery_info_invalid_upower_data_format():
    mock_upower_output = b"""
    battery (/org/freedesktop/UPower/devices/battery_bq2562x_battery)
      temperature:             invalid temperature
    """
    with patch('subprocess.run') as mock_run:
        test = System()
        # First call (cat uevent)
        first_call = MagicMock()
        first_call.stdout = mock_upower_output
        mock_run.side_effect = first_call
        result = test._get_battery_info()
        assert isinstance(result, dict)


def test_get_charger_info_valid_data():
    test = System()
    mock_charger_uevent = b"""Invalid data format Without proper key=value pairs"""
    with patch('subprocess.run') as mock_run:
        mock_call = MagicMock()
        mock_call.stdout = mock_charger_uevent
        mock_run.return_value = mock_call

        output = test._get_charger_info()
        assert isinstance(output, dict)


def test_get_charger_info_subprocess_error():
    test = System()
    with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'cat')):
        with pytest.raises(subprocess.CalledProcessError):
            test._get_charger_info()


def test_get_hardware_info_successful_retrieval():
    test = System()
    mock_battery_data = {
        "battery_temperature": "38",
        "POWER_SUPPLY_CAPACITY": "85",
        "POWER_SUPPLY_VOLTAGE_NOW": "4200000",
        "POWER_SUPPLY_VOLTAGE_AVG": "4180000",
        "POWER_SUPPLY_CURRENT_NOW": "500000",
        "POWER_SUPPLY_CURRENT_AVG": "480000"
    }
    mock_charger_data = {
        "POWER_SUPPLY_VOLTAGE_NOW": "5000000",
        "POWER_SUPPLY_CURRENT_NOW": "1000000"
    }
    mock_cpu_temp = 45.5

    with patch.object(System, '_get_battery_info', return_value=mock_battery_data), \
         patch.object(System, '_get_charger_info', return_value=mock_charger_data), \
         patch.object(System, '_get_cpu_temperature', return_value=mock_cpu_temp):
        
        result = test.get_hardware_info()
        assert result is not None
        assert 'timestamp' in result
        assert result['battery_temperature'] == 38
        assert result['battery_percentage'] == 85
        assert result['battery_voltage_now'] == 4.2
        assert result['battery_voltage_avg'] == 4.18
        assert result['battery_current_now'] == 0.5
        assert result['battery_current_avg'] == 0.48
        assert result['charger_voltage_now'] == 5.0
        assert result['charger_current_now'] == 1.0


def test_get_hardware_info_partial_data():
    test = System()
    mock_battery_data = {
        "POWER_SUPPLY_CAPACITY": "75"
    }
    mock_charger_data = {}
    mock_cpu_temp = 42.0

    with patch.object(System, '_get_battery_info', return_value=mock_battery_data), \
         patch.object(System, '_get_charger_info', return_value=mock_charger_data), \
         patch.object(System, '_get_cpu_temperature', return_value=mock_cpu_temp):
        
        result = test.get_hardware_info()
        assert result is not None
        assert result['battery_temperature'] == 0
        assert result['battery_percentage'] == 75
        assert result['battery_voltage_now'] == 0
        assert result['battery_voltage_avg'] == 0
        assert result['battery_current_now'] == 0
        assert result['battery_current_avg'] == 0
        assert result['charger_voltage_now'] == 0
        assert result['charger_current_now'] == 0
