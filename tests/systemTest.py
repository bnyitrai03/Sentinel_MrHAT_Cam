import pytest
import subprocess
from unittest.mock import patch, Mock
from sentinel_mrhat_cam import System


def test_mrhatrtcwake_invalid_wake_time_type():
    test = System()
    with pytest.raises(ValueError, match="wake_time must be a str, int, or float"):
        test.schedule_wakeup([])


@patch("subprocess.run")
def test_mrhatrtcwake_subprocess_error(mock_run, caplog):
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
def test_valid_wake_time_inputs(wake_time, expected_cmd):
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
