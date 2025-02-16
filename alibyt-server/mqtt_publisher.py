import json
import time
import os
import paho.mqtt.client as mqtt
import hashlib
from PIL import Image

# Load config
config_path = os.path.expanduser("~/AliByt/alibyt-server/apps_config.json")
with open(config_path, "r") as file:
    apps = json.load(file)

# MQTT setup
MQTT_BROKER = "localhost"  # Change if using an external broker
MQTT_TOPIC = "alibyt/images"

client = mqtt.Client()
client.connect(MQTT_BROKER)

# Track last sent images
last_hashes = {}

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
        for app, settings in apps.items():
            image_path = os.path.expanduser(settings["path"])
            refresh_rate = settings["refresh_rate"]

            # Get current image hash
            current_hash = get_image_hash(image_path)

            if current_hash and (app not in last_hashes or last_hashes[app] != current_hash):
                print(f"New image detected for {app}, sending to client...")
                last_hashes[app] = current_hash  # Update last hash

                # Send MQTT update
                client.publish(MQTT_TOPIC, json.dumps({"app": app, "path": image_path}))

            time.sleep(refresh_rate)

try:
    run_scheduler()
except KeyboardInterrupt:
    print("Exiting MQTT publisher...")
