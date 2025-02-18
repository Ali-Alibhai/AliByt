import json

def load_apps_config():
    """ Loads the apps_config.json file and returns available apps. """
    CONFIG_PATH = "/home/ali/AliByt/alibyt-server/apps_config.json"
    with open(CONFIG_PATH, "r") as file:
        return json.load(file)
