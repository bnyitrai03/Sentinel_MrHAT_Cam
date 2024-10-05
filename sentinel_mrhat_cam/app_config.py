from typing import List, Dict, Any
import logging
import json
from datetime import datetime
from .static_config import CONFIG_PATH
from .rtc import RTC


class Config:
    def __init__(self):
        self.data = dict()
        self._path: str = CONFIG_PATH
        self.active = dict()
        self.rtc = RTC()
        self.uuid: str = "8D8AC610-566D-4EF0-9C22-186B2A5ED793"

    def check_for_new_config(self) -> None:
        pass

    def get_default_config(self) -> Dict[str, Any]:
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
                new_config = json.load(file)

            self.validate_config(new_config)

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

    def get_active_config(self) -> Dict[str, Any]:
        """
        Generate an active configuration based on the current time from RTC.
        Returns
        -------
        dict
            The active configuration with the current timing period at the top level.
        """
        current_time_str = self.rtc.get_time()
        current_time = datetime.strptime(current_time_str, "%H:%M:%S").time()

        active_config = {
            "uuid": self.data["uuid"],
            "quality": self.data["quality"]
        }

        for timing in self.data['timing']:
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

    def validate_period(self, period) -> None:
        pass

    def validate_time_format(self, new_config) -> None:
        pass
