import json
import time
import os
import paho.mqtt.client as mqtt
import hashlib
from PIL import Image

# Load config
CONFIG_PATH = "/home/aalibh4/AliByt/alibyt-server/apps_config.json"
with open(CONFIG_PATH, "r") as file:
    apps = json.load(file)

# MQTT setup
MQTT_BROKER = "localhost"  # Change if using an external broker
MQTT_TOPIC = "alibyt/images"

client = mqtt.Client()
client.connect(MQTT_BROKER)

# Track last sent images and last execution times
last_hashes = {}
last_executions = {app: 0 for app in apps}  # Track when each app last ran

def get_image_hash(image_path):
    """ Returns a hash of the image file to detect changes. """
    try:
        with open(image_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except FileNotFoundError:
        return None

def run_scheduler():
    """ Runs the scheduler and sends new images only when they change. """
    while True:
        current_time = time.time()

        for app, settings in apps.items():
            image_path = os.path.expanduser(settings["path"])
            refresh_rate = settings["refresh_rate"]

            # Check if it's time to refresh this app
            if current_time - last_executions[app] >= refresh_rate:
                last_executions[app] = current_time  # Update last execution time

                # Get current image hash
                current_hash = get_image_hash(image_path)

                if current_hash and (app not in last_hashes or last_hashes[app] != current_hash):
                    print(f"New image detected for {app}, sending to client...")
                    last_hashes[app] = current_hash  # Update last hash

                    # Send MQTT update
                    client.publish(MQTT_TOPIC, json.dumps({"app": app, "path": image_path}))

        time.sleep(1)  # Short sleep to prevent CPU overuse

try:
    run_scheduler()
except KeyboardInterrupt:
    print("Exiting MQTT publisher...")
