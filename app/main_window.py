import sys

from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QComboBox, QFileDialog, QHBoxLayout, QLabel,
                               QLineEdit, QMainWindow, QMessageBox,
                               QPushButton, QSplitter, QTextEdit, QVBoxLayout,
                               QWidget)

from app.models.console import ConsoleOutputRedirector


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PELCA")
        self.file_path_edit = None  # Initialize the file path edit field
        self.console_text = None  # Initialize the console text area
        self.is_running = False  # Flag to check if a script is running
        self.console_output_redirector = ConsoleOutputRedirector()  # Console output redirection
        self._setup_ui()
        self._redirect_output()
        self.console_output_redirector.new_text.connect(self.update_console)
        self.figs = []

    def _setup_ui(self):
        """Set up the main UI components and layout."""
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        self._add_header_image(main_layout)
        self._add_splitter(main_layout)

        self.setCentralWidget(central_widget)

    def _add_header_image(self, layout):
        """Add a centered header image to the layout."""
        header_label = QLabel()
        header_pixmap = QPixmap("assets/first_image.png").scaled(413, 145, Qt.AspectRatioMode.KeepAspectRatio)
        header_label.setPixmap(header_pixmap)

        # Set fixed size for better control
        header_label.setFixedSize(413, 145)

        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(header_label)
        h_layout.addStretch()

        # Reduce margins and spacing
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        layout.addLayout(h_layout)

    def _add_splitter(self, layout):
        """Add a splitter with left and right sections to the layout."""
        splitter = QSplitter()

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        splitter.addWidget(right_widget)

        self._add_file_selection_section(left_layout)
        self._add_run_button(left_layout)
        self._add_console(left_layout)  # Add the console below the Run Script button
        self._add_plot_frame(right_layout)

        layout.addWidget(splitter)

    def _add_file_selection_section(self, layout):
        """Add file selection input and browse button to the left layout."""
        file_selection_layout = QHBoxLayout()
        file_selection_layout.addWidget(QLabel("Select input file:"))

        self.file_path_edit = QLineEdit()
        file_selection_layout.addWidget(self.file_path_edit)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_file)
        file_selection_layout.addWidget(browse_button)

        layout.addLayout(file_selection_layout)

    def _add_run_button(self, layout):
        """Add a button to execute a script using the selected file."""
        self.run_button = QPushButton("Run Script")
        self.run_button.clicked.connect(self.run_script_threaded)
        layout.addWidget(self.run_button)

    def _add_console(self, layout):
        """Add a console text area to display output."""
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)  # Make the console read-only
        layout.addWidget(self.console_text)

    def _add_plot_frame(self, layout):
        """Add a frame to display plots."""
        self.plot_frame = QWidget()
        layout.addWidget(self.plot_frame)

    def _redirect_output(self):
        """Redirect stdout and stderr to the console text area."""
        sys.stdout = self.console_output_redirector
        sys.stderr = self.console_output_redirector

    def browse_file(self):
        """Open a file dialog to select a file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Input File")
        if file_path:
            self.file_path_edit.setText(file_path)

    def setup_plot_frame(self, figs):
        """Set up the frame for displaying plots in PySide, including setting the size and displaying the first plot."""
        print("Setting up plot frame...")
        # Calculate max width and height based on figures in self.figs
        self.figs = figs

        max_width, max_height = get_max_fig_size(self.figs)
        self.plot_frame.setFixedSize(max_width, max_height)  # Set fixed size to accommodate the largest figure
        self.plot_frame_layout = QVBoxLayout(self.plot_frame)  # Add a layout to the plot frame

        # Initialize index and figure display
        self.current_index = 0

        # Create a placeholder for the canvas where the plot will be displayed
        self.canvas = FigureCanvas(self.figs[self.current_index])  # Initialize with the first figure
        # self.plot_frame_layout.addWidget(self.canvas)

        combobox = QComboBox()
        combobox.addItems([f"Plot {i+1}" for i in range(len(self.figs))])
        combobox.currentIndexChanged.connect(self.index_changed)
        self.plot_frame_layout.addWidget(combobox)

        self.display_plot(self.current_index)

    def index_changed(self, index):  # index is an int stating from 0
        """Handle the index change event from the combobox."""
        self.current_index = index
        self.display_plot(index)

    def display_plot(self, index):
        """Display the plot at the given index in the plot frame."""
        # Clear the existing layout
        # for i in reversed(range(self.plot_frame_layout.count())):
        #     widget = self.plot_frame_layout.itemAt(i).widget()
        #     if widget is not None:
        #         widget.setParent(None)

        # Get the figure and create a new canvas
        fig = self.figs[index]
        fig.tight_layout()
        self.canvas = FigureCanvas(fig)
        self.plot_frame_layout.addWidget(self.canvas)
        self.canvas.draw()

    def update_console(self, message):
        """Update console output in the main thread."""
        self.console_text.append(message)

    def reset_interface(self):
        pass

    def run_script_threaded(self):
        """Run the script in a separate thread to keep the UI responsive."""
        if self.is_running:
            print("A script is already running.")
            return
        else:
            self.is_running = True
            file_path = self.file_path_edit.text()
            self.worker = Worker(file_path)
            self.worker.finished.connect(self.on_finished)
            self.worker.error.connect(self.on_error)
            self.worker.figs.connect(self.setup_plot_frame)  # Connect to your data handler if needed
            self.worker.start()

    def on_finished(self):
        """Handle the finished signal."""
        print("Script executed successfully")
        self.run_button.setEnabled(True)  # Re-enable the run button
        self.is_running = False  # Reset running status

    def on_error(self, error_message):
        """Handle errors emitted from the worker."""
        print(f"Error: {error_message}")
        QMessageBox.critical(self, "Error", error_message)
        self.run_button.setEnabled(True)  # Re-enable the button
        self.is_running = False  # Reset running status
