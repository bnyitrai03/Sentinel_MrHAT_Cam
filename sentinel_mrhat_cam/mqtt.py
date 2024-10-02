from abc import ABC, abstractmethod
import logging
import time
import shutil
from typing import Any

try:
    from paho.mqtt import client as mqtt_client
    from paho.mqtt import enums as mqtt_enums
except ImportError:
    mqtt_client = None  # type: ignore
    mqtt_enums = None  # type: ignore

from .static_config import BROKER, CONFIGSUB_TOPIC, PORT, QOS, TEMP_CONFIG_PATH, CONFIG_PATH, USERNAME, PASSWORD

import json
import socket
import threading


class ICommunication(ABC):
    @abstractmethod
    def connect(self) -> Any:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def init(self) -> None:
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    def send(self, message: str, topic: str) -> None:
        pass

    @abstractmethod
    def wait_for_acknowledge(self, topic: str) -> None:
        pass


class MQTT(ICommunication):
    def __init__(self):
        self._broker: str = BROKER
        self._port: int = PORT
        self._qos: int = QOS
        self._subtopic: str = CONFIGSUB_TOPIC
        self.broker_connect_counter: int = 0
        self.client = mqtt_client.Client(mqtt_enums.CallbackAPIVersion.VERSION2)
        self.config_confirm_message: str = "config-nok|Confirm message uninitialized"
        self.config_received_event: threading.Event = threading.Event()

    def _broker_check(self) -> None:
        """
        Continuously checks the connection to the MQTT broker until it becomes available.

        This method repeatedly checks the availability of the MQTT broker by calling the
        `is_broker_available` method. It uses a counter to track the number of connection attempts.

        The process flow is as follows:
        - Wait for 0.5 seconds between each connection attempt.
        - Increment the connection attempt counter after each wait period.
        - If the connection is not established within 20 attempts, log an error and terminate the program.

        Attributes:
        ----------
        broker_connect_counter : int
            A counter that tracks the number of attempts made to connect to the broker.
            It is incremented with each failed attempt.

        Methods:
        -------
        is_broker_available() -> bool:
            Checks if the MQTT broker is available by attempting a socket connection.

        Logs:
        -----
        Logs the following messages:
        - INFO: Indicates that the connection attempt is in progress.
        - ERROR: If the broker is not available after 20 attempts, it logs an error before exiting.

        Raises:
        -------
        SystemExit:
            Terminates the script if the broker connection fails 20 times.
        """
        while not self._is_broker_available():
            logging.info("Waiting for broker to become available...")
            time.sleep(1)
            self.broker_connect_counter += 1
            if self.broker_connect_counter == 20:
                logging.error("Connecting to network failed 20 times, restarting script...")
                exit(1)

    def _is_broker_available(self) -> bool:
        """
        Checks if the MQTT broker is reachable by attempting to establish a socket connection.

        This method tries to create a TCP connection to the MQTT broker using the `socket` module.
        If the connection is successful, it returns `True`, indicating that the broker is available.
        If an `OSError` is raised (typically due to network issues or the broker being down),
        the method returns `False`. Any other unexpected exception results in logging the error
        and exiting the script.

        Methods:
        -------
        socket.create_connection((host, port), timeout) -> socket:
            Attempts to create a connection to the broker.

        Logs:
        -----
        Logs the following message:
        - ERROR: Logs any unexpected error during the connection attempt before terminating the script.

        Returns:
        -------
        bool:
            `True` if the broker is available, `False` otherwise.

        Raises:
        -------
        SystemExit:
            Exits the script if an unexpected error occurs during the connection attempt.
        """
        try:
            socket.create_connection((BROKER, PORT), timeout=5)
            return True
        except OSError:
            return False
        except Exception as e:
            logging.error(f"Error during creating connection: {e}")
            exit(1)

    def _publish(self, message: str, topic: str) -> None:
        """
        Publishes a message to a specified MQTT topic.

        This method sends a message to the MQTT broker to be published on a specified topic.
        It uses the MQTT client to publish the message with QoS = 2.
        The method waits for the message (max 5 seconds) to be published and handles any errors that might occur during
        the publishing process.

        Parameters:
        ----------
        message : str
            The payload to be published to the MQTT topic.

        topic : str
            The topic string to which the message should be published.

        Methods:
        -------
        client.publish(topic, message, qos) -> MQTTMessageInfo:
            Sends a message to the broker on the specified topic.

        msg_info.wait_for_publish(timeout) -> None:
            Blocks until the message publishing is acknowledged or the 5 second time limit is met.

        Raises:
        -------
        SystemExit:
            Exits the script if an error occurs during the publishing process.
        """
        try:
            msg_info = self.client.publish(topic, message, qos=self._qos)
            msg_info.wait_for_publish(timeout=5)
        except Exception:
            exit(1)

    def _init(self) -> None:
        """
        Initializes the MQTT client to receive the config file.

        This function sets up the MQTT client's `on_message` callback to handle the incoming config.
        When a config is received, it attempts to parse it as a JSON, validate it,
        and save it to a temporary file. If successful, the configuration is copied to the final
        configuration path, and a confirmation message is set. If an error occurs, an appropriate
        error message is set.
        """

        def on_message(client: Any, userdata: Any, message: Any) -> None:
            from .app_config import Config

            try:
                # Parse the JSON message
                config_data = json.loads(message.payload)
                Config.validate_config(config_data)

                # Write the validated JSON to the temp file
                with open(TEMP_CONFIG_PATH, "w") as temp_config:
                    json.dump(config_data, temp_config, indent=4)

                # Copy the file
                shutil.copyfile(TEMP_CONFIG_PATH, CONFIG_PATH)
                logging.info(f"Config saved to {CONFIG_PATH}")
                self.config_confirm_message = "config-ok"

            except json.JSONDecodeError as e:
                self.config_confirm_message = f"config-nok|Invalid JSON received: {e}"
                logging.error(f"Invalid JSON received: {e}")
            except Exception as e:
                self.config_confirm_message = f"config-nok| {e}"
                logging.error(f"Error processing message: {e}")
            finally:
                self.config_received_event.set()

        self.client.on_message = on_message
        self.client.subscribe(self._subtopic)

    def _reset_config_received_event(self) -> None:
        self.config_received_event.clear()

    def init(self) -> None:
        pass

    def is_connected(self) -> bool:
        return self.client.is_connected() if self.client else False

    def send(self, message: str, topic: str) -> None:
        """
        Sends the message over MQTT.

        This method orchestrates the entire process of capturing an image, gathering
        system data, creating a message, and transmitting it to a predefined MQTT topic.
        If the MQTT client is not already connected, the method attempts to establish
        the connection in a blocking manner to ensure the message is sent successfully.

        Raises
        ------
        Exception
            If any error occurs during the process, whether it be in capturing the image,
            creating the message, or transmitting it via MQTT. The exception is logged,
            and the error is re-raised.

        Notes
        -----
        - The method ensures that the MQTT client is connected before attempting to
        publish the message.
        - If MQTT logging is not already initialized, the method triggers its start
        to ensure that all communication is logged appropriately.
        - This method is decorated with `@log_execution_time`, which logs the time
        taken to execute the method.
        """

        if not self.is_connected():
            self.connect()

        self._publish(message, topic)

    def connect(self) -> Any:
        self._broker_check()

    def disconnect(self) -> None:
        """
        Disconnect the MQTT client from the broker.

        This method stops the network loop and disconnects the client from the MQTT broker.
        """
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()

    def wait_for_acknowledge(self, topic: str) -> None:
        # Read paho, how to wait for sub ... TODO
        pass
