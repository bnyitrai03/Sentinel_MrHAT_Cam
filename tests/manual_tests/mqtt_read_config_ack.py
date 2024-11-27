from paho.mqtt import client as mqtt_client
import sys
import logging

sys.path.append('/home/bence/Sentinel_MrHAT_Cam')
from sentinel_mrhat_cam import BROKER, CONFIGACK_TOPIC, PORT

broker = BROKER
port = PORT
topic = CONFIGACK_TOPIC

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.StreamHandler()])


def connect_mqtt() -> mqtt_client.Client:
    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}")

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
    client.username_pw_set("er-edge", "admin")
    client.enable_logger()
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client.Client):
    def on_message(client, userdata, msg):
        print(f"Received message {msg.payload.decode()}")

    client.subscribe(topic)
    client.on_message = on_message


if __name__ == '__main__':
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()
