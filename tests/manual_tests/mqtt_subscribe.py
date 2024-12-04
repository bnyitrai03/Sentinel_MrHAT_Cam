from paho.mqtt import client as mqtt_client
import base64
import logging
import json
import sys

sys.path.append('/home/bence/Sentinel_MrHAT_Cam')
from sentinel_mrhat_cam import BROKER

broker = BROKER
port = 1883
topic = "sentinel/cam1"
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.StreamHandler()])

# logging.Formatter.converter = lambda *args: datetime.now(pytz.utc).timetuple()


def connect_mqtt() -> mqtt_client.Client:
    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            logging.info("Connected to MQTT Broker!")
        else:
            logging.info(f"Failed to connect, return code {rc}")
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
    client.enable_logger()
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client.Client):
    def on_message(client, userdata, msg):
        try:
            message = json.loads(msg.payload)
            image_data = base64.b64decode(message['image'])
            output_image_path = f"images/image_{message['timestamp']}.jpg"
            with open(output_image_path, "wb") as f:
                f.write(image_data)
            logging.info(f"Received and saved image to {output_image_path}")
            logging.info(f"Message timestamp: {message['timestamp']}")
            logging.info(f"CPU temperature is: { message['cpuTemp']} °C")
            logging.info(f"Battery temperature is: {message['batteryTemp']} °C")
            logging.info(f"Battery percentage is: {message['batteryCharge']} %")
        except Exception as e:
            logging.error(f"Failed to process image: {e}")
    client.subscribe(topic)
    client.on_message = on_message


if __name__ == '__main__':
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()
