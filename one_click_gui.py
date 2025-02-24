#!/usr/bin/env python
"""
one_click_gui.py - Main GUI Entry Point
---------------------------------------
This file contains the main function and the MainWindow class,
which sets up the main application window, layout, side menu,
stacked widget for pages, and applies the global stylesheet.

It imports UI page classes from ui_pages.py and relies on
backend functions from backend_functions.py for core logic.
"""

import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPlainTextEdit, QStackedWidget, QSplitter, QStatusBar, QLabel, QPushButton
)

from ui_pages import (
    SideMenu, CreateVenvPage, ActivateEnvPage, CreateCondaPage,
    InstallPyTorchPage, PlaceholderPage, InstallPythonPage
)

class KamiSetup(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KamiSetup - AI Environment Installer")

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(200)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.addWidget(QWidget())
        self.stack.addWidget(CreateVenvPage(self.stack, self.console, self.status_bar))
        self.stack.addWidget(ActivateEnvPage(self.stack, self.console, self.status_bar))
        self.stack.addWidget(CreateCondaPage(self.stack, self.console, self.status_bar))
        self.stack.addWidget(InstallPyTorchPage(self.stack, self.console, self.status_bar))
        self.stack.addWidget(PlaceholderPage("Install ONNX", self.stack, self.console, self.status_bar))
        self.stack.addWidget(PlaceholderPage("Install Dependencies", self.stack, self.console, self.status_bar))
        self.stack.addWidget(InstallPythonPage(self.stack, self.console, self.status_bar))
        self.stack.addWidget(PlaceholderPage("Full AI Setup", self.stack, self.console, self.status_bar))

        self.side_menu = SideMenu(self.stack, self.console, self.status_bar)
        content_layout.addWidget(self.side_menu)
        content_layout.addWidget(self.stack)

        main_layout.addLayout(content_layout)
        main_layout.addWidget(self.console)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: "Segoe UI", "Arial";
                font-size: 10pt;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                border: none;
            }
            QLabel {
                color: #ffffff;
                margin-bottom: 3px;
            }
            QPushButton {
                background-color: #292929;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #666;
            }
            QPushButton:pressed {
                background-color: #2b2b2b;
            }
            QPlainTextEdit {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #444;
                font-family: monospace;
                font-size: 9pt;
            }
            QStatusBar {
                color: #ffffff;
            }
        """)

        self.resize(950, 750)


def main():
    app = QApplication(sys.argv)
    window = KamiSetup()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()