from typing import Dict, Any
import logging
import json
from datetime import datetime
from .static_config import CONFIG_PATH, CONFIGACK_TOPIC
from .rtc import IRTC
from .mqtt import ICommunication


class Config:
    def __init__(self, mqtt: ICommunication):
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
        self._path: str = CONFIG_PATH
        self._data: dict[str, Any] = {}
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
            self._data.update(Config._get_default_data())
            self.active = self._set_active_config()
            logging.error("Loading config failed, using default config")

    def _check_for_new_config(self) -> None:
        pass

    @staticmethod
    def _get_default_data() -> Dict[str, Any]:
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
            with open(self._path, "r") as file:
                new_config: dict = json.load(file)

            self.validate_config(new_config)

            self._data.update(new_config)
            self._set_active_config()
            logging.info("Config loaded")

        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in the config file: {str(e)}")
            raise
        except FileNotFoundError as e:
            logging.error(f"Config file not found: {self._path} - {str(e)}")
            raise
        except Exception as e:
            logging.error(e)
            raise

    def _set_active_config(self) -> None:
        """
        Generate an active configuration based on the current time from RTC.
        Returns
        -------
        dict
            The active configuration with the current timing period at the top level.
        """
        current_time_str = IRTC.get_time()
        current_time = datetime.strptime(current_time_str, "%H:%M:%S").time()

        active_config = {
            "uuid": self._data["uuid"],
            "quality": self._data["quality"]
        }

        for timing in self._data['timing']:
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

    def validate_config(self, new_config) -> None:
        pass

    def _validate_period(self, period) -> None:
        pass

    def _validate_time_format(self, new_config) -> None:
        pass
