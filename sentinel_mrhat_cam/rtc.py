from datetime import datetime
import logging
import re
import time
from abc import ABC, abstractmethod
from typing import List
import subprocess


class IRTC(ABC):
    @abstractmethod
    def get_time(self) -> str:
        pass


class RTC(IRTC):
    """
    A class that handles Real-Time Clock (RTC) operations and system time synchronization.

    This class provides static methods for syncing the system time with NTP servers,
    syncing the RTC with the system time, and retrieving the current time.

    """
    def _extract_time(self, lines: List[str], target_string: str) -> datetime:
        """
        Extract the time in HH:MM:SS format from the line containing the target string.

        Parameters
        ----------
        lines : list of str
            The output from the `timedatectl` command.
        target_string : str
            The string to search for in the lines (e.g., "RTC time:" or "Universal time:").

        Returns
        -------
        str
            The extracted time in HH:MM:SS format.

        Raises
        ------
        Exception
            If the time cannot be extracted from the line.
        """
        line = self._find_line(lines, target_string)
        # Define a regex pattern to match the time format HH:MM:SS
        pattern = r'(\d{2}:\d{2}:\d{2})'
        match = re.search(pattern, line)
        if match:
            time = match.group(1)
            return datetime.strptime(time, "%H:%M:%S")
        else:
            raise Exception(f"Unable to extract time from line: {line}")

    def _find_line(self, lines: list[str], target_string: str) -> str:
        """
        Find and return a specific line from `timedatectl` output.

        This method searches for a line containing the specified target string in the
        given list of lines from timedatectl output and returns the value
        associated with that line.

        Parameters
        ----------
        lines : list of str
            Lines of output from the timedatectl command.
        target_string : str
            The string to search for in the lines.

        Returns
        -------
        str
            The value associated with the target string, extracted from the found line.

        Raises
        ------
        StopIteration
            If no line containing the target string is found.

        Notes
        -----
        - The method assumes the line format is "Key: Value".
        - It returns the part after the first colon, stripped of leading/trailing whitespace.

        """
        found_line = next(line for line in lines if target_string in line)
        return found_line.split(': ', 1)[1].strip()

    def _get_timedatectl(self) -> List[str]:
        """
        Get output from the `timedatectl` command.

        This method executes the `timedatectl` command and returns its output as a list
        of strings, each representing a line of the output.

        Returns
        -------
        list of str
            Lines of output from the timedatectl command.

        Raises
        ------
        Exception
            If unable to execute the timedatectl command or if it returns a non-zero
            exit status.

        Notes
        -----
        - This method uses subprocess.run to execute the command.
        - The output is captured as text and split into lines.
        """
        result = subprocess.run(['timedatectl'], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Error getting date from timedatectl: {result.stderr}")
        return result.stdout.splitlines()

    def _sync_RTC_to_system(self) -> None:
        """
        Synchronize the RTC to the system clock.

        This method uses the `hwclock` command to set the hardware clock to the current
        system time. It requires sudo privileges to execute.

        Raises
        ------
        subprocess.CalledProcessError
            If the `hwclock` command fails to execute or returns a non-zero exit status.

        Notes
        -----
        - If an error occurs during synchronization, it logs an error message with details.
        - This operation is typically used to ensure the RTC maintains accurate time
        even when the system is powered off.
        """
        try:
            subprocess.run(['sudo', 'hwclock', '--systohc'], check=True)
            logging.info("RTC synced to system clock")
        except subprocess.CalledProcessError:
            raise

    def _sync_system_to_ntp(self, max_retries: int = 5, delay: int = 2) -> bool:
        """
        Synchronize the system clock to NTP server.

        This method attempts to synchronize the system clock with NTP servers. It uses
        the `timedatectl` command to check synchronization status and retries multiple
        times if synchronization fails.

        Parameters
        ----------
        max_retries : int, optional
            Maximum number of synchronization attempts. Default is 5.
        delay : int, optional
            Initial delay between retries in seconds. This delay doubles after each
            failed attempt. Default is 2 seconds.

        Returns
        -------
        bool
            True if synchronization is successful, False otherwise.

        Raises
        ------
        SystemExit
            If synchronization fails after the maximum number of retries.

        Notes
        -----
        - The method uses exponential backoff for retry delays.
        - It logs a warning message for each failed attempt.
        - If all retries fail, it logs an error message and exits the program.
        """
        for retry in range(max_retries):
            lines = self._get_timedatectl()
            is_synced = self._find_line(lines, "System clock synchronized:")
            if is_synced == "yes":
                return True

            logging.warning(f"Failed to sync system to NTP, retrying ({retry+1}/{max_retries})")
            time.sleep(delay)
            delay *= 2
        logging.error("Failed to sync system to NTP after maximum retries")
        exit(1)

    def get_time(self) -> str:
        """
        Get the current time, ensuring synchronization with NTP and RTC.

        This method retrieves the current time from the system, if the time is not synchronized
        with the hardware RTC, or with the NTP servers, the function attempts to synchronize them
        and then return the current time in ISO 8601 format.

        Returns
        -------
        str
            The current time in ISO 8601 format.

        Raises
        ------
        Exception
            If unable to read the system time or perform necessary operations.

        Notes
        -----
        - The method compares RTC time with system time and syncs if they differ by more than 2 seconds.
        - It uses NTP synchronization and updates the RTC if significant time difference is detected.
        """
        try:
            # Get all the lines from timedatectl output
            lines = self._get_timedatectl()

            rtc = self._extract_time(lines, "RTC time:")
            utc = self._extract_time(lines, "Universal time:")

            # If the RTC time is different from the system clock sync them
            if abs((utc - rtc).total_seconds()) > 2:
                self._sync_system_to_ntp()
                self._sync_RTC_to_system()
                # ask for the time again
                lines = self._get_timedatectl()
                utc = self._extract_time(lines, "Universal time:")

            return str(utc.strftime("%H:%M:%S"))

        except Exception as e:
            logging.error(f"Error reading system time: {e}")
            exit(1)
