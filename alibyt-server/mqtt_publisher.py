import json
import time
import os
import paho.mqtt.client as mqtt
import hashlib
from PIL import Image

# File Paths
CONFIG_PATH = "/home/aalibh4/AliByt/alibyt-server/apps_config.json"
SUBSCRIPTIONS_PATH = "/home/aalibh4/AliByt/alibyt-server/database.json"

# Load config
with open(CONFIG_PATH, "r") as file:
    apps = json.load(file)

# Load subscribed apps with error handling
subscribed_apps = set()
try:
    if os.path.exists(SUBSCRIPTIONS_PATH) and os.path.getsize(SUBSCRIPTIONS_PATH) > 0:
        with open(SUBSCRIPTIONS_PATH, "r") as f:
            subscriptions = json.load(f)
            subscribed_apps = set(subscriptions.get("subscribed_apps", []))
    else:
        print("Warning: `database.json` is empty. Using default empty subscriptions.")
except json.JSONDecodeError:
    print("Error: `database.json` is corrupted. Resetting to default.")
    subscribed_apps = set()
    with open(SUBSCRIPTIONS_PATH, "w") as f:
        json.dump({"subscribed_apps": []}, f, indent=4)

# MQTT setup
MQTT_BROKER = "localhost"
MQTT_TOPIC = "alibyt/images"

client = mqtt.Client()
client.connect(MQTT_BROKER)

# Track last sent images and execution times
last_hashes = {}
last_executions = {app: 0 for app in subscribed_apps}  # Track when each app last ran

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

        for app in subscribed_apps:  # Only process subscribed apps
            if app not in apps:
                continue  # Skip if the app is not in config

            image_path = os.path.expanduser(apps[app]["path"])
            refresh_rate = apps[app]["refresh_rate"]

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
