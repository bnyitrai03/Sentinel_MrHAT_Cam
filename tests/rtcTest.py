import pytest
import subprocess
import datetime
import pytz
from unittest.mock import patch, MagicMock
from sentinel_mrhat_cam import RTC

class RTCTest:
    @patch('sentinel_mrhat_cam.RTC._get_timedatectl')
    def test_extract_time_success(self, mock_get_timedatectl):
        mock_lines = [
            "Some header",
            "RTC time: Wed 2024-11-15 14:30:45 UTC"
        ]
        mock_get_timedatectl.return_value = mock_lines
        
        extracted_time = RTC._extract_time(mock_lines, "RTC time:")
        assert isinstance(extracted_time, datetime.datetime)
        assert extracted_time.strftime("%H:%M:%S") == "14:30:45"

    def test_extract_time_no_match(self):
        mock_lines = ["No time here"]
        with pytest.raises(Exception):
            RTC._extract_time(mock_lines, "RTC time:")

    @patch('sentinel_mrhat_cam.RTC._get_timedatectl')
    def test_find_line_success(self, mock_get_timedatectl):
        mock_lines = [
            "System clock synchronized: yes",
            "Other line"
        ]
        result = RTC._find_line(mock_lines, "System clock synchronized:")
        assert result == "yes"

    def test_find_line_not_found(self):
        mock_lines = ["Some other line"]
        with pytest.raises(StopIteration):
            RTC._find_line(mock_lines, "Not found")

    @patch('subprocess.run')
    def test_get_timedatectl_success(self, mock_subprocess_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Line 1\nLine 2"
        mock_subprocess_run.return_value = mock_result
        
        result = RTC._get_timedatectl()
        assert result == ["Line 1", "Line 2"]
        mock_subprocess_run.assert_called_once_with(['timedatectl'], capture_output=True, text=True)

    @patch('subprocess.run')
    def test_get_timedatectl_failure(self, mock_subprocess_run):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error message"
        mock_subprocess_run.return_value = mock_result
        
        with pytest.raises(Exception, match="Error getting date from timedatectl"):
            RTC._get_timedatectl()

    @patch('subprocess.run')
    def test_sync_RTC_to_system(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        RTC._sync_RTC_to_system()
        mock_subprocess_run.assert_called_once_with(['sudo', 'hwclock', '--systohc'], check=True)

    @patch('subprocess.run')
    def test_sync_RTC_to_system_failure(self, mock_subprocess_run):
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, 'hwclock')
        with pytest.raises(subprocess.CalledProcessError):
            RTC._sync_RTC_to_system()

    @patch('sentinel_mrhat_cam.RTC._get_timedatectl')
    @patch('sentinel_mrhat_cam.RTC._find_line')
    def test_sync_system_to_ntp_success(self, mock_find_line, mock_get_timedatectl):
        mock_get_timedatectl.return_value = ["mock lines"]
        mock_find_line.return_value = "yes"
        
        result = RTC._sync_system_to_ntp(max_retries=1)
        assert result is True

    @patch('sentinel_mrhat_cam.RTC._get_timedatectl')
    @patch('sentinel_mrhat_cam.RTC._find_line')
    @patch('time.sleep')
    def test_sync_system_to_ntp_failure(self, mock_sleep, mock_find_line, mock_get_timedatectl):
        mock_get_timedatectl.return_value = ["mock lines"]
        mock_find_line.return_value = "no"
        
        with pytest.raises(SystemExit):
            RTC._sync_system_to_ntp(max_retries=1)


    @patch('sentinel_mrhat_cam.RTC._get_timedatectl')
    @patch('sentinel_mrhat_cam.RTC._extract_time')
    def test_get_time_no_sync(self, mock_extract_time, mock_get_timedatectl):
        # Mock times with a difference less than 2 seconds
        rtc_time = datetime.datetime(2024, 11, 15, 14, 30, 0)
        utc_time = datetime.datetime(2024, 11, 15, 14, 30, 1)
        
        mock_get_timedatectl.return_value = ["mock lines"]
        mock_extract_time.side_effect = [rtc_time, utc_time]
        
        time_str = RTC.get_time()
        assert time_str == "14:30:01"