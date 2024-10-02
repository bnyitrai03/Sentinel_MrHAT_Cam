import logging
import json
import re
from typing import Any

from .mqtt import MQTT
from .static_config import CONFIGACKTOPIC, MINIMUM_WAIT_TIME, MAXIMUM_WAIT_TIME


class Config:
    """
    A class to handle configuration loading and validation..

    Parameters
    ----------
    path : str
        Path to the configuration file.

    Attributes
    ----------
    path : str
        Path to the configuration file.
    data : dict
        Dictionary to store the configuration data.
    """

    def __init__(self, path: str) -> None:
        """
        Initializes the Config class with the given file path.

        The constructor attempts to load the configuration file. If any errors occur
        during loading, an error message is published to the MQTT broker, and the default
        configuration is loaded.

        Parameters
        ----------
        path : str
            Path to the configuration file.
        """
        self.path = path
        self.data = dict()  # Empty dictionary to store the config data
        try:
            # Load the config file with validation
            self.load()
        except Exception as e:
            # If there is an error during loading, publish an error message to the MQTT broker
            logging.error(e)
            mqtt = MQTT()
            mqtt.connect()
            mqtt.publish(f"config-nok|{str(e)}", CONFIGACKTOPIC)
            mqtt.disconnect()

            # Load the default config
            self.data.update(Config.get_default_config())
            logging.error("Loading config failed, using default config")

    def load(self) -> None:
        """
        Load the configuration from the `sentinel_app_config.json` file.

        If the file is successfully opened and read, the configuration
        data is validated and stored in the `data` attribute of the Config instance.

        If any errors occur during the loading process, appropriate error messages are
        logged, and the function raises the encountered exception.

        Parameters
        ----------
        None

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
            with open(self.path, "r") as file:
                new_config = json.load(file)

            Config.validate_config(new_config)

            self.data.update(new_config)

        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in the config file: {str(e)}")
            raise
        except FileNotFoundError as e:
            logging.error(f"Config file not found: {self.path} - {str(e)}")
            raise
        except Exception as e:
            logging.error(e)
            raise

    @staticmethod
    def get_default_config() -> dict[str, Any]:
        """
        Defines and returns a default configuration dictionary.

        Returns
        -------
        dict
            Default configuration as a dictionary.
        """
        default_config = {
            "quality": "3K",
            "mode": "periodic",
            "period": 15,
            "wakeUpTime": "06:59:31",
            "shutDownTime": "22:00:00",
        }
        return default_config

    @staticmethod
    def validate_config(new_config: dict[str, Any]) -> None:
        """
        Validates the new configuration dictionary against the default configuration
        and checks if specific rules are fulfilled.

        This function checks if the provided configuration dictionary matches the expected structure
        and values. It raises appropriate exceptions if any validation checks fail.

        Parameters
        ----------
        new_config : dict
            The configuration dictionary to be validated.

        Raises
        ------
        TypeError
            If the configuration is not a dictionary, or if the period is not an integer,
            or if the wake-up or shut-down time formats are invalid.
        ValueError
            If the configuration keys do not match the default configuration keys,
            or if the quality or mode values are invalid,
            or if the period is outside the allowed range.
        """
        default_config = Config.get_default_config()

        if not isinstance(new_config, dict):
            raise TypeError("Config loaded from file is not a dictionary.")

        if default_config.keys() != new_config.keys():
            raise ValueError("Config keys do not match.")

        if new_config["quality"] not in ["4K", "3K", "HD"]:
            raise ValueError("Invalid quality specified in the config.")

        if new_config["mode"] not in ["periodic", "single-shot", "always-on"]:
            raise ValueError("Invalid mode specified in the config.")

        if new_config["mode"] == "periodic":
            Config.validate_period(new_config["period"])

        Config.validate_time_format(new_config)

    @staticmethod
    def validate_period(period: int) -> None:
        """
        Validates the period value in the new configuration dictionary.

        Parameters
        ----------
        period : int
            The time period to be validated.

        Raises
        ------
        TypeError
            If the period specified in the config is not an integer.
        ValueError
            If the period specified in the config is less than the minimum allowed wait time,
            or if it is more than the maximum allowed wait time.
        """
        if not isinstance(period, int):
            raise TypeError("Period specified in the config is not an integer.")
        if period < MINIMUM_WAIT_TIME:
            raise ValueError("Period specified in the config is less than the minimum allowed wait time.")
        if period > MAXIMUM_WAIT_TIME:
            raise ValueError("Period specified in the config is more than the maximum allowed wait time.")

    @staticmethod
    def validate_time_format(new_config: dict[str, Any]) -> None:
        """
        Validates the wake-up and shut-down time formats in the new configuration dictionary.

        Parameters
        ----------
        new_config : dict
            The configuration dictionary which contains the shut-down and wake-up time.

        Raises
        ------
        TypeError
            If the wake-up time or shut-down time format in the config is invalid.
        """
        # REGEX: hh:mm:ss
        time_pattern = re.compile(r'^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$')
        if bool(time_pattern.match(new_config["wakeUpTime"])) is False:
            raise TypeError("Invalid wake-up time format in the config.")
        if bool(time_pattern.match(new_config["shutDownTime"])) is False:
            raise TypeError("Invalid shut-down time format in the config.")
