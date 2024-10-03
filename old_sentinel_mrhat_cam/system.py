import subprocess
import logging
from datetime import datetime
from typing import List, Union, Any
import pytz
import time

try:
    from gpiozero import CPUTemperature
except ImportError:
    CPUTemperature = None


class System:
    """
    A class that provides abstraction to Raspbian commands which interact with the hardware.

    This class contains static methods for system operations such as shutdown,
    reboot, scheduling wake-up, and gathering hardware information.

    Notes
    -----
    - The class interacts with hardware components and raises exceptions if unable to access them.

    Examples
    --------
    >>> system = System()
    >>> cpu_temp = system.get_cpu_temperature()
    >>> print(f"Current CPU temperature: {cpu_temp}°C")
    """

    @staticmethod
    def shutdown() -> None:
        logging.info("Pi has been shut down")
        subprocess.run(['sudo', 'shutdown', '-h', 'now'])

    @staticmethod
    def reboot() -> None:
        logging.info("System will be rebooted")
        subprocess.run(['sudo', 'reboot'], check=True)

    # Still experimental, don't have the real API yet.
    @staticmethod
    def schedule_wakeup(wake_time: Union[str, int, float]) -> None:
        """
        Schedule a system wake-up at a specified time.

        Parameters
        ----------
        wake_time : str, int, float
            The time at which the system should wake up.

        Raises
        ------
        subprocess.CalledProcessError
            If the rtcwake command fails to execute.
        """
        try:

            logging.info(f"wake_time is: {wake_time}")

            if isinstance(wake_time, str):
                logging.info("inside isinstance(wake_time, str)")

                cmd = f"sudo mrhat-rtcwake -d rtc0 -t $(date +%s -d 'tomorrow {wake_time}')"

            elif isinstance(wake_time, (int, float)):
                cmd = f"sudo mrhat-rtcwake -d rtc0 -s {str(wake_time)}"
            else:
                raise ValueError("wake_time must be a str, int, or float")

            # Execute the command
            subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)

        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to set RTC wake-up alarm: {e}")
            logging.error(f"rtcwake error output: {e.stderr}")
            raise

    @staticmethod
    def get_cpu_temperature() -> float:
        """
        Get the current CPU temperature.

        Returns
        -------
        float
            The current CPU temperature in degrees Celsius.
        """
        cpu = CPUTemperature()
        return cpu.temperature  # type: ignore

    @staticmethod
    def get_battery_info() -> dict[str, Any]:
        """
        Get information about the battery status.

        This method uses the `upower` command-line tool to query the
        information about the lithium ion battery device. It extracts the temperature
        and charge percentage of the battery.

        Returns
        -------
        dict
            A dictionary containing the following keys:
            - `temperature` : float
                The current temperature of the battery in degrees Celsius.
            - `percentage` : int
                The current charge level of the battery as a percentage (0-100).

        Raises
        ------
        SystemExit
            If the method is unable to retrieve battery information. This could
            be due to various reasons such as:
            - The `upower` command is not available on the system.
            - The specified battery device is not found.

        Notes
        -----
        This method is hardware-specific and relies on the presence of a battery
        device at the path '/org/freedesktop/UPower/devices/battery_bq2562x_battery'.
        It may need to be modified for different hardware configurations.

        The method uses subprocess to run the `upower` command, which is common
        on Linux systems but may not be available on all platforms.

        Examples
        --------
        >>> battery_info = System.get_battery_info()
        >>> print(f"Battery temperature: {battery_info['temperature']}°C")
        >>> print(f"Battery charge: {battery_info['percentage']}%")
        """
        try:
            # Battery info is path dependant!!!!
            result = subprocess.run(
                ['upower', '-i', '/org/freedesktop/UPower/devices/battery_bq2562x_battery'],
                stdout=subprocess.PIPE,
                check=True,
            )
            info = result.stdout.decode('utf-8')

            battery_info: dict[str, Any] = {'temperature': None, 'percentage': None}

            for line in info.splitlines():
                if "temperature:" in line:
                    battery_info['temperature'] = float(line.split(":")[1].strip().split()[0])
                if "percentage:" in line:
                    battery_info['percentage'] = int(line.split(":")[1].strip().replace('%', ''))

            return battery_info

        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to get battery info: {e}")
            exit(1)

    @staticmethod
    def gather_hardware_info() -> Union[dict[str, Any], None]:
        """
        Collect comprehensive hardware information about the system.

        This method gathers detailed information about the battery, charger,
        and CPU temperature. It reads system files to obtain battery and charger
        data, and uses the get_cpu_temperature method to retrieve CPU temperature.
        This data is then saved to a file, which is the input of the Matlab plotting script.

        Returns
        -------
        dict or None
            If successful, returns a dictionary containing the following keys:
            - `timestamp` : str
                The current date and time in ISO 8601 format.
            - `cpu_temp` : float
                The current CPU temperature in degrees Celsius.
            - `battery_percentage` : int
                The current battery charge level as a percentage (0-100).
            - `battery_voltage_now` : float
                The current battery voltage in volts.
            - `battery_voltage_avg` : float
                The average battery voltage in volts.
            - `battery_current_now` : float
                The current battery current in amperes.
            - `battery_current_avg` : float
                The average battery current in amperes.
            - `charger_voltage_now` : float
                The current charger voltage in volts.
            - `charger_current_now` : float
                The current charger current in amperes.

            Returns None if unable to gather the hardware information.

        Notes
        -----
        This method is hardware-specific and relies on the presence of specific
        system files:
        - '/sys/class/power_supply/bq2562x-battery/uevent' for battery information
        - '/sys/class/power_supply/bq2562x-charger/uevent' for charger information

        It may need to be modified for different hardware configurations or
        operating systems.

        All voltage and current values are converted from microvolts/microamps
        to volts/amps for easier readability.

        Examples
        --------
        >>> hardware_info = System.gather_hardware_info()
        >>> if hardware_info:
        ...     print(f"CPU Temperature: {hardware_info['cpu_temp']}°C")
        ...     print(f"Battery Percentage: {hardware_info['battery_percentage']}%")
        ...     print(f"Battery Voltage: {hardware_info['battery_voltage_now']}V")
        >>> else:
        ...     print("Failed to gather hardware information")
        """
        try:
            # Get battery info
            battery_result = subprocess.run(
                ['cat', '/sys/class/power_supply/bq2562x-battery/uevent'], stdout=subprocess.PIPE, check=True
            )
            battery_info = battery_result.stdout.decode('utf-8')

            # Get charger info
            charger_result = subprocess.run(
                ['cat', '/sys/class/power_supply/bq2562x-charger/uevent'], stdout=subprocess.PIPE, check=True
            )
            charger_info = charger_result.stdout.decode('utf-8')

            # Parse the information
            battery_data = dict(line.split("=") for line in battery_info.strip().split("\n"))
            charger_data = dict(line.split("=") for line in charger_info.strip().split("\n"))

            # Get CPU temperature
            cpu_temp = System.get_cpu_temperature()

            # Prepare the log data
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "cpu_temp": cpu_temp,
                "battery_percentage": int(battery_data.get("POWER_SUPPLY_CAPACITY", "0")),
                "battery_voltage_now": int(battery_data.get("POWER_SUPPLY_VOLTAGE_NOW", "0")) / 1000000,
                "battery_voltage_avg": int(battery_data.get("POWER_SUPPLY_VOLTAGE_AVG", "0")) / 1000000,
                "battery_current_now": int(battery_data.get("POWER_SUPPLY_CURRENT_NOW", "0")) / 1000000,
                "battery_current_avg": int(battery_data.get("POWER_SUPPLY_CURRENT_AVG", "0")) / 1000000,
                "charger_voltage_now": int(charger_data.get("POWER_SUPPLY_VOLTAGE_NOW", "0")) / 1000000,
                "charger_current_now": int(charger_data.get("POWER_SUPPLY_CURRENT_NOW", "0")) / 1000000,
            }

            return log_data

        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to gather hardware info: {e}")
            return None


class RTC:
    """
    A class that handles Real-Time Clock (RTC) operations and system time synchronization.

    This class provides static methods for syncing the system time with NTP servers,
    syncing the RTC with the system time, and retrieving the current time.

    """

    @staticmethod
    def sync_RTC_to_system() -> None:
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
        except subprocess.CalledProcessError as e:
            logging.error(f"Error syncing RTC: {e}")

    @staticmethod
    def sync_system_to_ntp(max_retries: int = 5, delay: int = 2) -> bool:
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
            lines = RTC.get_timedatectl()
            is_synced = RTC.find_line(lines, "System clock synchronized:")
            if is_synced == "yes":
                return True

            logging.warning(f"Failed to sync system to NTP, retrying ({retry+1}/{max_retries})")
            time.sleep(delay)
            delay *= 2

        logging.error("Failed to sync system to NTP after maximum retries")
        exit(1)

    @staticmethod
    def convert_timestamp(timestamp: str) -> str:
        """
        Convert a timestamp string to ISO 8601 format.

        This method takes a timestamp string in a specific format and converts it
        to the ISO 8601 format. It handles UTC timezone and removes unnecessary
        parts of the input string.

        Parameters
        ----------
        timestamp : str
            The timestamp string to convert. Expected format is:
            "Day YYYY-MM-DD HH:MM:SS [UTC]", e.g., "Mon 2023-08-14 15:30:45 UTC".

        Returns
        -------
        str
            The timestamp converted to ISO 8601 format (YYYY-MM-DDTHH:MM:SS+00:00).

        Raises
        ------
        SystemExit
            If the method is unable to parse the input timestamp string.

        Notes
        -----
        - The method removes the 'UTC' part from the input string if present.
        - It ignores the day of the week in the input string.
        - The output is always in UTC timezone.

        Examples
        --------
        >>> iso_time = RTC.convert_timestamp("Mon 2023-08-14 15:30:45 UTC")
        >>> print(iso_time)
        '2023-08-14T15:30:45+00:00'
        """
        try:
            # Remove the 'UTC' part if it exists
            parts = timestamp.split()
            # if the last element is 'UTC' remove it
            if parts[-1] == 'UTC':
                timestamp = ' '.join(parts[:-1])
            # Parse the timestamp while ignoring the weekday and timezone
            parsed_time = datetime.strptime(timestamp, "%a %Y-%m-%d %H:%M:%S")
            # Localize to UTC
            utc_time = pytz.UTC.localize(parsed_time, None)
            return utc_time.isoformat()  # type: ignore
        except Exception as e:
            logging.error(f"Error parsing timestamp: {e}")
            exit(1)

    @staticmethod
    def get_timedatectl() -> List[str]:
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

    @staticmethod
    def find_line(lines: list[str], target_string: str) -> str:
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

    @staticmethod
    def get_time() -> str:
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
            lines = RTC.get_timedatectl()

            # Get the RTC time
            rtc_time_line = RTC.find_line(lines, "RTC time:")
            rtc_datetime = RTC.convert_timestamp(rtc_time_line)

            # Get the time from the system clock
            utc_time_line = RTC.find_line(lines, "Universal time:")
            utc_datetime = RTC.convert_timestamp(utc_time_line)

            # If the RTC time is different from the system clock, sync the RTC
            if rtc_datetime != utc_datetime:
                # Convert strings to datetime objects
                rtc = datetime.fromisoformat(rtc_datetime)
                utc = datetime.fromisoformat(utc_datetime)
                # Calculate the time difference in seconds
                time_diff = abs((utc - rtc).total_seconds())
                if time_diff > 2:
                    RTC.sync_system_to_ntp()
                    RTC.sync_RTC_to_system()
                    # Get the current time again after syncing
                    utc_time_line = RTC.find_line(lines, "Universal time:")
                    utc_datetime = RTC.convert_timestamp(utc_time_line)

            return utc_datetime

        except Exception as e:
            logging.error(f"Error reading system time: {e}")
            exit(1)
