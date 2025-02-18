import json
import time
import os
import hashlib
import paho.mqtt.client as mqtt
from flask import Flask, send_from_directory
import subprocess

# Config Paths
CONFIG_PATH = "/home/aalibh4/AliByt/alibyt-server/apps_config.json"
SUBSCRIPTIONS_PATH = "/home/aalibh4/AliByt/alibyt-server/database.json"
RENDERED_PATH = "/home/aalibh4/AliByt/alibyt-server/rendered_images"
IMAGE_SERVER_PORT = 8081  # Port for serving images

# Ensure rendered_images directory exists
os.makedirs(RENDERED_PATH, exist_ok=True)

# Load app configurations
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
MQTT_BROKER = "192.168.2.48"
MQTT_TOPIC = "alibyt/images"

client = mqtt.Client()
client.connect(MQTT_BROKER)

# Flask app for hosting images
app = Flask(__name__)

@app.route("/images/<path:filename>")
def serve_image(filename):
    """ Serve images from the rendered directory. """
    return send_from_directory(RENDERED_PATH, filename)

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

def render_pixlet_app(app_name, app_path):
    """ Renders a Pixlet app and saves the WebP output. """
    output_path = os.path.join(RENDERED_PATH, f"{app_name}.webp")
    try:
        subprocess.run(["pixlet", "render", app_path, "-o", output_path], check=True)
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error rendering {app_name}: {e}")
        return None

def run_scheduler():
    """ Runs the scheduler and renders new images before sending them. """
    while True:
        # Reload subscriptions every cycle
        try:
            if os.path.exists(SUBSCRIPTIONS_PATH) and os.path.getsize(SUBSCRIPTIONS_PATH) > 0:
                with open(SUBSCRIPTIONS_PATH, "r") as f:
                    subscriptions = json.load(f)
                    subscribed_apps = set(subscriptions.get("subscribed_apps", []))
            else:
                subscribed_apps = set()
        except json.JSONDecodeError:
            print("Error: `database.json` is corrupted. Resetting to default.")
            subscribed_apps = set()
            with open(SUBSCRIPTIONS_PATH, "w") as f:
                json.dump({"subscribed_apps": []}, f, indent=4)

        current_time = time.time()
        print(f"Currently subscribed apps: {subscribed_apps}")  # Debugging print statement

        for app in subscribed_apps:
            if app not in apps:
                print(f"Skipping {app} - Not found in config!")  # Debugging print
                continue

            app_path = os.path.expanduser(apps[app]["path"])  # Path to Pixlet .star app
            refresh_rate = apps[app]["refresh_rate"]
            output_path = os.path.join(RENDERED_PATH, f"{app}.webp")  # Where the rendered image will be stored

            # Check if it's time to refresh this app
            if current_time - last_executions.get(app, 0) >= refresh_rate:
                print(f"Rendering app: {app}, Refresh Rate: {refresh_rate}s")
                last_executions[app] = current_time  # Update last execution time

                # Render Pixlet App
                rendered_image = render_pixlet_app(app, app_path)

                if rendered_image:
                    # Get current image hash
                    current_hash = get_image_hash(rendered_image)

                    if current_hash and (app not in last_hashes or last_hashes[app] != current_hash):
                        print(f"New image rendered for {app}, sending to client...")
                        last_hashes[app] = current_hash  # Update last hash

                        # Generate URL for hosted image
                        image_url = f"http://{MQTT_BROKER}:{IMAGE_SERVER_PORT}/images/{app}.webp"

                        # Send MQTT update
                        client.publish(MQTT_TOPIC, json.dumps({"app": app, "path": image_url}))

        time.sleep(1)  # Short sleep to prevent CPU overuse

if __name__ == "__main__":
    from threading import Thread

    # Run the Flask image server in a separate thread
    flask_thread = Thread(target=lambda: app.run(host="0.0.0.0", port=IMAGE_SERVER_PORT, debug=False))
    flask_thread.daemon = True
    flask_thread.start()

    try:
        run_scheduler()
    except KeyboardInterrupt:
        print("Exiting MQTT publisher...")
