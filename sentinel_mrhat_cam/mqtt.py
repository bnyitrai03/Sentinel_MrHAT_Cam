from abc import ABC, abstractmethod
import logging
import time
import shutil
from typing import Any
import json
import socket
import threading
try:
    from paho.mqtt import client as mqtt_client
    from paho.mqtt import enums as mqtt_enums
except ImportError:
    mqtt_client = None  # type: ignore
    mqtt_enums = None  # type: ignore
from .static_config import BROKER, CONFIGSUB_TOPIC, PORT, QOS, TEMP_CONFIG_PATH, CONFIG_PATH, USERNAME, PASSWORD, CONFIGACK_TOPIC, MAX_WAIT_TIME_FOR_CONFG


class ICommunication(ABC):
    @abstractmethod
    def connect(self) -> Any:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass
    
    @abstractmethod
    def send(self, message: str, topic: str) -> None:
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    def wait_for_config(self, message: str, topic: str) -> None:
        pass

    @abstractmethod
    def init_receive(self) -> None:
        pass


class MQTT(ICommunication):
    """
    A class to handle MQTT client operations.

    This class manages the connection to an MQTT broker, publishes messages,
    and handles incoming configuration messages.

    Attributes
    ----------
    _broker : str
        The IPv4 address of the MQTT broker.
    _broker_connect_counter : int
        A counter to track reconnection attempts.
    _subtopic : str
        The topic to subscribe to for the incoming configuration file.
    _port : int
        The port number for the MQTT broker connection.
    _qos : int
        The Quality of Service level for MQTT messages.
    client : mqtt_client.Client
        The MQTT client instance.
    config_received_event : threading.Event
        An event to signal when a new configuration is received.
    config_confirm_message : str
        A message to confirm the receipt of a new configuration.

    Notes
    ------
    - The MQTT broker connection is retried up to 20 times upon failure.
    - This class requires the `paho-mqtt` library to be installed.
    - The class uses configuration values from a `static_config` module, which should be present in the same package.
    """

    def __init__(self):
        self._broker: str = BROKER
        self._port: int = PORT
        self._qos: int = QOS
        self._subtopic: str = CONFIGSUB_TOPIC
        self._broker_connect_counter: int = 0
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
            self._broker_connect_counter += 1
            if self._broker_connect_counter == 20:
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

    def init_receive(self) -> None:
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

            print("\n Inside on_message \n")

            try:

                print(f"\nReceived message: {message.payload.decode()}")
                if message.payload.decode() == "config-ok":
                    self.config_confirm_message = "config-ok"
                    self.config_received_event.set()
                    return

                # Parse the JSON message
                config_data = json.loads(message.payload)
                Config.validate_config(config_data)

                # Write the validated JSON to the temp file
                with open(TEMP_CONFIG_PATH, "w") as temp_config:
                    json.dump(config_data, temp_config, indent=4)

                # Copy the file
                shutil.copyfile(TEMP_CONFIG_PATH, CONFIG_PATH)
                print(f"Config saved to {CONFIG_PATH}")
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
        print(f"Subscribed to topic: {self._subtopic}")

    def is_connected(self) -> bool:
        return self.client.is_connected()

    def send(self, message: str, topic: str) -> None:
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
            self.client.publish(topic, message, qos=self._qos)
            # msg_info.wait_for_publish(timeout=5)
        except Exception:
            print("Failed to publish")
            exit(1)

    def connect(self) -> None:
        """
        Connect to the MQTT broker.

        This method sets up various callbacks for connection events and
        attempts to establish a connection to the MQTT broker.

        Returns
        -------
        mqtt_client.Client
            The connected MQTT client instance.
        """
        try:
            def on_connect(client: Any, userdata: Any, flags: Any, reason_code: Any, properties: Any) -> None:
                if reason_code == 0:
                    logging.info("Connected to MQTT Broker!")
                else:
                    logging.error(f"Failed to connect, return code {reason_code}")

            # checking the connection to the broker in a blocking way
            self._broker_check()
            self.client.on_connect = on_connect
            self.client.username_pw_set(USERNAME, PASSWORD)
            self.client.disable_logger()

            self.client.connect(self._broker, self._port)
            # Resetting the counter after a successful connection
            self.broker_connect_counter = 0
            self.init_receive()
            self.client.loop_start()

        except Exception as e:
            logging.error(f"Error connecting to MQTT broker: {e}")
            exit(1)

    def disconnect(self) -> None:
        """
        Disconnect the MQTT client from the broker.

        This method stops the network loop and disconnects the client from the MQTT broker.
        """
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()

    def wait_for_config(self, uuid: str, topic: str) -> None:
        logging.info("Waiting for config")
        self.config_received_event.clear()
        self.send(uuid, topic)
        if self.config_received_event.wait(MAX_WAIT_TIME_FOR_CONFG):
            print("Config received")
        else:
            print("Timeout waiting for config")
            self.config_confirm_message = "config-nok | Timed out waiting for config"

        logging.info(f"config_confirm_message: {self.config_confirm_message}")
        self.send(self.config_confirm_message, CONFIGACK_TOPIC)
