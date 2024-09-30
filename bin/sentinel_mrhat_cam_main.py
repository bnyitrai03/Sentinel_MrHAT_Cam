#!/usr/bin/env python3

import logging
import shutil
import sys
from os import makedirs
from os.path import dirname, exists, isdir, join, basename
from pathlib import Path

from sentinel_mrhat_cam.app import App
from sentinel_mrhat_cam.logger import Logger
from sentinel_mrhat_cam.static_config import LOG_CONFIG_PATH, CONFIG_PATH, CONFIG_DIR


def main():
    """
    Main entry point for the application.
    This function initializes the logger, creates an instance of the App class,
    and runs the application based on the configured mode.
    The application can run in three modes:
    1. "always-on": Continuously takes pictures and sends them.
    2. "periodic": Sends images periodically based on the configured schedule.
    3. "single-shot": Takes one picture, sends it, and then exits the script.
    The function handles the initialization of logging, creates the App instance
    with the provided configuration, and manages the main execution loop based
    on the selected mode.
    In case of a SystemExit exception, it logs the exit reason, disconnects
    from MQTT, and exits the application with the provided exit code.
    Raises
    ------
    SystemExit
        If the application needs to exit due to an error or completion of its task.
    Notes
    -----
    This function is the entry point of the application when run as a script.
    It sets up all necessary components and manages the main execution flow.
    """

    # Setting up the configuration directory and copying the default configuration files if necessary
    _set_up_configuration()

    # Configuring and starting the logging
    logger = Logger(LOG_CONFIG_PATH)
    logger.start_logging()

    # Instantiating the Camera and MQTT objects with the provided configuration file
    app = App(CONFIG_PATH, logger)
    app.start()

    try:
        app.run()
        
    except SystemExit as e:
        logging.info(f"Exit code in main: {e.code}\n Exiting the application because: {e}")
        sys.exit(e.code)
    finally:
        app.mqtt.disconnect()
        logger.disconnect_mqtt()


def _set_up_configuration():
    """
    Set up the configuration directory and copy the default configuration files if necessary.
    This function creates the configuration directory if it does not exist and copies the default
    configuration files to the configuration directory if they do not exist. Will not overwrite existing files.
    Notes
    -----
    This function is called before the main function to ensure that the configuration files are
    available before the application starts.
    """

    # Setting the default configuration path
    default_config_dir = str(Path(dirname(__file__)).parent.absolute().joinpath('config'))

    # Ensuring configuration directory exists
    if not isdir(CONFIG_DIR):
        makedirs(CONFIG_DIR, exist_ok=True)

    # Copying the default configuration files to the config directory, if they do not exist
    if not exists(LOG_CONFIG_PATH):
        default_log_config = join(default_config_dir, basename(LOG_CONFIG_PATH))
        shutil.copy(default_log_config, LOG_CONFIG_PATH)
    if not exists(CONFIG_PATH):
        default_config = join(default_config_dir, basename(CONFIG_PATH))
        shutil.copy(default_config, CONFIG_PATH)


if __name__ == "__main__":
    main()
