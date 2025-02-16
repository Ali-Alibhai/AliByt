
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image

# Matrix configuration
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.hardware_mapping = 'adafruit-hat'  # Ensure correct mapping
options.disable_hardware_pulsing = True  # Reduce flickering
options.gpio_slowdown = 1  # Adjust as needed

matrix = RGBMatrix(options=options)

# Create an image (Full red screen)
image = Image.new("RGB", (64, 32), (255, 0, 0))  # Full-screen red

# Display the image on the matrix
matrix.SetImage(image)

# Keep the script running to hold the image on display
try:
    while True:
        pass  # Keeps the script alive
except KeyboardInterrupt:
    print("Exiting...")

