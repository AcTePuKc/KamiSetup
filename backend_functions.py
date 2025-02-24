"""
backend_functions.py - Backend Logic Functions
---------------------------------------------
This file contains all the backend logic and functions for the
One-Click Environment Setup application.

It includes functions for:
- Finding virtual environments (venvs)
- Creating virtual environments and conda environments
- Checking for conda installation
- Listing conda environments
- Saving and loading selected environment settings
- Downloading and installing Python
- Launching activated command prompts
- Logging utilities
- Worker thread for subprocess execution (InstallWorker)

These functions are designed to be UI-agnostic and are called by
the UI page classes defined in ui_pages.py.
"""

import subprocess
import requests
import os
import re
import json
import urllib.request
import datetime
from PySide6.QtCore import QThread, Signal

# --- Constants ---

class InstallWorker(QThread):
    output_signal = Signal(str)  # Signal to send console output
    # Signal to indicate process completion with env name
    finished_signal = Signal(int, str)

    def __init__(self, command, console, env_name):
        super().__init__()
        self.command = command  # The subprocess command to execute
        self.console = console
        self.env_name = env_name  # Store environment name

    def run(self):
        """Runs the command in a separate thread and sends live output to UI."""
        process = subprocess.Popen(
            self.command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        while True:
            output_line = process.stdout.readline()
            if output_line:
                # Send output to console
                self.output_signal.emit(output_line.strip())
            else:
                break

        return_code = process.wait()  # Wait for process to complete
        self.finished_signal.emit(return_code, self.env_name)


# --- Configuration ---
SETTINGS_FILE = "settings.json"
# Revised template with {version_full}
PYTHON_DOWNLOAD_URL = "https://www.python.org/ftp/python/{version_full}/python-{version_full}-amd64.exe"


def find_local_venvs(search_dir="."):
    """Finds venvs (Windows: Scripts/activate.bat)."""
    venvs = []
    for item in os.listdir(search_dir):
        full_path = os.path.join(search_dir, item)
        if os.path.isdir(full_path):
            activate_bat = os.path.join(full_path, "Scripts", "activate.bat")
            if os.path.exists(activate_bat):
                venvs.append(item)
    return venvs


def create_virtual_env(env_name, python_version):
    """Creates a venv, auto-incrementing."""
    base_name = env_name or "myenv"
    final_name = base_name
    num = 0
    while os.path.exists(final_name):
        num += 1
        final_name = f"{base_name}_{num}" if num > 0 else base_name

    py_cmd = ["py", f"-{python_version}", "-m", "venv", final_name]
    subprocess.check_call(py_cmd)
    return final_name


def check_conda():
    """Checks if conda is installed."""
    try:
        subprocess.check_output(["conda", "--version"],
                                stderr=subprocess.STDOUT)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def list_conda_envs():
    """Lists conda environments (handles errors)."""
    try:
        result = subprocess.check_output(
            ["conda", "env", "list"], text=True, stderr=subprocess.STDOUT)
        envs = []
        for line in result.splitlines():
            if line.strip() and not line.startswith("#") and " " in line:
                env_name = line.split()[0].strip()
                envs.append(env_name)
        return envs
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        log_error(f"Error listing conda environments: {e}")  # Use log_error
        return []
    
def save_setting(key, value):
    """Saves a setting to settings.json"""
    settings = load_settings()
    settings[key] = value
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def load_settings():
    """Loads settings from settings.json"""
    if not os.path.exists(SETTINGS_FILE):
        return {}
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

def create_conda_env(env_name, python_version, console):
    """Creates a conda environment and returns the final environment name."""
    base_name = env_name or "myenv"
    final_name = base_name
    num = 0
    while True:
        env_exists = final_name in list_conda_envs()
        if not env_exists:
            break
        num += 1
        final_name = f"{base_name}_{num}" if num > 0 else base_name

    return final_name  # No worker creation here


def save_selected_env(env_type, env_name):
    """Saves the selected environment type and name."""
    with open(SETTINGS_FILE, "w") as f:
        f.write(f"{env_type}\n{env_name}")


def load_selected_env():
    """Loads the selected environment."""
    try:
        with open(SETTINGS_FILE, "r") as f:
            env_type = f.readline().strip()
            env_name = f.readline().strip()
            return env_type, env_name
    except FileNotFoundError:
        return None, None


def get_full_version(version_display):
    """Fetches the latest patch version for a given Python major.minor version dynamically."""
    base_url = "https://www.python.org/ftp/python/"

    try:
        # Console feedback
        log_info(f"Fetching Python version list from: {base_url}")  # Use log_info
        response = requests.get(base_url, timeout=10)
        response.raise_for_status()

        versions = re.findall(r'href="(\d+\.\d+\.\d+)/"', response.text)
        versions.sort(reverse=True)

        version_map = {}
        for full_version in versions:
            major_minor = ".".join(full_version.split(".")[:2])
            version_map[major_minor] = full_version

        latest_full_version = version_map.get(version_display, version_display)
        log_info(  # Use log_info
            f"Latest full Python version found for {version_display}: {latest_full_version}")
        return latest_full_version

    except requests.RequestException as e:
        error_msg = f"Error fetching latest Python versions: {e}"
        log_error(error_msg)
        return version_display


def download_and_install_python(version_display, console):  # ADD console parameter
    """Downloads and installs Python (DYNAMIC URL VERSION)."""
    version_full = get_full_version(version_display)
    if version_full is None:
        version_full = version_display

    download_url = PYTHON_DOWNLOAD_URL.format(version_full=version_full)
    installer_path = f"python-{version_full}-installer.exe"

    log_info(
        f"Downloading Python {version_full} installer from: {download_url}", console)
    try:
        urllib.request.urlretrieve(
            download_url, installer_path, reporthook=download_progress_hook)
        log_success(
            f"Python installer downloaded to: {installer_path}", console)
    except Exception as e:
        error_msg = f"Error downloading Python installer: {e}"
        log_error(error_msg, console)
        from PySide6.QtWidgets import QMessageBox  # Import here to avoid circular import
        QMessageBox.critical(None, "Download Error", error_msg)
        return False

    log_info(f"Installing Python {version_full}...", console)
    try:
        subprocess.check_call([installer_path, "/passive", "/norestart"])
        log_success(f"Python {version_full} installed successfully.", console)
        return True
    except subprocess.CalledProcessError as e:
        error_msg = f"Error installing Python {version_full}. Installer exited with code: {e.returncode}"
        log_error(error_msg, console)
        from PySide6.QtWidgets import QMessageBox  # Import here to avoid circular import
        QMessageBox.critical(None, "Installation Error", error_msg)
        return False
    finally:
        try:
            os.remove(installer_path)
        except OSError as e:
            log_error(f"Error deleting installer file: {e}", console)


def download_progress_hook(block_num, block_size, total_size):
    """Basic download progress hook for urllib.request.urlretrieve."""
    bytes_read = block_num * block_size
    if total_size > 0:
        percent_complete = int((bytes_read / total_size) * 100)
        print(
            f"Downloaded {percent_complete}% ({bytes_read} / {total_size} bytes)", end='\r')
    else:
        print(f"Downloaded {bytes_read} bytes", end='\r')


def launch_activated_cmd(env_type, env_name, console):
    """Launches CMD with venv or conda env activated."""
    if not env_name:
        log_error("Error: No environment name provided.", console)
        return

    try:
        log_info(f"Launching CMD with activation for: {env_name} (Type: {env_type})", console)

        creationflags = 0  # Default for non-Windows
        if os.name == 'nt': # Check for Windows explicitly using os.name
            creationflags = subprocess.CREATE_NEW_CONSOLE

        if env_type == "venv":
            activation_script = os.path.join(env_name, "Scripts", "activate.bat")
            # Modified command for venv: activate, show where python, and then python --version
            command_to_run = f"call {activation_script} && where python && python --version" # <-- CHANGED LINE AGAIN - Now includes both
        elif env_type == "conda":
            conda_activate_command = f"conda activate {env_name} && conda info --envs"
            log_info(f"Conda Activate Command: {conda_activate_command}", console)
            command_to_run = conda_activate_command
        else:
            command_to_run = "echo Error: Unknown environment type && pause"

        cmd = ["cmd.exe", "/K", command_to_run] if os.name == 'nt' else ["/bin/bash", "-c", command_to_run] # Use bash on non-Windows
        log_info(f"Executing command: {cmd}", console)

        subprocess.Popen(cmd, creationflags=creationflags)
        log_success("subprocess.Popen for activated CMD called.", console)

    except Exception as e:
        error_msg = f"Error launching activated CMD: {e}"
        log_error(error_msg, console)
        from PySide6.QtWidgets import QMessageBox  # Import here to avoid circular import
        QMessageBox.critical(None, "Activation Error", error_msg)


# --- Logging Helper Functions ---
def log_message(message, level, console=None):
    """Logs a message to the console with timestamp and level."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] [{level}] {message}"
    print(formatted_message)  # Still print to terminal for debugging
    if console:
        console.appendPlainText(formatted_message)


def log_info(message, console=None):
    """Logs an INFO message."""
    log_message(message, "INFO", console)


def log_success(message, console=None):
    """Logs a SUCCESS message."""
    log_message(message, "SUCCESS", console)


def log_error(message, console=None):
    """Logs an ERROR message."""
    log_message(message, "ERROR", console)