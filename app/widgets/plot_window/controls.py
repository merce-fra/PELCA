import io

import plotly.graph_objects as go
import plotly.io as pio
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PIL import Image
from plotly.io import to_html
from PySide6.QtCore import QObject, Qt, QUrl, Signal
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QFrame,
                               QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                               QMessageBox, QPushButton, QSplitter,
                               QStackedWidget, QTextEdit, QToolButton,
                               QVBoxLayout, QWidget)

from app.models.console import ConsoleOutputRedirector
from app.models.plot import ModeSwitcher
from app.threads.process_excel import ProcessExcel
from app.utils.legacy import get_max_fig_size
from app.widgets.header import HeaderWidget


class ControlsWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.figs = parent.figs
        self.index = parent.index
        self.layout = QVBoxLayout()
        self.setup_ui()
        self.setLayout(self.layout)

    def update_mode_label(self, plotly_mode):
        if plotly_mode:
            self.mode_label.setText("Current mode: Plotly")
            self.switch_plot_button.setText("DEMO - Switch to Matplotlib")
        else:
            self.mode_label.setText("Current mode: Matplotlib")
            self.switch_plot_button.setText("DEMO - Switch to Plotly")

    def setup_ui(self):
        # Title Label
        self.layout.addWidget(HeaderWidget())

        # Save plot buttons
        self.save_plot_button = QPushButton("Save current plot")
        self.save_all_plot_button = QPushButton("Save all plots")
        self.switch_plot_button = QPushButton("TEST - Init plot frame")

        self.parent.mode_switcher = ModeSwitcher()
        self.switch_plot_button.clicked.connect(self.parent.mode_switcher.switch_mode)
        # Adding a separator between title and buttons
        self.mode_label = QLabel("Current mode: Matplotlib")
        self.parent.mode_switcher.mode_changed.connect(self.update_mode_label)
        self.add_separator()

        self.layout.addWidget(self.save_plot_button)
        self.layout.addWidget(self.save_all_plot_button)
        self.layout.addWidget(self.switch_plot_button)
        self.layout.addWidget(ImageButtonsWidget(self))
        self.add_separator()

        # Options Label
        options_label = QLabel(f"Select Options for data export :")
        self.layout.addWidget(options_label)

        # Checkboxes
        self.checkbox1 = QCheckBox("Impact total")
        self.checkbox2 = QCheckBox("Impacdt manufacturing")
        self.checkbox3 = QCheckBox("Impact use")
        self.checkbox4 = QCheckBox("Fault cause")
        self.checkbox5 = QCheckBox("RU age")

        # Adding checkboxes to the layout
        self.layout.addWidget(self.checkbox1)
        self.layout.addWidget(self.checkbox2)
        self.layout.addWidget(self.checkbox3)
        self.layout.addWidget(self.checkbox4)
        self.layout.addWidget(self.checkbox5)

        # Save Data Button
        self.save_data_button = QPushButton("Save data to Excel")
        self.save_data_button.clicked.connect(self.save_selection)
        self.layout.addWidget(self.save_data_button)

    def add_separator(self):
        # Creating a horizontal line separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(separator)

    def save_selection(self):
        selected_options = []
        if self.checkbox1.isChecked():
            selected_options.append(self.checkbox1.text())
        if self.checkbox2.isChecked():
            selected_options.append(self.checkbox2.text())
        if self.checkbox3.isChecked():
            selected_options.append(self.checkbox3.text())
        if self.checkbox4.isChecked():
            selected_options.append(self.checkbox4.text())
        if self.checkbox5.isChecked():
            selected_options.append(self.checkbox5.text())


class ImageButtonsWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        def create_thumbnail(fig, size=(100, 100)):
            """Crée une image miniature de la figure pour la compatibilité avec PySide6"""
            with io.BytesIO() as buf:
                fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
                buf.seek(0)
                img = Image.open(buf)
                img.thumbnail(size)
                qimage = QImage(img.tobytes(), img.width, img.height, QImage.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qimage)
                label = QLabel()
                label.setPixmap(pixmap)
                return label

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.thumbnails = []
        for idx, fig in enumerate(parent.figs["matplotlib"]):
            thumbnail = create_thumbnail(fig)
            button = QPushButton()
            button.setIcon(QIcon(thumbnail.pixmap()))
            button.setIconSize(thumbnail.pixmap().rect().size())
            button.clicked.connect(lambda checked, index=idx: parent.index.set_index(index))

            self.layout.addWidget(button)
            self.thumbnails.append(button)
