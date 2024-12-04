from typing import Dict, Any, List
import logging
import json
from datetime import datetime
from .static_config import CONFIG_PATH, CONFIGACK_TOPIC, MINIMUM_WAIT_TIME, MAXIMUM_WAIT_TIME
from .rtc import RTC
from .mqtt import ICommunication
import re


class Config:
    def __init__(self, mqtt: ICommunication):
        """
        Initializes the Config class with the given file path.

        The constructor attempts to load the configuration file. If any errors occur
        during loading, an error message is published to the MQTT broker, and the default
        configuration is loaded.

        Parameters
        ----------
        mqtt : ICommunication
            An instance of the MQTT communication interface.
        """
        self._path: str = CONFIG_PATH
        self._full_config: dict[str, Any] = {}
        self.active: dict[str, Any] = {}
        try:
            self.load()
        except Exception as e:
            # If there is an error during loading, publish an error message to the remote server
            logging.error(e)
            self.communication: ICommunication = mqtt
            self.communication.connect()
            self.communication.send(f"config-nok|{str(e)}", CONFIGACK_TOPIC)
            self.communication.disconnect()

            # Load the default config
            self._full_config.update(Config._get_default_config())
            self.active = self._set_active_config()
            logging.error("Loading config failed, using default config")

    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """
        Defines and returns a default configuration dictionary.

        Returns
        -------
        dict
            Default configuration as a dictionary.
        """
        default_config = {
            "uuid": "8D8AC610-566D-4EF0-9C22-186B2A5ED793",
            "quality": "4K",
            "timing": [
                {
                    "period": -1,
                    "start": "00:00:00",
                    "end": "07:00:00"
                },
                {
                    "period": 30,
                    "start": "07:00:00",
                    "end": "12:00:00"
                },
                {
                    "period": -1,
                    "start": "12:00:00",
                    "end": "15:00:00"
                },
                {
                    "period": 30,
                    "start": "15:00:00",
                    "end": "19:00:00"
                },
                {
                    "period": -1,
                    "start": "19:00:00",
                    "end": "23:59:59"
                }
            ]
        }
        return default_config

    def load(self) -> None:
        """
        Load the configuration from the `sentinel_app_config.json` file.

        If the file is successfully opened and read, the configuration
        data is validated and stored in the `data` attribute of the Config instance.

        If any errors occur during the loading process, appropriate error messages are
        logged, and the function raises the encountered exception.

        Raises
        ------
        json.JSONDecodeError
            If the configuration file contains invalid JSON format.
        FileNotFoundError
            If the configuration file is not found at the specified path.
        Exception
            If any other error occurs during the loading process.
        """
        try:
            with open(self._path, "r") as file:
                new_config: dict = json.load(file)

            Config.validate_config(new_config)

            self._full_config.update(new_config)
            self._set_active_config()
            logging.info("Config loaded")

        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in the config file: {str(e)}")
            raise json.JSONDecodeError
        except FileNotFoundError as e:
            logging.error(f"Config file not found: {self._path} - {str(e)}")
            raise FileNotFoundError
        except Exception as e:
            logging.error(e)
            raise

    def _set_active_config(self) -> None:
        """
        Generate an active configuration based on the current time from RTC.
        """
        try:
            current_time_str = RTC.get_time()
            if current_time_str is None:
                raise ValueError("RTC.get_time() returned None")

            current_time = datetime.strptime(current_time_str, "%H:%M:%S").time()

            active_config = {
                "uuid": self._full_config["uuid"],
                "quality": self._full_config["quality"]
            }

            for timing in self._full_config['timing']:
                start_time = datetime.strptime(timing['start'], "%H:%M:%S").time()
                end_time = datetime.strptime(timing['end'], "%H:%M:%S").time()

                if start_time <= current_time < end_time:
                    active_config.update({
                        "period": timing["period"],
                        "start": timing["start"],
                        "end": timing["end"]
                    })
                    break

            self.active = active_config

        except Exception as e:
            logging.error(f"Error in _set_active_config method: {e}")
            raise

    @staticmethod
    def validate_config(new_config: Dict[str, Any]) -> None:
        """
        Validates the new configuration dictionary against the expected structure and rules.

        Parameters
        ----------
        new_config : dict
            The configuration dictionary to be validated.

        Raises
        ------
        TypeError
            If the configuration is not a dictionary, or if any value types are incorrect.
        ValueError
            If the configuration structure is invalid, or if any values are out of allowed ranges.
        """
        if not isinstance(new_config, dict):
            raise TypeError("Config loaded from file is not a dictionary.")

        expected_keys = {"uuid", "quality", "timing"}
        if set(new_config.keys()) != expected_keys:
            raise ValueError("Config keys do not match expected structure.")

        Config._validate_uuid(new_config["uuid"])
        Config._validate_quality(new_config["quality"])
        Config._validate_timing(new_config["timing"])

    @staticmethod
    def _validate_uuid(uuid: str) -> None:
        """
        Validates the UUID in the configuration using a regular expression.

        Parameters
        ----------
        uuid : str
            The UUID to be validated.

        Raises
        ------
        ValueError
            If the UUID is invalid.
        """
        uuid_pattern = re.compile(
            r'^[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$', re.IGNORECASE)
        if not uuid_pattern.match(uuid):
            raise ValueError("Invalid UUID format in the config.")

    @staticmethod
    def _validate_quality(quality: str) -> None:
        """
        Validates the quality setting in the configuration.

        Parameters
        ----------
        quality : str
            The quality setting to be validated.

        Raises
        ------
        ValueError
            If the quality setting is invalid.
        """
        if quality not in ["4K", "3K", "HD"]:
            raise ValueError("Invalid quality specified in the config.")

    @staticmethod
    def _validate_timing(timing: List[Dict[str, Any]]) -> None:
        """
        Validates the timing settings in the configuration.

        Parameters
        ----------
        timing : List[Dict[str, Any]]
            The list of timing dictionaries to be validated.

        Raises
        ------
        ValueError
            If the timing settings are invalid.
        TypeError
            If the timing settings have incorrect types.
        """
        if not isinstance(timing, list):
            raise TypeError("Timing must be a list of dictionaries.")

        # Go over each item in the timing key-value pairs
        for interval in timing:
            if not isinstance(interval, dict):
                raise TypeError("Each timing interval must be a dictionary.")

            required_keys = {"period", "start", "end"}
            if set(interval.keys()) != required_keys:
                raise ValueError("Invalid keys in timing interval.")

            Config._validate_period(interval["period"])
            Config._validate_time_format(interval["start"])
            Config._validate_time_format(interval["end"])

            if interval["start"] >= interval["end"]:
                raise ValueError("Start time must be before end time in each interval.")

        Config._validate_interval_covarge(timing)

    @staticmethod
    def _validate_interval_covarge(timing: List[Dict[str, Any]]) -> None:
        """ Check if intervals cover full day without overlap
         Sort intervals by start time """
        sorted_intervals = sorted(timing, key=lambda i: i["start"])

        """  # Iterate through sorted intervals
         enumerate is used to get both the index and value in each iteration
         This allows us to easily check the first (i == 0) and last (i == len(sorted_intervals) - 1) intervals,
         as well as compare each interval with the next one (sorted_intervals[i+1]) """
        for i, interval in enumerate(sorted_intervals):
            if i == 0 and interval["start"] != "00:00:00":
                raise ValueError("First interval must start at 00:00:00")

            if i == len(sorted_intervals) - 1 and interval["end"] != "23:59:59":
                raise ValueError("Last interval must end at 23:59:59")

            # Check if current interval ends where next interval starts
            if i < len(sorted_intervals) - 1:
                if interval["end"] != sorted_intervals[i + 1]["start"]:
                    raise ValueError("Intervals must be contiguous")

    @staticmethod
    def _validate_period(period: int) -> None:
        """
        Validates the period value in the configuration.

        Parameters
        ----------
        period : int
            The time period to be validated.

        Raises
        ------
        TypeError
            If the period is not an integer.
        ValueError
            If the period is invalid (not -1 and not within allowed range).
        """
        if not isinstance(period, int):
            raise TypeError("Period must be an integer.")
        if period != -1 and (period < MINIMUM_WAIT_TIME or period > MAXIMUM_WAIT_TIME):
            raise ValueError(f"Period must be -1 or between {MINIMUM_WAIT_TIME} and {MAXIMUM_WAIT_TIME}.")

    @staticmethod
    def _validate_time_format(time: str) -> None:
        """
        Validates the time format in the configuration.

        Parameters
        ----------
        time : str
            The time string to be validated.

        Raises
        ------
        ValueError
            If the time format is invalid.
        """
        time_pattern = re.compile(r'^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$')
        if not time_pattern.match(time):
            raise ValueError(f"Invalid time format: {time}. Expected format: HH:MM:SS")
