import os
import logging

# Configuration file paths
CONFIG_DIR = '/home/admin/config'
LOG_CONFIG_PATH = os.path.join(CONFIG_DIR, 'sentinel_log_config.yaml')
CONFIG_PATH = os.path.join(CONFIG_DIR, 'sentinel_app_config.json')
TEMP_CONFIG_PATH = os.path.join(CONFIG_DIR, 'temp_config.json')
STATE_FILE_PATH = os.path.join(CONFIG_DIR, 'state_file.json')

# MQTT Configuration
""" BROKER = "192.168.0.105"
PORT = 1883
IMAGETOPIC = "mqtt/rpi/image"
CONFIGACKTOPIC = "er-edge/confirm"
CONFIGSUBTOPIC = "config/er-edge"
QOS = 2
USERNAME = "er-edge"
PASSWORD = "admin" """
UUID_TOPIC = "cam4/uuid"

# Prod topics
PORT = 1883
QOS = 2
BROKER = "37.220.137.22"
IMAGE_TOPIC = "sentinel/cam4"
CONFIGACK_TOPIC = "cam4/confirm"
CONFIGSUB_TOPIC = "settings/cam4"
USERNAME = "cam4"
PASSWORD = "rubin2024cam4"
LOGGING_TOPIC = "cam4/log"
LOG_LEVEL = logging.INFO

# App configuration
"""
if  `period` < **SHUTDOWN_THRESHOLD** :
    The device won't shut down, instead it will wait in the script.

if  `period` > **SHUTDOWN_THRESHOLD** :
    The device shuts down in between picture taking.
"""
SHUTDOWN_THRESHOLD = 40

"""
This is the default time in seconds that, the he Pi takes to shutdown, and then to boot again.
"""
DEFAULT_BOOT_SHUTDOWN_TIME = 30
TIME_TO_BOOT_AND_SHUTDOWN = 20

"""
This is the minimum value for `period` in seconds.
"""
MINIMUM_WAIT_TIME = 5

"""
This is the maximum value for `period` in seconds.
"""
MAXIMUM_WAIT_TIME = 10800
