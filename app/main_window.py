import sys

from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QFrame,
                               QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                               QMessageBox, QPushButton, QSplitter, QTextEdit,
                               QVBoxLayout, QWidget)

import app.ressources.ressources_rc  # Import des ressources compilées
from app.threads.process_excel import ProcessExcel
from app.widgets.header import HeaderWidget
from app.widgets.plot_window.plot import PlotWindow
from app.widgets.script import ScriptWidget

class Communicator(QObject):
    close_window_signal = Signal()


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PELCA")
        self.setGeometry(100, 100, 600, 800)
        self.file_path_edit = None  # Initialize the file path edit field
        self.console_text = None  # Initialize the console text area
        self.is_running = False  # Flag to check if a script is running
        self._setup_ui()
        self.setWindowIcon(QIcon(":/ressources/icons/icon.ico"))

    def _setup_ui(self):
        """Set up the main UI components and layout."""
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        version_label = QLabel()

        with open("version.txt", "r") as file:
            version = file.read()
            version_label.setText(version)
            version_label.setAlignment(Qt.AlignRight)
            main_layout.addWidget(version_label)

        version_label.setText("v2.0.0")

        self.header = HeaderWidget()
        main_layout.addWidget(self.header)
        self.script_widget = ScriptWidget(parent=self)
        main_layout.addWidget(self.script_widget)
