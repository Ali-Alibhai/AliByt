import json
import time
import os
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image

# Load app settings
config_path = "~/AliByt/alibyt-server/apps_config.json"
config_path = os.path.expanduser(config_path)

with open(config_path, "r") as file:
    apps = json.load(file)

# Initialize the matrix
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'adafruit-hat'
options.disable_hardware_pulsing = True
options.gpio_slowdown = 2

matrix = RGBMatrix(options=options)

def display_image(image_path, brightness):
    """Displays an image on the LED matrix with specified brightness."""
    options.brightness = brightness  # Set app-specific brightness
    matrix.SetOptions(options)  # Apply brightness change

    try:
        image = Image.open(image_path).convert("RGB")
        image = image.resize((matrix.width, matrix.height))
        matrix.SetImage(image)
    except Exception as e:
        print(f"Error displaying {image_path}: {e}")

def run_scheduler():
    """Runs the app scheduler."""
    while True:
        for app, settings in apps.items():
            image_path = os.path.expanduser(settings["path"])
            refresh_rate = settings["refresh_rate"]
            brightness = settings["brightness"]

            print(f"Displaying {app} at brightness {brightness}")
            display_image(image_path, brightness)

            time.sleep(refresh_rate)  # Wait for the app-specific refresh time

try:
    run_scheduler()
except KeyboardInterrupt:
    print("Exiting scheduler...")
