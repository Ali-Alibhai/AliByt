from flask import Flask, request, jsonify
import json
import os
import paho.mqtt.client as mqtt

app = Flask(__name__)

# Paths
APPS_CONFIG_FILE = os.path.expanduser("~/AliByt/alibyt-server/apps_config.json")
DB_FILE = os.path.expanduser("~/AliByt/alibyt-server/database.json")

# MQTT Setup
MQTT_BROKER = "localhost"
MQTT_TOPIC = "alibyt/images"

mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER)

# Load app subscriptions
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        subscriptions = json.load(f)
else:
    subscriptions = {"subscribed_apps": [], "client_speed": 5}

def save_subscriptions():
    """ Save subscription data to file """
    with open(DB_FILE, "w") as f:
        json.dump(subscriptions, f, indent=4)

def load_apps_config():
    """ Load available apps from config file """
    if os.path.exists(APPS_CONFIG_FILE):
        with open(APPS_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

@app.route("/subscribe", methods=["POST"])
def subscribe():
    """ Subscribe to an app """
    data = request.json
    app_name = data.get("app")

    available_apps = load_apps_config()
    if app_name in available_apps and app_name not in subscriptions["subscribed_apps"]:
        subscriptions["subscribed_apps"].append(app_name)
        save_subscriptions()
        return jsonify({"message": f"Subscribed to {app_name}"}), 200
    return jsonify({"error": "Invalid request or already subscribed"}), 400

@app.route("/unsubscribe", methods=["POST"])
def unsubscribe():
    """ Unsubscribe from an app """
    data = request.json
    app_name = data.get("app")

    if app_name in subscriptions["subscribed_apps"]:
        subscriptions["subscribed_apps"].remove(app_name)
        save_subscriptions()
        return jsonify({"message": f"Unsubscribed from {app_name}"}), 200
    return jsonify({"error": "App not found in subscriptions"}), 400

@app.route("/subscriptions", methods=["GET"])
def get_subscriptions():
    """ Get list of subscribed apps """
    return jsonify(subscriptions)

@app.route("/push_update", methods=["POST"])
def push_update():
    """ Push a new image update via MQTT """
    data = request.json
    app_name = data.get("app")

    available_apps = load_apps_config()
    if app_name in subscriptions["subscribed_apps"] and app_name in available_apps:
        image_path = os.path.expanduser(available_apps[app_name]["path"])
        
        mqtt_message = json.dumps({"app": app_name, "path": image_path})
        mqtt_client.publish(MQTT_TOPIC, mqtt_message)

        return jsonify({"message": f"Update pushed for {app_name}"}), 200
    return jsonify({"error": "App not subscribed or invalid"}), 400

@app.route("/set_speed", methods=["POST"])
def set_client_speed():
    """ Set client cycle speed """
    data = request.json
    new_speed = data.get("speed")

    if isinstance(new_speed, int) and new_speed > 0:
        subscriptions["client_speed"] = new_speed
        save_subscriptions()
        
        mqtt_message = json.dumps({"type": "update_speed", "speed": new_speed})
        mqtt_client.publish(MQTT_TOPIC, mqtt_message)

        return jsonify({"message": f"Client speed updated to {new_speed} seconds"}), 200
    return jsonify({"error": "Invalid speed value"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
