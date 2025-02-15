import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
TOPIC_PREFIX = "alibyt/app/"

def publish_update(app_name, image_url):
    """ Publish an image update via MQTT """
    client = mqtt.Client()
    client.connect(BROKER, PORT, 60)

    topic = f"{TOPIC_PREFIX}{app_name}"
    client.publish(topic, image_url)
    client.disconnect()

if __name__ == "__main__":
    print("MQTT Publisher ready.")
