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
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QFrame,
                               QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                               QMessageBox, QPushButton, QSplitter,
                               QStackedWidget, QTextEdit, QToolButton,
                               QVBoxLayout, QWidget)

from app.utils.legacy import export_data, export_data_excel, get_max_fig_size
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
                    fig = self.figs[self.index]
                    filepath = os.path.join(folder_path, f"selected_plot_{self.index + 1}.svg")
                    fig.savefig(filepath, dpi=300)
                    print(f"Selected plot saved successfully as {filepath}")
                except Exception as e:
                    print(f"An error occurred while saving the selected plot: {e}")
        else:
            print("No plots available to save.")

    def save_data(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Save Data")
        if folder_path:
            try:
                if self.checkbox_impact_total.isChecked():
                    export_data(folder_path, "Impact_total", self.figs["plot_data"]["EI"])
                if self.checkbox_impact_manufacturing.isChecked():
                    export_data(folder_path, "Impact_manu", self.figs["plot_data"]["EI_manu"])
                if self.checkbox_impact_use.isChecked():
                    export_data(folder_path, "Impact_use", self.figs["plot_data"]["EI_use"])
                if self.checkbox_fault_cause.isChecked():
                    export_data(folder_path, "fault_cause", self.figs["plot_data"]["fault_cause"])
                if self.checkbox_ru_age.isChecked():
                    export_data(folder_path, "RU_age", self.figs["plot_data"]["RU_age"])
                print(f"Selected data saved successfully in {folder_path}")
            except Exception as e:
                print(f"An error occurred while saving the data: {e}")

    def save_data_excel(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Save Data")
        if folder_path:
            try:
                if self.checkbox_impact_total.isChecked():
                    export_data_excel(folder_path, "Impact_total", self.figs["plot_data"]["EI"])
                if self.checkbox_impact_manufacturing.isChecked():
                    export_data_excel(folder_path, "Impact_manu", self.figs["plot_data"]["EI_manu"])
                if self.checkbox_impact_use.isChecked():
                    export_data_excel(folder_path, "Impact_use", self.figs["plot_data"]["EI_use"])
                if self.checkbox_fault_cause.isChecked():
                    export_data_excel(folder_path, "fault_cause", self.figs["plot_data"]["fault_cause"])
                if self.checkbox_ru_age.isChecked():
                    export_data_excel(folder_path, "RU_age", self.figs["plot_data"]["RU_age"])
            except Exception as e:
                print(f"An error occurred while saving the data: {e}")

    def setup_ui(self):
            # Title Label
            self.layout.addWidget(HeaderWidget())

            # Save plot buttons
            self.save_plot_button = QPushButton("Save current plot")
            self.save_plot_button.setFixedHeight(30)

            self.save_all_plot_button = QPushButton("Save all plots")
            self.save_all_plot_button.setFixedHeight(30)

            self.switch_plot_button = QPushButton("TEST - Init plot frame")
            self.switch_plot_button.setFixedHeight(30)

            self.save_plot_button.clicked.connect(self.save_selected_plot)
            self.save_all_plot_button.clicked.connect(self.save_plots)

            # Adding a separator between title and buttons
            self.add_separator()

            self.layout.addWidget(self.save_plot_button)
            self.layout.addWidget(self.save_all_plot_button)
            self.layout.addWidget(self.switch_plot_button)
            # self.layout.addWidget(ImageButtonsWidget(self))
            self.add_separator()

            # Options Label
            options_label = QLabel("Select Options for data export :")
            options_label.setFixedHeight(20)
            self.layout.addWidget(options_label)

            # Checkboxes
            self.checkbox_impact_total = QCheckBox("Impact total")
            self.checkbox_manufacturing = QCheckBox("Impact manufacturing")
            self.checkbox_use = QCheckBox("Impact use")
            self.checkbox_fault_cause = QCheckBox("Fault cause")
            self.checkbox_ru_age = QCheckBox("RU age")

            self.layout.addWidget(self.checkbox_impact_total)
            self.layout.addWidget(self.checkbox_manufacturing)
            self.layout.addWidget(self.checkbox_use)
            self.layout.addWidget(self.checkbox_fault_cause)
            self.layout.addWidget(self.checkbox_ru_age)

            # Save Data Button
            self.save_data_button = QPushButton("Save data")
            self.save_data_button.setFixedHeight(30)

            self.save_excel_button = QPushButton("Save data to excel")
            self.save_excel_button.setFixedHeight(30)

            self.save_excel_button.clicked.connect(self.save_data_excel)
            self.save_data_button.clicked.connect(self.save_data)
            
            self.layout.addWidget(self.save_data_button)
            self.layout.addWidget(self.save_excel_button)

    def add_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(separator)


class ImageButtonsWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        def create_thumbnail(fig, size=(100, 100)):
            """Crée une image miniature de la figure Plotly pour la compatibilité avec PySide6"""
            # Utiliser plotly.io.to_image pour convertir la figure Plotly en image PNG
            if fig['type'] == 'plotly':
                img_bytes = pio.to_image(fig['plot'], format="png")
                
                # Ouvrir l'image avec PIL
                img = Image.open(io.BytesIO(img_bytes))
                img.thumbnail(size)  # Créer la miniature
                img = img.convert("RGBA")  # Convertir l'image en mode RGBA pour assurer la compatibilité avec PySide6

            # Convertir l'image en QImage pour l'affichage avec PySide6
                qimage = QImage(img.tobytes(), img.width, img.height, img.width * 4, QImage.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qimage)
                
                # Créer un QLabel pour afficher l'image
                label = QLabel()
                label.setPixmap(pixmap)
                return label
            else:
                with io.BytesIO() as buf:
                    fig['plot'].savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
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
        for idx, fig in enumerate(parent.figs["plots"]):
            thumbnail = create_thumbnail(fig)
            button = QPushButton()
            button.setIcon(QIcon(thumbnail.pixmap()))
            button.setIconSize(thumbnail.pixmap().rect().size())
            button.clicked.connect(lambda checked, index=idx: self.parent.index.set_index(index))
            self.layout.addWidget(button)
            self.thumbnails.append(button)
