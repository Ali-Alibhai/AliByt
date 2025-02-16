import json
import os
import time
import paho.mqtt.client as mqtt
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image

# MQTT setup
MQTT_BROKER = "localhost"
MQTT_TOPIC = "alibyt/images"

# Matrix setup
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.hardware_mapping = 'adafruit-hat'
options.gpio_slowdown = 2

matrix = RGBMatrix(options=options)

# Queue of images
image_queue = []
current_index = 0
display_speed = 5  # Default 5 seconds per image

def on_message(client, userdata, message):
    """ Handles incoming MQTT messages (new images). """
    global image_queue
    data = json.loads(message.payload)
    image_path = os.path.expanduser(data["path"])

    if image_path not in image_queue:
        image_queue.append(image_path)  # Add new image to queue

client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER)
client.subscribe(MQTT_TOPIC)
client.loop_start()

def display_images():
    """ Loops through image queue and displays them. """
    global current_index
    while True:
        if image_queue:
            print(f"Current Queue: {image_queue}")  # Print the entire queue
            image_path = image_queue[current_index]
            print(f"Displaying Image: {image_path}")  # Print the image being displayed
            
            try:
                image = Image.open(image_path).convert("RGB")
                image = image.resize((matrix.width, matrix.height))
                matrix.SetImage(image)
                print(f"Successfully displayed: {image_path}")
            except Exception as e:
                print(f"Error displaying image: {e}")

            # Cycle to next image
            current_index = (current_index + 1) % len(image_queue)
        else:
            print("Image queue is empty!")

        time.sleep(display_speed)  # Adjust display time


try:
    display_images()
except KeyboardInterrupt:
    print("Exiting MQTT client...")
