import json
import time
import os
import paho.mqtt.client as mqtt
import subprocess
import base64

# Config Paths
CONFIG_PATH = "/home/ali/AliByt/alibyt-server/apps_config.json"
SUBSCRIPTIONS_PATH = "/home/ali/AliByt/alibyt-server/database.json"
RENDERED_PATH = "/home/ali/AliByt/alibyt-server/rendered_images"

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

# Track last sent images
last_images = {}

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

def run_scheduler():
    """Runs the scheduler and renders new images before sending them."""
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

        print(f"Currently subscribed apps: {subscribed_apps}")  # Debugging print statement

        for app in subscribed_apps:
            if app not in apps:
                print(f"Skipping {app} - Not found in config!")  # Debugging print
                continue

            app_info = apps[app]
            app_path = os.path.join(app_info["path"], app_info["app_name"])  # Path to Pixlet .star app
            output_path = os.path.join(RENDERED_PATH, app_info["photo_name"])  # Where the rendered image will be stored

            # Render Pixlet App
            rendered_image = render_pixlet_app(app, app_path, output_path)

            if rendered_image:
                # Get Base64-encoded image
                image_base64 = encode_image_to_base64(output_path)

                if image_base64:
                    # Only send if the image is different from the last one
                    if app not in last_images or last_images[app] != image_base64:
                        print(f"New image rendered for {app}, sending to client...")
                        last_images[app] = image_base64  # Update last image sent

                        # Send MQTT update with image data
                        client.publish(MQTT_TOPIC, json.dumps({
                            "app": app,
                            "image_data": image_base64,
                            "delete_old": True
                        }))

        time.sleep(1)  # Short sleep to prevent CPU overuse

if __name__ == "__main__":
    try:
        run_scheduler()
    except KeyboardInterrupt:
        print("Exiting MQTT publisher...")
