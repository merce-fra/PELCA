import io
import os

import plotly.graph_objects as go
import plotly.io as pio
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PIL import Image
from plotly.io import to_html
from PySide6.QtCore import QObject, Qt, QUrl, Signal
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWebEngineWidgets import QWebEngineView
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

    def save_plots(self):
        if self.figs["matplotlib"]:
            folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Save Plots")
            if folder_path:
                try:
                    for idx, fig in enumerate(self.figs["matplotlib"]):
                        filepath = os.path.join(folder_path, f"plot_{idx+1}.svg")
                        fig.savefig(filepath, dpi=300)
                    print(f"All plots saved successfully in {folder_path}")
                except Exception as e:
                    print(f"An error occurred while saving the plots: {e}")

    def save_selected_plot(self):
        if self.figs["matplotlib"]:
            folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Save Selected Plot")
            if folder_path:
                try:
                    fig = self.figs[self.current_index]
                    filepath = os.path.join(folder_path, f"selected_plot_{self.index + 1}.svg")
                    fig.savefig(filepath, dpi=300)
                    print(f"Selected plot saved successfully as {filepath}")
                except Exception as e:
                    print(f"An error occurred while saving the selected plot: {e}")
        else:
            print("No plots available to save.")

    def save_data_to_excel(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Save Data")
        if folder_path:
            try:
                if self.var_EI.get():
                    export_data(folder_path, "Impact_total", EI)
                if self.var_EI_manu.get():
                    export_data(folder_path, "Impact_manu", EI_manu)
                if self.var_EI_use.get():
                    export_data(folder_path, "Impact_use", EI_use)
                if self.var_fault_cause.get():
                    export_data(folder_path, "fault_cause", fault_cause)
                if self.var_RU_age.get():
                    export_data(folder_path, "RU_age", RU_age)
                print(f"Selected data saved successfully in {folder_path}")
            except Exception as e:
                print(f"An error occurred while saving the data: {e}")

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
        self.checkbox_impact_total = QCheckBox("Impact total")
        self.checkbox_impact_manufacturing = QCheckBox("Impact manufacturing")
        self.checkbox_impact_use = QCheckBox("Impact use")
        self.checkbox_fault_cause = QCheckBox("Fault cause")
        self.checkbox_ru_age = QCheckBox("RU age")

        # Adding checkboxes to the layout
        self.layout.addWidget(self.checkbox_impact_total)
        self.layout.addWidget(self.checkbox_impact_manufacturing)
        self.layout.addWidget(self.checkbox_impact_use)
        self.layout.addWidget(self.checkbox_fault_cause)
        self.layout.addWidget(self.checkbox_ru_age)

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
