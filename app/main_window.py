import sys

from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QFrame,
                               QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                               QMessageBox, QPushButton, QSplitter, QTextEdit,
                               QVBoxLayout, QWidget)

from app.models.console import ConsoleOutputRedirector
from app.threads.process_excel import ProcessExcel
from app.widgets.header import HeaderWidget
from app.widgets.plot import PlotWindow
from app.widgets.script import ScriptWidget
from src.utils import get_max_fig_size


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
        # self.console_output_redirector = ConsoleOutputRedirector()  # Console output redirection
        self._setup_ui()
        # self.console_output_redirector.new_text.connect(self.update_console)
        self.figs = []

    def _setup_ui(self):
        """Set up the main UI components and layout."""
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        self.header = HeaderWidget()
        main_layout.addWidget(self.header)
        self.script_widget = ScriptWidget(parent=self)
        main_layout.addWidget(self.script_widget)

        self.result_window = PlotWindow(parent=self)
        self.result_window.show()
