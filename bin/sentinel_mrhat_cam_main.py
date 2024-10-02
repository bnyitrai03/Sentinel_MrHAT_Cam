#!/usr/bin/env python3

import time
import shutil
from os import makedirs
from os.path import dirname, exists, isdir, join, basename
from pathlib import Path
from sentinel_mrhat_cam.states import Context
from sentinel_mrhat_cam.logger import Logger
from sentinel_mrhat_cam.static_config import LOG_CONFIG_PATH, CONFIG_PATH, CONFIG_DIR


def main():
    """
    Main entry point for the application.
    This function initializes the logger, creates an instance of the Context class,
    and runs the application based on the configured mode.
    The application can run in two modes:
    1. Sends images periodically based on the configured schedule.
    2. The Pi shuts down in between sending the images.
    The function handles the initialization of logging, creates the App instance
    with the provided configuration, and manages the main execution loop based
    on the selected mode.

    Notes
    -----
    This function is the entry point of the application when run as a script.
    It sets up all necessary components and manages the main execution flow.
    """

    # Setting up the configuration directory and copying the default configuration files if necessary
    _set_up_configuration()

    # Configuring and starting the logging
    logger = Logger()
    logger.start_logging()

    app = Context(logger)
    while True:
        app.request()
        time.sleep(5)  # !!!


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
