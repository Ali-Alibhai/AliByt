import json
import os
import time
import requests
import paho.mqtt.client as mqtt
from io import BytesIO
from PIL import Image, ImageSequence
from rgbmatrix import RGBMatrix, RGBMatrixOptions

# MQTT Setup
MQTT_BROKER = "192.168.2.48"
MQTT_TOPIC = "alibyt/images"

# Matrix Setup
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.hardware_mapping = 'adafruit-hat'
options.gpio_slowdown = 2
matrix = RGBMatrix(options=options)

# Image Storage
CACHE_DIR = "/home/aalibh4/alibyt-client/image_cache"
os.makedirs(CACHE_DIR, exist_ok=True)  # Ensure cache directory exists

# Image Queue (Dictionary for easy replacement)
image_queue = {}
current_image = None  # Track the currently displayed app
display_speed = 5  # Default 5 seconds per image


def get_cached_path(app_name):
    """Returns the local path where the image for a given app should be stored."""
    return os.path.join(CACHE_DIR, f"{app_name}.webp")


def download_image(image_data, app_name):
    """Decodes and saves Base64 image data only if it's new."""
    local_path = get_cached_path(app_name)

    try:
        # Decode and save image
        with open(local_path, "wb") as f:
            f.write(image_data)
        return local_path
    except Exception as e:
        print(f"Error saving image for {app_name}: {e}")
        return None


def on_message(client, userdata, message):
    """Handles incoming MQTT messages and updates the image queue."""
    global image_queue
    try:
        data = json.loads(message.payload)
        app_name = data.get("app")
        image_data = data.get("image_data")
        delete_old = data.get("delete_old", False)

        if app_name and image_data:
            # Replace or delete existing image
            if delete_old and app_name in image_queue:
                os.remove(get_cached_path(app_name))  # Delete old file
                print(f"Deleted old image for {app_name}")

            # Store new image
            local_path = download_image(base64.b64decode(image_data), app_name)
            if local_path:
                image_queue[app_name] = local_path
                print(f"Updated queue: {app_name} -> {local_path}")
        else:
            print("Invalid app name or image data received.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")


# MQTT Client Setup
client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER)
client.subscribe(MQTT_TOPIC)
client.loop_start()


def display_images():
    """Loops through image queue and displays them, handling animated WebP images."""
    global current_image
    while True:
        if image_queue:
            app_names = list(image_queue.keys())  # Get the list of apps in queue
            for app_name in app_names:
                image_path = image_queue[app_name]
                print(f"Displaying Image for {app_name}: {image_path}")

                try:
                    image = Image.open(image_path)  # Load image from cache
                    
                    # Check if image is animated
                    if getattr(image, "is_animated", False):
                        total_frames = image.n_frames
                        frame_delay = display_speed / total_frames  # Frame timing
                        print(f"Animated WebP detected: {total_frames} frames, {frame_delay:.2f}s per frame.")

                        for frame in ImageSequence.Iterator(image):
                            frame = frame.convert("RGB").resize((matrix.width, matrix.height))
                            matrix.SetImage(frame)
                            time.sleep(frame_delay)  # Control animation speed

                        print(f"Finished animation for {image_path}, moving to next image.")
                    else:
                        # Display static image
                        image = image.convert("RGB").resize((matrix.width, matrix.height))
                        matrix.SetImage(image)
                        print(f"Successfully displayed: {image_path}")
                        time.sleep(display_speed)  # Sleep only for static images
                except Exception as e:
                    print(f"Error displaying image: {e}")
                    del image_queue[app_name]  # Remove invalid images

        else:
            print("Image queue is empty!")
            time.sleep(1)  # Prevents excessive CPU usage


# Start Image Display Loop
try:
    display_images()
except KeyboardInterrupt:
    print("Exiting MQTT client...")
