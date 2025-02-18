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

# Image Queue
image_queue = []
current_index = 0
display_speed = 5  # Default 5 seconds per image


def download_image(url):
    """Downloads an image from a URL and returns a PIL Image object."""
    try:
        print(f"Downloading image from {url}...")
        response = requests.get(url, timeout=10)  # Set a timeout to prevent hanging
        response.raise_for_status()  # Raise error for failed requests
        return Image.open(BytesIO(response.content))
    except requests.RequestException as e:
        print(f"Error downloading image: {e}")
        return None


def on_message(client, userdata, message):
    """Handles incoming MQTT messages and updates the image queue."""
    global image_queue
    try:
        data = json.loads(message.payload)
        image_url = data.get("path")  # Now we expect a URL instead of a file path

        if image_url:
            image_queue.append(image_url)
            print(f"Added new image to queue: {image_url}")
        else:
            print("Invalid image URL received.")
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
    global current_index
    while True:
        if image_queue:
            print(f"Current Queue: {image_queue}")
            image_url = image_queue[current_index]
            print(f"Displaying Image: {image_url}")

            image = download_image(image_url)  # Fetch image from URL

            if image:
                try:
                    # Check if image is animated
                    if getattr(image, "is_animated", False):
                        total_frames = image.n_frames
                        frame_delay = display_speed / total_frames  # Frame timing
                        print(f"Animated WebP detected: {total_frames} frames, {frame_delay:.2f}s per frame.")

                        for frame in ImageSequence.Iterator(image):
                            frame = frame.convert("RGB").resize((matrix.width, matrix.height))
                            matrix.SetImage(frame)
                            time.sleep(frame_delay)  # Control animation speed

                        print(f"Finished animation for {image_url}, moving to next image.")
                    else:
                        # Display static image
                        image = image.convert("RGB").resize((matrix.width, matrix.height))
                        matrix.SetImage(image)
                        print(f"Successfully displayed: {image_url}")
                        time.sleep(display_speed)  # Sleep only for static images
                except Exception as e:
                    print(f"Error displaying image: {e}")
            else:
                print(f"Removing invalid image URL: {image_url}")
                image_queue.remove(image_url)  # Remove invalid images

            # Cycle to next image
            current_index = (current_index + 1) % len(image_queue) if image_queue else 0
        else:
            print("Image queue is empty!")
            time.sleep(1)  # Prevents excessive CPU usage


# Start Image Display Loop
try:
    display_images()
except KeyboardInterrupt:
    print("Exiting MQTT client...")
