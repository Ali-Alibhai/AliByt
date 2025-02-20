import os
import json
import re

# Base directory where apps are stored
APPS_BASE_DIR = "/home/ali/AliByt/alibyt-apps/tidbyt-community/apps"

# Path to the apps_config.json file
CONFIG_PATH = "/home/ali/AliByt/alibyt-server/apps_config.json"

# Default refresh rate
DEFAULT_REFRESH_RATE = 60  # Default refresh rate in seconds

def find_star_file(directory):
    """Finds the .star file inside the given app directory."""
    for file in os.listdir(directory):
        if file.endswith(".star"):
            return file  # Return the full filename (e.g., "nba_standings.star")
    return None  # No .star file found

def extract_config_options(star_file_path):
    """Extracts configuration options from the .star file by scanning for schema definitions."""
    config_options = []
    try:
        with open(star_file_path, "r", encoding="utf-8") as file:
            content = file.read()
            
            # Match schema configuration definitions
            matches = re.findall(r'schema\.(\w+)\(\s*id\s*=\s*"(.*?)".*?name\s*=\s*"(.*?)"', content)
            for match in matches:
                option_type, option_id, label = match
                
                # Extract default value
                default_match = re.search(rf'id\s*=\s*"{option_id}".*?default\s*=\s*(.*?),', content, re.DOTALL)
                default_value = default_match.group(1) if default_match else None
                
                # Extract dropdown options
                options_match = re.search(rf'id\s*=\s*"{option_id}".*?options\s*=\s*\[(.*?)\]', content, re.DOTALL)
                options = [opt.strip('" ') for opt in options_match.group(1).split(',')] if options_match else None
                
                config_options.append({
                    "label": label,
                    "type": option_type,
                    "id": option_id,
                    "default_value": default_value,
                    "selected_value": None,
                    "options": options
                })
    except Exception as e:
        print(f"Error reading {star_file_path}: {e}")
    
    return config_options

def update_apps_config():
    """Scans the apps directory and updates the apps_config.json file."""
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

        # Full path to .star file
        star_file_path = os.path.join(app_dir, star_filename)

        # Extract config settings from the .star file
        config_settings = extract_config_options(star_file_path)

        # Generate the .webp filename (same name as the .star file, but with .webp)
        webp_filename = star_filename.replace(".star", ".webp")

        # Add to config
        apps_config[app_name] = {
            "path": app_dir,
            "app_name": star_filename,
            "photo_name": webp_filename,
            "refresh_rate": DEFAULT_REFRESH_RATE,
            "config_settings": config_settings  # New field for available configurations
        }

    # Save updated config
    with open(CONFIG_PATH, "w", encoding="utf-8") as config_file:
        json.dump(apps_config, config_file, indent=4)

    print(f"✅ Updated {CONFIG_PATH} with {len(apps_config)} apps.")

if __name__ == "__main__":
    update_apps_config()
