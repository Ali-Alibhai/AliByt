import os
import json

# Base directory where apps are stored
APPS_BASE_DIR = "/home/ali/AliByt/alibyt-apps/tidbyt-community/apps"

# Path to the apps_config.json file
CONFIG_PATH = "/home/ali/AliByt/alibyt-server/apps_config.json"

# Default refresh rate
DEFAULT_REFRESH_RATE = 60  # You can change this default


def find_star_file(directory):
    """Finds the .star file inside the given app directory."""
    for file in os.listdir(directory):
        if file.endswith(".star"):
            return file  # Return the full filename (e.g., "nba_standings.star")
    return None  # No .star file found


def update_apps_config():
    """ Scans the apps directory and updates the apps_config.json file """
    apps_config = {}

    # Check if the base directory exists
    if not os.path.exists(APPS_BASE_DIR):
        print(f"Error: Apps directory {APPS_BASE_DIR} does not exist!")
        return

    # Loop through all app directories
    for app_name in os.listdir(APPS_BASE_DIR):
        app_dir = os.path.join(APPS_BASE_DIR, app_name)

        # Ensure it's a directory
        if not os.path.isdir(app_dir):
            continue

        # Find the actual .star filename inside the directory
        star_filename = find_star_file(app_dir)
        if not star_filename:
            print(f"⚠️ Warning: No .star file found in {app_dir}, skipping...")
            continue  # Skip this app if no .star file is found

        # Generate the .webp filename (same name as the .star file, but with .webp)
        webp_filename = star_filename.replace(".star", ".webp")

        # Add to config
        apps_config[app_name] = {
            "path": app_dir,
            "app_name": star_filename,
            "photo_name": webp_filename,
            "refresh_rate": DEFAULT_REFRESH_RATE
        }

    # Save updated config
    with open(CONFIG_PATH, "w") as config_file:
        json.dump(apps_config, config_file, indent=4)

    print(f"✅ Updated {CONFIG_PATH} with {len(apps_config)} apps.")


if __name__ == "__main__":
    update_apps_config()

