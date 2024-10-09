import logging
from paho.mqtt import client as mqtt_client
from sentinel_mrhat_cam import BROKER, IMAGE_TOPIC

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

broker = BROKER
port = 1883
topic = IMAGE_TOPIC


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logging.info("Connected to MQTT Broker!")
        client.subscribe(topic)
        logging.info(f"Subscribed to topic: {topic}")
    else:
        logging.error(f"Failed to connect, return code {rc}")


def on_message(client, userdata, msg):
    logging.info(f"Received message on topic {msg.topic}: {msg.payload.decode()}")


def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    logging.info(f"Subscribed with mid: {mid}, QoS: {granted_qos}")


def run():
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_subscribe = on_subscribe

    client.connect(broker, port)
    client.loop_forever()


if __name__ == '__main__':
    run()
