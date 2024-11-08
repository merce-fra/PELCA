from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QTextEdit,
                               QVBoxLayout, QWidget)

from app.threads.process_excel import ProcessExcel
from app.widgets.plot_window.plot import PlotWindow


class ScriptWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.is_running = False  # Initialize running status
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self._add_file_selection_section(layout)
        self._add_run_button(layout)
        self._add_console(layout)
        self.setLayout(layout)  # Set the main layout

    def _add_file_selection_section(self, layout):
        """Add file selection input and browse button to the layout."""
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
        self.run_button.clicked.connect(self.run_script)
        layout.addWidget(self.run_button)

    def _add_console(self, layout):
        """Add a console text area to display output."""
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        layout.addWidget(self.console_text)

    def _redirect_output(self):
        """Redirect stdout and stderr to the console text area if needed."""
        # Optional: add redirection logic here to capture print statements
        pass

    def browse_file(self):
        """Open a file dialog to select a file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Input File")
        if file_path:
            self.file_path_edit.setText(file_path)

    def update_console(self, message):
        """Update console output in the main thread."""
        self.console_text.append(message)

    def run_script(self):
        """Run the script in a separate thread to keep the UI responsive."""
        if self.is_running:
            print("Script is already running.")
            return
        else:
            self.is_running = True
            file_path = self.file_path_edit.text()
            self.worker = ProcessExcel(file_path)
            self.worker.finished.connect(self.on_finished)
            self.worker.error.connect(self.on_error)
            self.worker.figs.connect(self.handle_figures)
            self.worker.start()
            self.run_button.setEnabled(False)  # Disable the run button while running

    def handle_figures(self, figs):
        """Handle the figures emitted by the worker thread."""
        self.plot_window = PlotWindow(self.parent, figs)
        self.plot_window.show()

    def on_finished(self):
        """Handle the finished signal."""
        print("Script executed successfully in the worker thread.")
        self.run_button.setEnabled(True)
        self.is_running = False

    def on_error(self, error_message):
        """Handle errors emitted from the worker."""
        print(f"Error: {error_message}")
        QMessageBox.critical(self, "Error", error_message)
        self.run_button.setEnabled(True)
        self.is_running = False