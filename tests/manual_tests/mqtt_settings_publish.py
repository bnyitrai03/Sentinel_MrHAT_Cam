import json
from paho.mqtt import client as mqtt_client
import sys

sys.path.append('/home/bence/Sentinel_MrHAT_Cam')
from sentinel_mrhat_cam import BROKER, CONFIGSUB_TOPIC

broker = BROKER
port = 1883
topic = CONFIGSUB_TOPIC

# Path to your config.json file
config_path = "config/sentinel_app_config.json"


def connect_mqtt():
    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}")

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client):
    try:
        with open(config_path, 'r') as file:
            config_data = json.load(file)

        # Convert the JSON object to a string
        message = json.dumps(config_data)
        message = "config-ok"

        result = client.publish(topic, message, qos=2)
        result.wait_for_publish()
        status = result[0]
        if status == 0:
            print(f"Sent config to topic {topic}")
        else:
            print(f"Failed to send message to topic {topic}")
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
    except json.JSONDecodeError:
        print(f"Invalid JSON in the config file: {config_path}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)
    client.disconnect()
    client.loop_stop()


if __name__ == '__main__':
    run()
