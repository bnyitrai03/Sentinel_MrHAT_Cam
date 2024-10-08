# python 3.11
from paho.mqtt import client as mqtt_client
import base64
import logging
import json
from PIL import Image
import io
from datetime import datetime
from dateutil import parser
import pytz
from sentinel_mrhat_cam import BROKER

start_time = None

broker = BROKER
port = 1883
topic = "mqtt/rpi/image"
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.StreamHandler()])

logging.Formatter.converter = lambda *args: datetime.now(pytz.utc).timetuple()


def connect_mqtt() -> mqtt_client.Client:
    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}")

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
    client.enable_logger()
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


# Variable to store the time when the image is received
start_time = None


def subscribe(client: mqtt_client.Client):
    def on_message(client, userdata, msg):
        global start_time
        received_time = datetime.now(pytz.utc)
        time_difference = received_time - start_time
        logging.info(f"Time taken to receive: {time_difference.total_seconds():.2f} seconds")

        try:
            # Parse the JSON message
            payload = json.loads(msg.payload)

            # Extract timestamp and image data
            timestamp_str = payload['timestamp']
            image_base64 = payload['image']
            cpu_temp = payload['cpuTemp']
            battery_temp = payload['batteryTemp']
            battery_percentage = payload['batteryCharge']

            # Parse the timestamp string
            timestamp = parser.isoparse(timestamp_str)

            # Decode the Base64 image data
            image_data = base64.b64decode(image_base64)

            # Create a timestamp string for filenames
            time_string = timestamp.strftime("%Y%m%d_%H%M%S")

            # Save directly to a file
            output_image_path = f"images/image_{time_string}.jpg"
            with open(output_image_path, "wb") as f:
                f.write(image_data)
            logging.info(f"Received and saved image as {output_image_path}")

            # Load into a PIL Image object (for metadata or future processing if needed)
            image = Image.open(io.BytesIO(image_data))
            logging.info(f"Image size: {image.size}")

            delay = (received_time - timestamp).total_seconds()
            logging.info(f"Image timestamp: {timestamp_str}")
            logging.info(f"Time received: {received_time}")
            logging.info(f"Delay: {delay:.2f} seconds")

            logging.info(f"The cpu temperature is: {cpu_temp} °C")
            logging.info(f"The battery temperature is: {battery_temp} °C")
            logging.info(f"The battery percentage is: {battery_percentage} %")

        except Exception as e:
            logging.error(f"Failed to process image: {e}")
            logging.error(f"Payload: {msg.payload[:100]}...")

    client.subscribe(topic)
    client.on_message = on_message


def run():
    global start_time
    client = connect_mqtt()
    start_time = datetime.now(pytz.utc)
    subscribe(client)
    client.loop_forever()


if __name__ == '__main__':
    run()
