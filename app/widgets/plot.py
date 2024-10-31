import plotly.graph_objects as go
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QMainWindow, QPushButton, QSplitter, QTextEdit,
                               QVBoxLayout, QWidget)

from app.models.console import ConsoleOutputRedirector
from app.threads.process_excel import ProcessExcel
from app.widgets.header import HeaderWidget
from src.utils import get_max_fig_size

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QHBoxLayout, QCheckBox, QFileDialog, QLineEdit
from PySide6.QtWidgets import QMessageBox, QFrame
from PySide6.QtWidgets import QHBoxLayout, QSplitter
from PySide6.QtWidgets import QToolButton
from PySide6.QtGui import QIcon
from PySide6.QtWebEngineWidgets import QWebEngineView
import plotly.graph_objects as go
from plotly.io import to_html
import plotly.graph_objects as go
import plotly.io as pio
from PySide6.QtCore import QUrl

class ControlsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setup_ui()
        self.setLayout(self.layout)

    def setup_ui(self):
        # Title Label
        self.layout.addWidget(HeaderWidget())

        # Save plot buttons
        self.save_plot_button = QPushButton("Save current plot")
        self.save_all_plot_button = QPushButton("Save all plots")
        
        # Adding a separator between title and buttons
        self.add_separator()

        self.layout.addWidget(self.save_plot_button)
        self.layout.addWidget(self.save_all_plot_button)
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

class PlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.figs = []
        self.current_index = 0
        self.layout = QVBoxLayout()
        self.setup_ui()
        self.setLayout(self.layout)

    def setup_ui(self):

        self.html_browser = QWebEngineView()
        self.layout.addWidget(self.html_browser)

        fig = go.Figure(data=[
            go.Bar(name='Catégorie A', x=['A', 'B', 'C'], y=[10, 20, 30]),
            go.Bar(name='Catégorie B', x=['A', 'B', 'C'], y=[15, 25, 35])
        ])
        fig.update_layout(barmode='group', title='Graphique à barres')

        # Générer le contenu HTML avec les dépendances JavaScript via CDN
        html_content = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")

        # Charger le contenu HTML dans QWebEngineView
        self.html_browser.setHtml(html_content, QUrl(""))


        navigation_layout = QHBoxLayout()
        self.prev_button = QToolButton()
        self.prev_button.setIcon(QIcon("path/to/prev_icon.png"))
        self.prev_button.clicked.connect(self.show_previous_plot)
        navigation_layout.addWidget(self.prev_button)

        self.next_button = QToolButton()
        self.next_button.setIcon(QIcon("path/to/next_icon.png"))
        self.next_button.clicked.connect(self.show_next_plot)
        navigation_layout.addWidget(self.next_button)

        self.layout.addLayout(navigation_layout)

    def show_previous_plot(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_plot()

    def show_next_plot(self):
        if self.current_index < len(self.figs) - 1:
            self.current_index += 1
            self.update_plot()

    def update_plot(self):
        pass

class PlotWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.setWindowTitle(f"Pelca Results")
        x = parent.pos().x() + 500
        y = parent.pos().y()
        self.setGeometry(x, y, 800, 600)
        self.layout = QHBoxLayout()
        self.setup_ui()
        self.setLayout(self.layout)

    def setup_ui(self):
        self.controls_widget = ControlsWidget()
        self.plot_widget = PlotWidget()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.controls_widget)
        splitter.addWidget(self.plot_widget)
        self.layout.addWidget(splitter)




# def _add_plot_frame(self, layout):
#         """Add a frame to display plots."""
#         self.plot_frame = QWidget()
#         layout.addWidget(self.plot_frame)
# def setup_plot_frame(self, figs):
#         """Set up the frame for displaying plots in PySide, including setting the size and displaying the first plot."""
#         print("Setting up plot frame...")
#         # Calculate max width and height based on figures in self.figs
#         self.figs = figs

#         max_width, max_height = get_max_fig_size(self.figs)
#         self.plot_frame.setFixedSize(max_width, max_height)  # Set fixed size to accommodate the largest figure
#         self.plot_frame_layout = QVBoxLayout(self.plot_frame)  # Add a layout to the plot frame

#         # Initialize index and figure display
#         self.current_index = 0

#         # Create a placeholder for the canvas where the plot will be displayed
#         self.canvas = FigureCanvas(self.figs[self.current_index])  # Initialize with the first figure
#         # self.plot_frame_layout.addWidget(self.canvas)

#         combobox = QComboBox()
#         combobox.addItems([f"Plot {i+1}" for i in range(len(self.figs))])
#         combobox.currentIndexChanged.connect(self.index_changed)
#         self.plot_frame_layout.addWidget(combobox)

#         self.display_plot(self.current_index)

#     def index_changed(self, index):  # index is an int stating from 0
#         """Handle the index change event from the combobox."""
#         self.current_index = index
#         self.display_plot(index)

#     def display_plot(self, index):
#         """Display the plot at the given index in the plot frame."""
#         for i in reversed(range(self.plot_frame_layout.count())):
#             widget = self.plot_frame_layout.itemAt(i).widget()
#             if widget is not None:
#                 widget.setParent(None)

#         # Get the figure and create a new canvas
#         fig = self.figs[index]
#         fig.tight_layout()
#         self.canvas = FigureCanvas(fig)
#         self.plot_frame_layout.addWidget(self.canvas)
#         self.canvas.draw()
