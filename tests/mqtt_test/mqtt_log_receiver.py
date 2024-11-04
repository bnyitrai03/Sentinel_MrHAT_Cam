# log_receiver.py

from paho.mqtt import client as mqtt_client
import logging
import sys

sys.path.append('/home/bence/Sentinel_MrHAT_Cam')
from sentinel_mrhat_cam.static_config import BROKER, PORT, USERNAME, PASSWORD, LOGGING_TOPIC, QOS

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logging.info(f"Connected with result code {rc}")
        logging.info(f"Subscribing to topic: {LOGGING_TOPIC} with QoS: {QOS}")
        client.subscribe(LOGGING_TOPIC, qos=QOS)
        logging.info("Subscribed successfully")
    else:
        logging.error(f"Failed to connect, return code {rc}")


def on_message(client, userdata, msg):

    log_entry = msg.payload.decode()
    print(log_entry)


def connect_mqtt() -> mqtt_client.Client:
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)
    return client


def run():
    client = connect_mqtt()
    client.loop_forever()


if __name__ == "__main__":
    run()
