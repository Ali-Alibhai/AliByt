from flask import Flask, request, jsonify
import json
import os
import mqtt

app = Flask(__name__)

# File to store subscriptions
DB_FILE = "database.json"

# Load existing subscriptions
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        subscriptions = json.load(f)
else:
    subscriptions = {"subscribed_apps": []}

@app.route("/subscribe", methods=["POST"])
def subscribe():
    """ Subscribe to an app """
    data = request.json
    app_name = data.get("app")

    if app_name and app_name not in subscriptions["subscribed_apps"]:
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
    image_url = data.get("image_url")

    if app_name in subscriptions["subscribed_apps"]:
        mqtt.publish_update(app_name, image_url)
        return jsonify({"message": f"Update pushed for {app_name}"}), 200
    return jsonify({"error": "App not subscribed"}), 400

def save_subscriptions():
    """ Save subscription data to file """
    with open(DB_FILE, "w") as f:
        json.dump(subscriptions, f, indent=4)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
