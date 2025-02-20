import json
import time
import os
import paho.mqtt.client as mqtt
import subprocess
import base64
import threading
import random

# Config Paths
CONFIG_PATH = "/home/ali/AliByt/alibyt-server/apps_config.json"
SUBSCRIPTIONS_PATH = "/home/ali/AliByt/alibyt-server/database.json"
RENDERED_PATH = "/home/ali/AliByt/alibyt-server/rendered_images"
CACHE_PATH = "/home/ali/AliByt/alibyt-server/image_cache"  # Store old images

# Ensure directories exist
os.makedirs(RENDERED_PATH, exist_ok=True)
os.makedirs(CACHE_PATH, exist_ok=True)

# Load app configurations
with open(CONFIG_PATH, "r") as file:
    apps = json.load(file)

# MQTT setup
MQTT_BROKER = "192.168.2.48"
MQTT_TOPIC = "alibyt/images"
client = mqtt.Client()
client.connect(MQTT_BROKER)

# Track last sent images and timestamps
last_images = {}
last_executions = {}

def encode_image_to_base64(image_path):
    """Encodes the image file into a Base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        print(f"Error: File not found - {image_path}")
        return None

def render_pixlet_app(app_name, app_path, output_path):
    """Renders a Pixlet app and saves the WebP output."""
    try:
        subprocess.run(["pixlet", "render", app_path, "-o", output_path], check=True)
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error rendering {app_name}: {e}")
        return None

def process_app(app):
    """Runs a single app in its own thread, with retry on failures."""
    global last_images, last_executions

    app_info = apps[app]
    app_path = os.path.join(app_info["path"], app_info["app_name"])
    output_path = os.path.join(RENDERED_PATH, app_info["photo_name"])
    cache_path = os.path.join(CACHE_PATH, app_info["photo_name"])
    refresh_rate = app_info["refresh_rate"]

    while True:
        current_time = time.time()

        if app in last_executions and (current_time - last_executions[app] < refresh_rate):
            time.sleep(1)
            continue

        print(f"Rendering {app}...")

        retry_attempts = 3  # Retry up to 3 times if rendering fails
        success = False

        for attempt in range(retry_attempts):
            rendered_image = render_pixlet_app(app, app_path, output_path)

            if rendered_image:
                image_base64 = encode_image_to_base64(output_path)

                if image_base64:
                    # Compare new image with cached image
                    if os.path.exists(cache_path):
                        cached_base64 = encode_image_to_base64(cache_path)
                        if image_base64 == cached_base64:
                            print(f"No change in {app}, skipping update.")
                            last_executions[app] = current_time
                            success = True
                            break

                    os.replace(output_path, cache_path)

                    print(f"New image rendered for {app}, sending to client...")
                    last_images[app] = image_base64
                    last_executions[app] = current_time

                    client.publish(MQTT_TOPIC, json.dumps({
                        "app": app,
                        "image_data": image_base64,
                        "delete_old": True
                    }))
                    success = True
                    break
            else:
                print(f"Retry {attempt + 1}/{retry_attempts} for {app}...")
                time.sleep(random.randint(2, 5))  # Wait 2-5 seconds before retrying

        if not success:
            print(f"Failed to render {app} after {retry_attempts} attempts. Skipping.")
        
        time.sleep(1)  # Prevent CPU overload

def run_scheduler():
    """Runs the scheduler, creating threads for each app."""
    threads = []

    while True:
        try:
            with open(SUBSCRIPTIONS_PATH, "r") as f:
                subscriptions = json.load(f)
                subscribed_apps = set(subscriptions.get("subscribed_apps", []))
        except json.JSONDecodeError:
            print("Error: `database.json` is corrupted. Resetting to default.")
            subscribed_apps = set()
            with open(SUBSCRIPTIONS_PATH, "w") as f:
                json.dump({"subscribed_apps": []}, f, indent=4)

        for app in subscribed_apps:
            if app not in apps:
                print(f"Skipping {app} - Not found in config!")
                continue

            # Start a new thread for each app
            if app not in last_executions:
                thread = threading.Thread(target=process_app, args=(app,))
                thread.daemon = True
                thread.start()
                threads.append(thread)

        time.sleep(5)  # Give time for new apps to be detected

if __name__ == "__main__":
    try:
        run_scheduler()
    except KeyboardInterrupt:
        print("Exiting MQTT publisher...")
