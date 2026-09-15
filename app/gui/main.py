"""Top-level application window.

Exposes ``MainWindow``, a ``QMainWindow`` subclass that assembles the full GUI
layout: a version/contact bar, ``HeaderWidget`` (banner image), and ``RunPanel``
(file selection, run buttons, live console). Instantiated by ``main_gui.py``.
"""

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

import app.gui.resources.ressources_rc  # type: ignore # noqa: F401 – registers Qt resources
from app.gui.header import HeaderWidget
from app.gui.launch.run_panel import RunPanel


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, version: str) -> None:
        super().__init__()
        self.version = version
        self.setWindowTitle("PELCA")
        self.setGeometry(200, 200, 600, 800)
        self.file_path_edit = None  # Initialize the file path edit field
        self.console_text = None  # Initialize the console text area
        self.is_running = False  # Flag to check if a script is running
        self._setup_ui()
        self.setWindowIcon(QIcon(":/ressources/icons/icon.ico"))
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(":/ressources/icons/icon.ico"))
        self.tray_icon.show()

    def _setup_ui(self):
        """Set up the main UI components and layout."""
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        top_bar = QHBoxLayout()
        contact_btn = QPushButton("Contact us")
        contact_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        contact_btn.clicked.connect(self._open_mail_client)
        top_bar.addWidget(contact_btn, 0, Qt.AlignmentFlag.AlignLeft)

        # Version label
        version_label = QLabel(self.version)
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top_bar.addWidget(version_label, 1)

        main_layout.addLayout(top_bar)

        self.header = HeaderWidget()
        main_layout.addWidget(self.header)

        # Create a horizontal layout for script and form widgets
        self.script_form_layout = QHBoxLayout()
        self.script_widget = RunPanel(parent=self)
        self.script_form_layout.addWidget(self.script_widget)
        self.params = False
        main_layout.addLayout(self.script_form_layout)

    def _open_mail_client(self) -> None:
        """Open the default mail client with a new composition window."""
        QDesktopServices.openUrl(QUrl("mailto:pelca@fr.merce.mee.com"))
