import os
import json
import platform
import getpass
from dotenv import load_dotenv, set_key

ENV_FILE_PATH = ".env"

def get_chrome_user_data_dir():
    """
    check or prompt for the Chrome user data directory and storing it in .env
    so the user doesn't have to re enter each time.
    """
    load_dotenv(ENV_FILE_PATH)
    system = platform.system()
    user = getpass.getuser()

    # defaults for macOS or Windows
    if system == "Darwin":
        user_data_dir = f"/Users/{user}/Library/Application Support/Google/Chrome"
    elif system == "Windows":
        user_data_dir = f"C:\\Users\\{user}\\AppData\\Local\\Google\\Chrome\\User Data"

    # if default path not found, prompt
    if not os.path.exists(user_data_dir):
        print(f"Default Chrome user data directory not found at: {user_data_dir}")
        user_data_dir = input("Please enter the correct Chrome user data directory, or 'q' to quit: ")
        if user_data_dir.lower() == "q":
            return ""

    # store in .env so we don't prompt again next time
    set_key(ENV_FILE_PATH, "USER_DATA_DIR", user_data_dir)
    return user_data_dir


def get_profile_display_name(profile_path):
    preferences_file = os.path.join(profile_path, "Preferences")
    if not os.path.isfile(preferences_file):
        return None
    
    try:
        with open(preferences_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    account_info = data.get("account_info", [])
    if isinstance(account_info, list) and account_info:
        first_item = account_info[0]
        if isinstance(first_item, dict):
            full_name = first_item.get("full_name")
            given_name = first_item.get("given_name")
            display_name = full_name or given_name
            if display_name:
                return display_name
    return None


def get_chrome_profile_dir(user_data_dir):
    """
    lists subdirectories in the user_data_dir that look like "Profile*"
    allows the user to pick one, then saves it to .env for reuse.
    """
    print("*** *** *** Welcome to CU MS-CS Coursera Grade Verifier *** *** ***\n")
    print(" NOTES BEFORE STARTING:")
    print("     - Before use, ensure that you have a chrome user profile.")
    print("       If not, please create one before running this program.\n")
    print("     - Ensure that no instances of Chrome are currently running")
    print("       on your device.\n")
    print("-------------------------------------------------------------------\n")

    load_dotenv(ENV_FILE_PATH)
    if not user_data_dir or not os.path.isdir(user_data_dir):
        print(f"Invalid user_data_dir: {user_data_dir}")
        return ""

    all_subdirs = os.listdir(user_data_dir)
    subdirs = [
        d for d in all_subdirs
        if d.startswith("Profile") and os.path.isdir(os.path.join(user_data_dir, d))
    ]

    if not subdirs:
        print(f"No Chrome profiles found in {user_data_dir}.")
        return ""

    print("Available Chrome profiles found:\n")
    profile_choices = []
    for d in subdirs:
        profile_path = os.path.join(user_data_dir, d)
        display_name = get_profile_display_name(profile_path)
        display_name = display_name if display_name else d
        profile_choices.append((d, display_name))

    for i, (folder, friendly_name) in enumerate(profile_choices, start=1):
        print(f"{i}. ({folder}, {friendly_name})")

    print("-------------------------------------------------------------------\n")
    choice = input("Select a profile by number: ")
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(profile_choices):
            raise ValueError("Invalid choice")
    except ValueError:
        print("Invalid input.")
        raise
    
    selected_profile_folder, selected_profile_name = profile_choices[idx]
    set_key(ENV_FILE_PATH, "PROFILE_DIR", selected_profile_folder)
    return selected_profile_folder


def get_coursera_password():
    """
    prompt for the password
    """
    password = input("Please enter your Coursera account password: ")
    return password


def get_coursera_username():
    """
    prompt for the username
    """
    username = input("Please enter your Coursera account email: ")
    return username