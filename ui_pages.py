"""
ui_pages.py - UI Page Classes
-----------------------------
This file defines all the QWidget-based classes that represent
the different pages in the One-Click Environment Setup GUI.

These pages handle the user interface elements, layouts,
button clicks, and input handling for each section of the application
(e.g., Create Venv, Activate Env, Conda Manager, Install Python, etc.).

They rely on backend functions from backend_functions.py to perform
the actual environment management and installation tasks.
"""

import sys
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QStackedWidget, QMessageBox, QRadioButton, QCheckBox,
    QPlainTextEdit, QButtonGroup
)
import subprocess
from backend_functions import (  # Import backend functions from backend_functions.py
    find_local_venvs, create_virtual_env, check_conda, list_conda_envs,
    create_conda_env, save_selected_env, load_selected_env, get_full_version,
    download_and_install_python, launch_activated_cmd, log_info, log_success,
    log_error, download_progress_hook, InstallWorker # Import InstallWorker too
)


class SideMenu(QWidget):
    """The side menu."""

    def __init__(self, stack, console, status_bar):
        super().__init__()
        self.stack, self.console, self.status_bar = stack, console, status_bar
        layout = QVBoxLayout(self)

        buttons = [
            ("Create && Activate Virtual Env", 1,
             "Opening Create Virtual Environment page..."),
            ("Activate Existing Virtual Env", 2,
             "Opening Activate Existing Virtual Environment page..."),
            ("Conda Environment Manager", 3,
             "Opening Conda Environment Manager page..."),
            ("Install PyTorch / CUDA ", 4, "Opening Install PyTorch & CUDA page..."),
            ("Install ONNX", 5, "Opening Install ONNX page..."),
            ("Install Dependencies", 6, "Opening Install Dependencies page..."),
            ("Install Python", 7, "Opening Install Python page..."),
            ("Full Setup", 8, "Opening Full Setup page..."),
            ("Exit", lambda: sys.exit(0), "Exiting..."),
        ]

        for text, target, message in buttons:
            btn = QPushButton(text)
            if isinstance(target, int):
                btn.clicked.connect(lambda checked, s=self,
                                    i=target, m=message: s.switch_page(i, m))
            else:
                btn.clicked.connect(target)
            layout.addWidget(btn)

        layout.addStretch(1)
        self.setMinimumWidth(180)

    def switch_page(self, index, message):
        """Switches the stacked widget."""
        log_info(message, self.console)  # Use log_info
        self.status_bar.showMessage(message, 3000)
        self.stack.setCurrentIndex(index)
        if index == 2:
            activate_page = self.stack.widget(2)
            if isinstance(activate_page, ActivateEnvPage):
                activate_page.load_and_display()
        elif index == 3:
            create_conda_page = self.stack.widget(3)
            if isinstance(create_conda_page, CreateCondaPage):
                create_conda_page.load_and_display()


class CreateVenvPage(QWidget):
    """Page for creating & providing activation instructions for venv."""

    def __init__(self, stack, console, status_bar):
        super().__init__()
        self.stack, self.console, self.status_bar = stack, console, status_bar
        layout = QVBoxLayout(self)
        layout.setSpacing(10)  # Add vertical spacing
        # Add margins around the page
        layout.setContentsMargins(15, 15, 15, 15)

        # Consistent title
        title_label = QLabel("Create & Activate Virtual Environment (venv)")
        title_label.setProperty("page_title", True)  # For styling
        layout.addWidget(title_label)

        name_label = QLabel("Virtual Environment Name:")  # Label above input
        layout.addWidget(name_label)
        self.name_edit = QLineEdit(self)  # Use QLineEdit for single-line input
        self.name_edit.setPlaceholderText("Enter venv name (default: myenv)")
        layout.addWidget(self.name_edit)

        # Connect textEdited signal to formatting function
        self.name_edit.textEdited.connect(
            self.format_venv_name)  # Connect signal

        # Label above dropdown
        version_label = QLabel("Select Python Version:")
        layout.addWidget(version_label)
        self.version_combo = QComboBox(self)
        self.version_combo.addItems(["3.8", "3.9", "3.10", "3.11", "3.12"])
        layout.addWidget(self.version_combo)

        btn_layout = QHBoxLayout()
        self.check_btn = QPushButton("Check Version")
        btn_layout.addWidget(self.check_btn)
        self.check_btn.clicked.connect(self.check_python_version)

        self.create_btn = QPushButton("Create && Get Activation Instructions")
        btn_layout.addWidget(self.create_btn)
        self.create_btn.clicked.connect(self.create_and_show_info)

        layout.addLayout(btn_layout)

    def format_venv_name(self, text):
        """Formats the venv name to be venv-folder-friendly."""
        formatted_name = text.lower()  # Lowercase
        # Replace spaces/invalid chars with underscores
        formatted_name = "".join(
            c if c.isalnum() or c == '_' else "_" for c in formatted_name)
        # Set formatted text back to line edit
        self.name_edit.setText(formatted_name)
        # Optionally, you could also set the cursor position to the end if needed:
        # self.name_edit.setCursorPosition(len(formatted_name))

    def check_python_version(self):
        """Checks if the selected Python version is installed."""
        version = self.version_combo.currentText()
        try:
            subprocess.check_output(
                ["py", f"-{version}", "--version"], stderr=subprocess.STDOUT)
            msg = f"Python {version} is available."
            self.status_bar.showMessage(msg, 3000)
            log_success(msg, self.console)  # Use log_success

        except subprocess.CalledProcessError:
            msg = f"Python {version} is not installed."
            self.status_bar.showMessage(msg, 3000)
            log_info(msg, self.console)  # Use log_info

    def install_python(self):
        """Downloads and installs the selected Python version."""
        version_display = self.version_combo.currentText()  # Get display text (e.g., "3.8")
        version_full = get_full_version(version_display)
        msg = f"Downloading and installing Python {version_display}..."
        log_info(msg, self.console)  # Use log_info
        self.status_bar.showMessage(msg, 3000)

        # Pass full version to download_and_install_python
        if download_and_install_python(version_full, self.console):  # Pass console
            msg = f"Python {version_display} installed successfully."
            QMessageBox.information(self, "Installation Complete", msg)
            log_success(msg, self.console)  # Use log_success
            self.status_bar.showMessage(msg, 3000)

        else:
            msg = f"Failed to install Python {version_display}."
            QMessageBox.critical(self, "Installation Failed", msg)
            log_error(msg, self.console)  # Use log_error
            self.status_bar.showMessage(msg, 3000)

    def create_and_show_info(self):
        """Creates the venv and shows activation instructions."""
        name = self.name_edit.text().strip()
        version_display = self.version_combo.currentText()  # Get display version
        try:
            # Check if Python version is available
            subprocess.check_output(
                ["py", f"-{version_display}", "--version"], stderr=subprocess.STDOUT)
            # Python version is available, proceed to create venv
            final_name = create_virtual_env(name, version_display)  # Use display version here too
            msg = f"Virtual environment '{final_name}' created."
            log_success(msg, self.console)
            self.status_bar.showMessage(msg, 3000)
            save_selected_env("venv", final_name)
            self.show_activation_info(final_name)

        except subprocess.CalledProcessError:
            # Python version is NOT available, offer to install
            msgbox = QMessageBox()
            msgbox.setIcon(QMessageBox.Question)
            msgbox.setText(f"Python {version_display} is not installed. Do you want to install it?")
            msgbox.setWindowTitle("Python Not Found")
            msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            install_button = msgbox.button(QMessageBox.Yes)
            install_button.setText("Install Python")  # More descriptive button text
            msgbox.setDefaultButton(QMessageBox.Yes)

            result = msgbox.exec()
            if result == QMessageBox.Yes:
                log_info(f"User chose to install Python {version_display}.", self.console)
                if download_and_install_python(version_display, self.console):  # Pass console here
                    log_success(f"Python {version_display} installed. Proceeding with environment creation...", self.console)
                    try:
                        final_name = create_virtual_env(name, version_display)  # Use display version after install
                        msg = f"Virtual environment '{final_name}' created."
                        log_success(msg, self.console)
                        self.status_bar.showMessage(msg, 3000)
                        save_selected_env("venv", final_name)
                        self.show_activation_info(final_name)
                    except subprocess.CalledProcessError as e_venv:
                        msg_venv_error = f"Failed to create venv after Python install: {e_venv}"
                        log_error(msg_venv_error, self.console)
                        self.status_bar.showMessage(msg_venv_error, 5000)
                else:
                    msg_install_fail = f"Python {version_display} installation failed. Venv creation aborted."
                    log_error(msg_install_fail, self.console)
                    self.status_bar.showMessage(msg_install_fail, 5000)
            else:
                msg_user_cancel = f"Python {version_display} installation cancelled. Venv creation aborted."
                log_info(msg_user_cancel, self.console)
                self.status_bar.showMessage(msg_user_cancel, 3000)

        except subprocess.CalledProcessError as e:  # Catch initial version check error (unlikely now, but good to have)
            msg_error = f"Error checking Python version: {e}"
            log_error(msg_error, self.console)
            self.status_bar.showMessage(msg_error, 5000)

    def show_activation_info(self, venv_name):
        """Opens CMD with venv activated using shared function."""
        msg = f"Launching terminal with venv activation for: {venv_name}"
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Information)
        dialog.setText(msg)
        dialog.setWindowTitle("Launching Activated Terminal")
        dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Open)
        dialog.button(QMessageBox.Open).setText("Launch Activated CMD")
        dialog.setDefaultButton(QMessageBox.Ok)

        result = dialog.exec()

        if result == QMessageBox.Open:
            # Pass env_type="venv" and venv_name
            launch_activated_cmd("venv", venv_name, self.console)


class ActivateEnvPage(QWidget):
    """Page for selecting an existing venv and getting activation instructions."""

    def __init__(self, stack, console, status_bar):
        super().__init__()
        self.stack, self.console, self.status_bar = stack, console, status_bar
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        title_label = QLabel("Activate Existing Virtual Environment")
        title_label.setProperty("page_title", True)
        layout.addWidget(title_label)

        venv_label = QLabel("Select Virtual Environment:")
        layout.addWidget(venv_label)
        self.venv_combo = QComboBox(self)
        layout.addWidget(self.venv_combo)

        reload_btn = QPushButton("Refresh List")
        layout.addWidget(reload_btn)
        reload_btn.clicked.connect(self.load_venvs)

        btn_layout = QHBoxLayout() # <-- Create QHBoxLayout for buttons
        self.activate_btn = QPushButton("Get Activation Instructions")
        btn_layout.addWidget(self.activate_btn)
        self.activate_btn.clicked.connect(self.show_activation_info)

        self.activate_only_btn = QPushButton("Activate Only (No CMD)") # NEW - Activate Only Button
        btn_layout.addWidget(self.activate_only_btn) # Add to button layout
        self.activate_only_btn.clicked.connect(self.activate_only) # Connect new button
        layout.addLayout(btn_layout) # <-- Add button layout to main layout


        self.selected_env_label = QLabel("")
        self.selected_env_label.setProperty(
            "selection_label", True)
        layout.addWidget(self.selected_env_label)

        self.load_venvs()
        self.load_and_display()
        layout.addStretch(1)

    def showEvent(self, event):
        """Override showEvent to refresh venv list when page is shown."""
        super().showEvent(event)
        self.load_venvs()
        self.load_and_display()

    def load_venvs(self):
        self.venv_combo.clear()
        venvs = find_local_venvs(".")
        if not venvs:
            self.venv_combo.addItem("No venvs found.")
            self.venv_combo.setEnabled(False)
            self.activate_btn.setEnabled(False)
            self.activate_only_btn.setEnabled(False) # Disable "Activate Only" too if no venvs
        else:
            self.venv_combo.setEnabled(True)
            self.activate_btn.setEnabled(True)
            self.activate_only_btn.setEnabled(True) # Enable "Activate Only" too if venvs are found
            self.venv_combo.addItems(venvs)

    def show_activation_info(self):
        """Gets the selected venv name and launches CMD using shared function."""
        selected = self.venv_combo.currentText()
        if selected == "No venvs found.":
            return
        venv_name = selected

        msg = f"Launching terminal with venv activation for: {venv_name}"
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Information)
        dialog.setText(msg)
        dialog.setWindowTitle("Launching Activated Terminal")
        dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Open)
        dialog.button(QMessageBox.Open).setText("Launch Activated CMD")
        dialog.setDefaultButton(QMessageBox.Ok)

        result = dialog.exec()

        if result == QMessageBox.Open:
            # Pass env_type="venv" and venv_name
            launch_activated_cmd("venv", venv_name, self.console)

    def activate_only(self): # NEW - Activate Only method
        """Activates the selected venv without launching CMD."""
        selected = self.venv_combo.currentText()
        if selected == "No venvs found.":
            return
        venv_name = selected

        save_selected_env("venv", venv_name) # Save selected venv
        self.load_and_display() # Update selected env label

        log_success(f"Virtual environment '{venv_name}' selected for activation (no CMD launched).", self.console) # Log success
        self.status_bar.showMessage(f"Virtual environment '{venv_name}' selected.", 3000) # Status bar message


    def load_and_display(self):
        """Loads and displays the currently selected environment."""
        env_type, env_name = load_selected_env()
        if env_type == "venv" and env_name:
            self.selected_env_label.setText(f"Selected venv: {env_name}")
        else:
            self.selected_env_label.setText("No venv selected")


class CreateCondaPage(QWidget):
    """Page for creating/selecting and getting activation instructions for conda."""

    def __init__(self, stack, console, status_bar):
        super().__init__()
        self.stack, self.console, self.status_bar = stack, console, status_bar
        layout = QVBoxLayout(self)
        layout.setSpacing(10)  # Add vertical spacing
        # Add margins around the page
        layout.setContentsMargins(15, 15, 15, 15)

        # More descriptive title
        title_label = QLabel("Conda Environment Manager")
        title_label.setProperty("page_title", True)  # For styling
        layout.addWidget(title_label)
        # Sub-title for create section
        layout.addWidget(QLabel("Create & Activate Conda Environment"))

        name_label = QLabel("Conda Environment Name:")  # Label above input
        layout.addWidget(name_label)
        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText(
            "Enter conda env name (default: myenv)")
        layout.addWidget(self.name_edit)

        # Label above dropdown
        version_label = QLabel("Select Python Version:")
        layout.addWidget(version_label)
        self.version_combo = QComboBox(self)
        self.version_combo.addItems(["3.8", "3.9", "3.10", "3.11", "3.12"])
        layout.addWidget(self.version_combo)

        btn_layout = QHBoxLayout()
        self.check_btn = QPushButton("Check Conda")
        self.check_btn.clicked.connect(self.check_conda_installation)
        btn_layout.addWidget(self.check_btn)

        self.activate_btn = QPushButton(
            "Get Activation Instructions (Existing Env)")
        self.activate_btn.clicked.connect(self.show_existing_activation_info)
        btn_layout.addWidget(self.activate_btn)

        self.create_btn = QPushButton("Create && Get Activation Instructions")
        self.create_btn.clicked.connect(self.create_and_show_info)
        btn_layout.addWidget(self.create_btn)

        layout.addLayout(btn_layout)

        existing_env_label = QLabel(
            "Existing Conda Environments:")  # Section label
        layout.addWidget(existing_env_label)
        self.conda_env_combo = QComboBox(self)
        layout.addWidget(self.conda_env_combo)

        self.refresh_conda_btn = QPushButton("Refresh List")
        self.refresh_conda_btn.clicked.connect(self.load_conda_envs)
        layout.addWidget(self.refresh_conda_btn)

        self.selected_env_label = QLabel("")
        self.selected_env_label.setProperty(
            "selection_label", True)  # For styling
        layout.addWidget(self.selected_env_label)

        if not check_conda():
            self.create_btn.setEnabled(False)
            self.check_btn.setEnabled(False)
            self.activate_btn.setEnabled(False)
            self.version_combo.setEnabled(False)
            self.name_edit.setEnabled(False)
            self.conda_env_combo.setEnabled(False)
            self.refresh_conda_btn.setEnabled(False)
            log_error("Conda is not installed.", self.console)  # Use log_error
            self.status_bar.showMessage("Conda is not installed.", 3000)

        self.load_conda_envs()
        self.load_and_display()

    def showEvent(self, event):
        """Override showEvent to refresh conda env list when page is shown."""
        super().showEvent(event)
        self.load_conda_envs()
        self.load_and_display()

    def check_conda_installation(self):
        if check_conda():
            msg = "Conda is installed."
            log_success(msg, self.console)  # Use log_success
        else:
            msg = "Conda is not installed."
            log_info(msg, self.console)  # Use log_info
            self.create_btn.setEnabled(False)
        self.console.appendPlainText(msg)
        self.status_bar.showMessage(msg, 3000)

    def load_conda_envs(self):
        """Loads the list of conda environments."""
        self.conda_env_combo.clear()
        envs = list_conda_envs()
        if not envs:
            self.conda_env_combo.addItem("No conda envs found.")
            self.conda_env_combo.setEnabled(False)
            self.activate_btn.setEnabled(False)
        else:
            self.conda_env_combo.setEnabled(True)
            self.activate_btn.setEnabled(True)
            self.conda_env_combo.addItems(envs)

    def show_existing_activation_info(self):
        """Shows activation instructions for an existing conda environment."""
        selected = self.conda_env_combo.currentText()
        if selected == "No conda envs found.":
            return

        save_selected_env("conda", selected)  # Save selection
        self.load_and_display()

        msg = (
            f"Conda environment '{selected}' selected.\n"
            f"To activate it, open a *NEW* terminal (e.g., Conda Prompt, PowerShell) and run:\n\n"
            f"    conda activate {selected}\n\n"
            f"This application cannot directly activate the environment.\n\n"
            f"Click 'Launch New Terminal' to open a new terminal with the environment activated."
        )

        # ✅ Use QMessageBox with correct button detection
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Information)
        dialog.setText(msg)
        dialog.setTextFormat(Qt.TextFormat.RichText)
        dialog.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        dialog.setWindowTitle("Activation Instructions")
        dialog.setStandardButtons(
            QMessageBox.Ok | QMessageBox.Open)  # ✅ Use proper buttons
        dialog.setDefaultButton(QMessageBox.Ok)
        dialog.button(QMessageBox.Open).setText(
            "Launch New Terminal")  # ✅ Rename button for clarity

        result = dialog.exec()

        if result == QMessageBox.Open:  # ✅ Correct button check
            # ✅ Calls CMD to activate Conda env
            launch_activated_cmd("conda", selected, self.console)

    def create_and_show_info(self):
        """Creates a conda environment using a worker thread."""
        name = self.name_edit.text().strip()
        version = self.version_combo.currentText()

        try:
            final_name = create_conda_env(name, version, self.console)  # Ensure self.console is passed
            msg = f"Conda environment '{final_name}' creation started..."
            log_success(msg, self.console)
            self.status_bar.showMessage(msg, 3000)
            save_selected_env("conda", final_name)
            self.load_conda_envs()
            self.load_and_display()

            # Create worker thread to run conda create command
            self.install_worker = InstallWorker(["conda", "create", "-n", final_name, f"python={version}", "-y"], self.console, final_name) # Pass final_name
            self.install_worker.output_signal.connect(self.console.appendPlainText)  # Connect output signal
            self.install_worker.finished_signal.connect(lambda code, env: self.handle_conda_process_completion(code, env)) # Connect finished signal with lambda for arguments
            self.install_worker.start() # Start the worker thread

        except Exception as e:
            msg = f"Error starting conda environment creation: {e}"
            log_error(msg, self.console)
            self.status_bar.showMessage(msg, 5000)

    def handle_conda_process_completion(self, return_code, env_name):  # New handler for process completion
        """Handles the completion of the conda create process from the worker thread."""
        console = self.console  # Access console from page instance
        if return_code == 0:
            success_msg = f" Conda environment '{env_name}' created successfully!"
            log_success(success_msg, console)
            self.status_bar.showMessage("Conda environment created.", 3000)

            # Refresh conda env list after creation
            self.load_conda_envs()
            self.load_and_display()

            # Launch activated CMD after successful creation
            launch_activated_cmd("conda", env_name, console)  # Pass console here too

        else:
            error_msg = f" Failed to create conda environment '{env_name}'. Error code: {return_code}"
            log_error(error_msg, console)
            self.status_bar.showMessage("Conda environment creation failed.", 5000)
            QMessageBox.critical(self, "Error", f"Conda environment creation failed. See console for details. Error code: {return_code}")


    def show_activation_info(self, conda_env_name=None):
        """Displays activation instructions and launches CMD if requested for a newly created Conda env."""
        if not conda_env_name:
            log_error("Error: No Conda environment name provided.", self.console)
            return

        msg = (
            f"Conda environment '{conda_env_name}' created and selected.\n"
            f"To activate it, open a *NEW* terminal and run:\n\n"
            f"    conda activate {conda_env_name}\n\n"
            f"This application cannot directly activate the environment.\n\n"
            f"Click 'Launch New Terminal' to open a new terminal."
        )

        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Information)
        dialog.setText(msg)
        dialog.setTextFormat(Qt.TextFormat.RichText)
        dialog.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        dialog.setWindowTitle("Activation Instructions")
        dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Open)
        dialog.button(QMessageBox.Open).setText("Launch Activated CMD")
        dialog.setDefaultButton(QMessageBox.Ok)

        result = dialog.exec()

        if result == QMessageBox.Open:
            try:
                log_info(f"Attempting to launch CMD with conda activation for: {conda_env_name}", self.console)

                if sys.platform == 'win32':
                    creationflags = subprocess.CREATE_NEW_CONSOLE
                else:
                    creationflags = 0

                # ✅ Fix: Correct variable name
                launch_activated_cmd("conda", conda_env_name, self.console)

            except Exception as e:
                error_msg = f"Error launching CMD: {e}"
                log_error(error_msg, self.console)

    def load_and_display(self):
        """Loads and displays the currently selected environment."""
        env_type, env_name = load_selected_env()
        if env_type == "conda" and env_name:
            self.selected_env_label.setText(f"Selected conda env: {env_name}")
        else:
            self.selected_env_label.setText("No conda env selected")


class PlaceholderPage(QWidget):
    """A generic placeholder page."""

    def __init__(self, title, stack, console, status_bar):
        super().__init__()
        self.stack, self.console, self.status_bar = stack, console, status_bar
        layout = QVBoxLayout(self)
        layout.setSpacing(10)  # Add vertical spacing
        # Add margins around the page
        layout.setContentsMargins(15, 15, 15, 15)

        title_label = QLabel(f"{title}")  # Title from constructor
        title_label.setProperty("page_title", True)  # For styling
        layout.addWidget(title_label)
        # Placeholder content info
        layout.addWidget(QLabel(f"{title} page (placeholder content)"))


# --- Install Python Page ---
class InstallPythonPage(QWidget):
    """Page for installing Python (if missing)."""

    def __init__(self, stack, console, status_bar):
        super().__init__()
        self.stack, self.console, self.status_bar = stack, console, status_bar
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        title_label = QLabel("Install Python")
        title_label.setProperty("page_title", True)
        layout.addWidget(title_label)
        layout.addWidget(QLabel("Install Python (if missing)"))

        version_label = QLabel("Select Python Version to Install:")
        layout.addWidget(version_label)
        self.version_combo = QComboBox(self)
        self.version_combo.addItems(["3.8", "3.9", "3.10", "3.11", "3.12"])
        layout.addWidget(self.version_combo)

        btn_layout = QHBoxLayout()

        self.check_btn = QPushButton(
            "Check Python Version")
        btn_layout.addWidget(self.check_btn)
        self.check_btn.clicked.connect(
            self.check_python_version)

        self.install_btn = QPushButton(
            "Install Python")
        btn_layout.addWidget(self.install_btn)
        self.install_btn.clicked.connect(self.start_python_installation) # Changed connection to start_python_installation
        self.install_btn.setEnabled(False) # Initially disabled

        layout.addLayout(btn_layout)

    def check_python_version(self):
        """Checks if the selected Python version is installed."""
        version = self.version_combo.currentText()
        try:
            subprocess.check_output(
                ["py", f"-{version}", "--version"], stderr=subprocess.STDOUT)
            msg = f"Python {version} is already installed."
            self.status_bar.showMessage(msg, 3000)
            log_success(msg, self.console)
            self.install_btn.setEnabled(False) # Disable Install button if installed

        except subprocess.CalledProcessError:
            msg = f"Python {version} is not installed. Ready to install."
            self.status_bar.showMessage(msg, 3000)
            log_info(msg, self.console)
            self.install_btn.setEnabled(True) # Enable Install button if not installed


    def start_python_installation(self): # NEW - Start installation using worker
        """Starts Python installation in a separate thread."""
        version = self.version_combo.currentText()
        self.install_btn.setEnabled(False) # Disable Install button during install
        msg = f"Downloading and installing Python {version}..."
        log_info(msg, self.console)
        self.status_bar.showMessage("Downloading Python installer...", 0) # Show indefinite progress message

        self.install_worker = InstallWorker( # Create worker thread
            lambda: download_and_install_python(version, self.console), # Use lambda to pass function with arguments
            self.console,
            version # Pass version as env_name (can be used for logging in worker if needed)
        )
        self.install_worker.output_signal.connect(self.console.appendPlainText) # Connect output
        self.install_worker.finished_signal.connect(lambda code, env: self.handle_python_install_completion(code, version)) # Connect finished signal
        self.install_worker.start() # Start worker thread


    def handle_python_install_completion(self, return_code, version): # NEW - Handle install completion
        """Handles the completion of the Python installation process."""
        self.status_bar.clearMessage() # Clear indefinite progress message
        self.install_btn.setEnabled(True) # Re-enable Install button

        if return_code == 0:
            msg = f"Python {version} installed successfully."
            QMessageBox.information(
                self, "Installation Complete", msg)
            log_success(msg, self.console)
            self.status_bar.showMessage("Python installation complete.", 3000)
            self.install_btn.setEnabled(False) # Disable Install button after success

        else:
            msg = f"Failed to install Python {version}."
            QMessageBox.critical(
                self, "Installation Failed", msg)
            log_error(msg, self.console)
            self.status_bar.showMessage("Python installation failed.", 5000)

class InstallPyTorchPage(QWidget):
    """Page for installing PyTorch & CUDA."""

    def __init__(self, stack, console, status_bar):
        super().__init__()
        self.stack, self.console, self.status_bar = stack, console, status_bar
        layout = QVBoxLayout(self)
        layout.setSpacing(10)  # Add vertical spacing
        # Add margins around the page
        layout.setContentsMargins(15, 15, 15, 15)

        title_label = QLabel("Install PyTorch / CUDA")  # Consistent title
        title_label.setProperty("page_title", True)  # For styling
        layout.addWidget(title_label)

        os_label = QLabel("Operating System:")  # Label above dropdown
        layout.addWidget(os_label)
        # OS Dropdown (Windows only for now)
        self.os_combo = QComboBox(self)
        self.os_combo.addItem("Windows")  # For now, only Windows is supported
        # Disable OS dropdown for now (Windows-only)
        self.os_combo.setEnabled(False)
        layout.addWidget(self.os_combo)  # Add OS dropdown

        package_manager_label = QLabel(
            "Package Manager:")  # Label above radio buttons
        layout.addWidget(package_manager_label)
        # Package Manager Radio Buttons
        self.package_manager_layout = QHBoxLayout()
        self.pip_radio = QRadioButton("Pip")  # Pip Radio Button
        self.conda_radio = QRadioButton("Conda")  # Conda Radio Button
        self.package_manager_layout.addWidget(self.pip_radio)
        self.package_manager_layout.addWidget(self.conda_radio)
        self.pip_radio.setChecked(True)  # Default to Pip
        # Add Radio Button layout
        layout.addLayout(self.package_manager_layout)

        # Create Package Manager Button Group
        self.package_manager_group = QButtonGroup(self)  # Create ButtonGroup
        self.package_manager_group.addButton(self.pip_radio)  # Add radio buttons to group
        self.package_manager_group.addButton(self.conda_radio)

        python_version_label = QLabel(
            "Python Version:")  # Label above dropdown
        layout.addWidget(python_version_label)
        # Python Version Dropdown (Placeholder List)
        self.python_combo = QComboBox(self)
        self.python_combo.addItems(
            ["3.8", "3.9", "3.10", "3.11", "3.12"])  # Placeholder list
        layout.addWidget(self.python_combo)  # Add Python Version dropdown

        compute_platform_label = QLabel(
            "Compute Platform:")  # Label above radio buttons
        layout.addWidget(compute_platform_label)
        # CPU/CUDA Radio Buttons
        # Reusing the variable name - layout was already added
        self.device_layout = QHBoxLayout()
        self.cpu_radio = QRadioButton("CPU-only")  # CPU Radio Button
        self.cuda_radio = QRadioButton("CUDA")  # CUDA Radio Button
        self.device_layout.addWidget(self.cpu_radio)
        self.device_layout.addWidget(self.cuda_radio)
        self.cpu_radio.setChecked(True)  # Default to CPU
        # Add CPU/CUDA radio buttons layout
        layout.addLayout(self.device_layout)

        # Create Compute Platform Button Group
        self.device_group = QButtonGroup(self)  # Create ButtonGroup
        self.device_group.addButton(self.cpu_radio)  # Add radio buttons to group
        self.device_group.addButton(self.cuda_radio)

        cuda_version_label = QLabel("CUDA Version:")  # Label above dropdown
        layout.addWidget(cuda_version_label)
        # CUDA Version Dropdown (Conditional - Hidden initially)
        self.cuda_version_combo = QComboBox(self)
        self.cuda_version_combo.addItems(
            ["CUDA 11.8", "CUDA 12.1", "CUDA 12.4"])  # Placeholder CUDA versions
        # Initially Hidden - shown only when CUDA is selected
        self.cuda_version_combo.setVisible(False)
        layout.addWidget(self.cuda_version_combo)  # Add CUDA Version dropdown

        # Torchvision Checkbox
        self.torchvision_checkbox = QCheckBox(
            "Include Torchvision")  # Torchvision Checkbox
        layout.addWidget(self.torchvision_checkbox)

        # Label above text area
        command_label = QLabel("Installation Command:")
        layout.addWidget(command_label)
        # Installation Command Text Area (Read-Only Placeholder)
        self.command_output = QPlainTextEdit()  # Read-only Text Area
        self.command_output.setReadOnly(True)
        self.command_output.setPlainText(
            "Installation command will be generated here based on your selections.")  # Placeholder text
        layout.addWidget(self.command_output)

        # Buttons Layout (Horizontal)
        btn_layout = QHBoxLayout()

        self.copy_command_btn = QPushButton(
            "Copy Command to Clipboard")  # Copy Command Button
        btn_layout.addWidget(self.copy_command_btn)
        # Button click connection will be added later

        self.install_btn = QPushButton(
            "Install PyTorch")  # Install PyTorch Button
        btn_layout.addWidget(self.install_btn)
        # Button click connection will be added later

        layout.addLayout(btn_layout)  # Add Buttons Layout


    def install_pytorch(self):
        """Placeholder for PyTorch installation logic."""
        version = self.python_combo.currentText()
        use_cuda = self.cuda_radio.isChecked()
        include_torchvision = self.torchvision_checkbox.isChecked()

        device_type = "CUDA" if use_cuda else "CPU"  # Determine device type string

        msg = (
            f"Starting PyTorch installation (placeholder):\n"
            f"  Version: {version}\n"
            f"  Device: {device_type}\n"
            f"  Include Torchvision: {'Yes' if include_torchvision else 'No'}\n"
            # Indicate placeholder
            f"\n**Installation process (placeholder) started...**\n"
            # Clarify placeholder status
            f"**In a future version, this will actually install PyTorch.**"
        )
        log_info(msg, self.console)  # Use log_info
        self.status_bar.showMessage(
            "PyTorch installation (placeholder) started...", 5000)
        QMessageBox.information(self, "PyTorch Installation",
                                "Placeholder Installation Started!\n\nCheck console for details.")  # Informative popup
