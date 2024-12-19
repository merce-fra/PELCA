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




def fig_to_image(fig, dpi=300):
    if fig["type"] == "plotly":
        img_bytes = pio.to_image(fig["plot"], format="png", scale=1)
        img = Image.open(io.BytesIO(img_bytes))
        img = img.convert("RGBA")
        return img
    else:
        # Save the Matplotlib figure to a BytesIO object
        buf = io.BytesIO()
        fig["plot"].savefig(buf, format="png", dpi=dpi)
        buf.seek(0)  # Move to the beginning of the buffer
        img = Image.open(buf)
        img = img.convert("RGBA")
        return img


def fig_to_html(fig):
    if fig["type"] == "plotly":
        return to_html(fig["plot"], full_html=False)
    

def get_unique_filepath(folder, base_filename, extension):
    counter = 1
    filepath = os.path.join(folder, f"{base_filename}.{extension}")
    while os.path.exists(filepath):
        filepath = os.path.join(folder, f"{base_filename}_{counter}.{extension}")
        counter += 1
    return filepath


class ControlsWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.figs = parent.figs
        self.index = parent.index
        self.layout = QVBoxLayout()
        self.setup_ui()
        self.setLayout(self.layout)

    def save_plot(self, fig, png_folder, html_folder, prefix="default_plot"):
        try:
            # Créer les dossiers s'ils n'existent pas
            os.makedirs(png_folder, exist_ok=True)
            os.makedirs(html_folder, exist_ok=True)

            # Nettoyer le titre pour le nom de fichier
            safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in prefix)

            # Sauvegarde en PNG
            png_filepath = get_unique_filepath(png_folder, safe_title, "png")
            img = fig_to_image(fig)
            if img:
                img.save(png_filepath, format="PNG")

            # Sauvegarde en HTML
            html_filepath = get_unique_filepath(html_folder, safe_title, "html")
            html = fig_to_html(fig)
            if html:
                with open(html_filepath, 'w', encoding='utf-8') as f:
                    f.write(html)

            print(f"Plot saved successfully as PNG: '{png_filepath}' and HTML: '{html_filepath}'")
        except Exception as e:
            print(f"An error occurred while saving the plot: {e}")


    def save_plots(self):
        folder_path = self.figs['plot_data']['dic'].get('LCA_path', "")
        if folder_path:
            # Sous-dossiers pour PNG et HTML
            png_folder = os.path.join(folder_path, "plots", "png")
            html_folder = os.path.join(folder_path, "plots", "html")

            for fig in self.figs.get("plots", []):
                title = fig.get('title', "default_plot")
                self.save_plot(fig, png_folder, html_folder, prefix=title)

    def save_selected_plot(self):
        folder_path = self.figs['plot_data']['dic'].get('LCA_path', "")
        if folder_path:
            # Sous-dossiers pour PNG et HTML
            png_folder = os.path.join(folder_path, "plots", "png")
            html_folder = os.path.join(folder_path, "plots", "html")

            fig = self.figs["plots"][self.index.get_index()]
            title = fig.get('title', "default_plot")
            self.save_plot(fig, png_folder, html_folder, prefix=title)
 
    def save_data(self):
        # Dossier cible obtenu depuis le dictionnaire
        folder_path = self.figs['plot_data']['dic']['LCA_path']
        if folder_path:
            try:
                # Création du sous-dossier "numpy"
                numpy_folder = os.path.join(folder_path, "numpy")
                os.makedirs(numpy_folder, exist_ok=True)

                # Mapping des données et noms de fichiers
                export_mapping = {}
                if "EI" in self.figs["plot_data"]:
                    export_mapping["Impact_total"] = self.figs["plot_data"]["EI"]
                if "EI_manu" in self.figs["plot_data"]:
                    export_mapping["Impact_manu"] = self.figs["plot_data"]["EI_manu"]
                if "EI_use" in self.figs["plot_data"]:
                    export_mapping["Impact_use"] = self.figs["plot_data"]["EI_use"]
                if "fault_cause" in self.figs["plot_data"]:
                    export_mapping["fault_cause"] = self.figs["plot_data"]["fault_cause"]
                if "RU_age" in self.figs["plot_data"]:
                    export_mapping["RU_age"] = self.figs["plot_data"]["RU_age"]

                # Exportation des données avec gestion des doublons
                for base_filename, data in export_mapping.items():
                    filename = f"{base_filename}"
                    path_file = os.path.join(numpy_folder, f"{filename}.npy")

                    # Gestion des doublons avec incrémentation
                    counter = 1
                    while os.path.exists(path_file):
                        filename = f"{base_filename}_{counter}"
                        path_file = os.path.join(numpy_folder, f"{filename}.npy")
                        counter += 1

                    # Appel à la fonction export_data
                    export_data(numpy_folder, filename, data)

                print(f"All NumPy data saved successfully in {numpy_folder}")
            except Exception as e:
                print(f"An error occurred while saving NumPy data: {e}")


    def save_data_excel(self):
        folder_path = self.figs['plot_data']['dic']['LCA_path']
        if folder_path:
            try:
                # Création du sous-dossier "excel"
                excel_folder = os.path.join(folder_path, "excel")
                os.makedirs(excel_folder, exist_ok=True)

                # Mapping des données et noms de fichiers
                export_mapping = {}
                if "EI" in self.figs["plot_data"]:
                    export_mapping["Impact_total"] = self.figs["plot_data"]["EI"]
                if "EI_manu" in self.figs["plot_data"]:
                    export_mapping["Impact_manu"] = self.figs["plot_data"]["EI_manu"]
                if "EI_use" in self.figs["plot_data"]:
                    export_mapping["Impact_use"] = self.figs["plot_data"]["EI_use"]
                if "fault_cause" in self.figs["plot_data"]:
                    export_mapping["fault_cause"] = self.figs["plot_data"]["fault_cause"]
                if "RU_age" in self.figs["plot_data"]:
                    export_mapping["RU_age"] = self.figs["plot_data"]["RU_age"]

                # Exportation des données avec gestion des doublons
                for base_filename, data in export_mapping.items():
                    filename = f"{base_filename}"
                    path_file = os.path.join(excel_folder, f"{filename}.xlsx")

                    # Gestion des doublons avec incrémentation
                    counter = 1
                    while os.path.exists(path_file):
                        filename = f"{base_filename}_{counter}"
                        path_file = os.path.join(excel_folder, f"{filename}.xlsx")
                        counter += 1

                    # Appel à la fonction export_data_excel
                    export_data_excel(excel_folder, filename, data)

                print(f"All Excel data saved successfully in {excel_folder}")
            except Exception as e:
                print(f"An error occurred while saving Excel data: {e}")

    def setup_ui(self):
            # Title Label
            self.layout.addWidget(HeaderWidget())

            # Save plot buttons
            self.save_plot_button = QPushButton("Save current plot")
            self.save_plot_button.setFixedHeight(30)

            self.save_all_plot_button = QPushButton("Save all plots")
            self.save_all_plot_button.setFixedHeight(30)

            self.save_plot_button.clicked.connect(self.save_selected_plot)
            self.save_all_plot_button.clicked.connect(self.save_plots)

            # Adding a separator between title and buttons
            self.add_separator()

            self.layout.addWidget(self.save_plot_button)
            self.layout.addWidget(self.save_all_plot_button)
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

    

            # Save Data Button
            self.save_data_button = QPushButton("Save data to numpy array")
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
