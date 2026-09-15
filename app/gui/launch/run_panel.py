"""Launch panel: file selection, run mode buttons, and live console output.

Exposes ``RunPanel``, a ``QWidget`` that provides the full pre-run interface:
file path input, two run-mode buttons (with or without LCA), and a scrollable
console. Also exposes ``EmittingStream``, a ``QObject`` that redirects
``sys.stdout`` and ``sys.stderr`` to a Qt signal so pipeline output appears
in the console in real time.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QSettings, Signal
from PySide6.QtGui import QColor, QTextCursor
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.gui.launch.worker import RunnerThread
from app.gui.results.window import PlotWindow

logger = logging.getLogger(__name__)

_SETTINGS_ORG = "PELCA"
_SETTINGS_APP = "PELCA"
_KEY_LAST_FILE = "last_input_file"


class EmittingStream(QObject):
    """Qt-compatible stream that redirects ``write()`` calls to a Qt signal.

    Emits text as-is when it contains ``\\r`` (carriage-return progress bars),
    otherwise appends a trailing newline if absent.
    """

    text_written = Signal(str)

    def write(self, text: str) -> None:
        """Emit *text* via the signal."""
        if text:
            if "\r" not in text and not text.endswith("\n"):
                text += "\n"
            self.text_written.emit(text)

    def flush(self) -> None:
        pass

    def fileno(self) -> int:
        return 1


class RunPanel(QWidget):
    """Widget combining file selection, run mode buttons, and a live console."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._window = parent
        self.is_running = False
        self.buttons = False
        self._settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
        self._setup_ui()
        self._restore_last_file()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()
        self._add_file_selection_section(layout)
        self._add_run_buttons(layout)
        self._add_console(layout)
        self.setLayout(layout)

    def _add_file_selection_section(self, layout: QVBoxLayout) -> None:
        """Add file selection input and browse button to the layout."""
        file_selection_layout = QHBoxLayout()
        file_selection_layout.addWidget(QLabel("Select input file:"))

        self.file_path_edit = QLineEdit()
        file_selection_layout.addWidget(self.file_path_edit)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_file)
        file_selection_layout.addWidget(browse_button)

        layout.addLayout(file_selection_layout)

    def _add_run_buttons(self, layout: QVBoxLayout) -> None:
        """Add buttons to launch a LCIC-only or full LCA + LCIC run."""
        button_layout = QHBoxLayout()

        self.run_button = QPushButton("Run LCIC only")
        self.run_button.clicked.connect(self.run_lcic)

        self.run_button2 = QPushButton("Run LCA + LCIC")
        self.run_button2.clicked.connect(self.run_lca_lcic)
        button_layout.addWidget(self.run_button2)
        button_layout.addWidget(self.run_button)

        layout.addLayout(button_layout)

        self.run_button.hide()
        self.run_button2.hide()

    def run_lca_lcic(self) -> None:
        self.run_script(run_lca=True)

    def run_lcic(self) -> None:
        self.run_script(run_lca=False)

    def _add_console(self, layout: QVBoxLayout) -> None:
        """Add a console text area and redirect stdout/stderr into it."""
        self.text_edit_stdout = QTextEdit(self)
        self.text_edit_stdout.setReadOnly(True)
        layout.addWidget(self.text_edit_stdout)

        self.stdout_stream = EmittingStream()
        self.stdout_stream.text_written.connect(
            lambda text: self.append_output_stdout(text, is_error=False)
        )
        sys.stdout = self.stdout_stream

        self.stderr_stream = EmittingStream()
        self.stderr_stream.text_written.connect(
            lambda text: self.append_output_stdout(text, is_error=True)
        )
        sys.stderr = self.stderr_stream

    def append_output_stdout(self, text: str, is_error: bool = False) -> None:
        cursor = self.text_edit_stdout.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = cursor.charFormat()
        fmt.setForeground(QColor("grey") if is_error else QColor("white"))
        cursor.setCharFormat(fmt)
        # Split on \r: each segment after index 0 overwrites the current line
        # in-place, matching terminal carriage-return progress-bar behaviour.
        for i, segment in enumerate(text.split("\r")):
            if i > 0:
                cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
                cursor.movePosition(
                    QTextCursor.MoveOperation.EndOfLine,
                    QTextCursor.MoveMode.KeepAnchor,
                )
                cursor.removeSelectedText()
            if segment:
                cursor.insertText(segment)
        self.text_edit_stdout.setTextCursor(cursor)
        self.text_edit_stdout.ensureCursorVisible()

    def browse_file(self) -> None:
        """Open a file dialog to select an input file.

        The dialog opens in the directory of the last used file, if it still exists.
        """
        last = str(self._settings.value(_KEY_LAST_FILE, ""))
        start_dir = str(Path(last).parent) if last and Path(last).exists() else ""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Input File",
            start_dir,
            "Excel files (*.xlsx *.xlsm);;All files (*)",
        )
        if file_path:
            self.file_path_edit.setText(file_path)
            self._save_last_file(file_path)
            if not self.buttons:
                self.run_button.show()
                self.run_button2.show()
                self.buttons = True

    def run_script(self, run_lca: bool) -> None:
        """Start the pipeline in a background thread."""
        if self.is_running:
            logger.warning("A run is already in progress.")
            return

        file_path = self.file_path_edit.text()
        if not file_path:
            QMessageBox.warning(self, "No file selected", "Please select an input file first.")
            return

        self._save_last_file(file_path)
        self.is_running = True
        self.run_button.setEnabled(False)
        self.run_button2.setEnabled(False)

        self.worker = RunnerThread(file_path, run_lca=run_lca)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.progress.connect(lambda msg: logger.info(msg))
        self.worker.start()

    def handle_figures(self, result: dict) -> None:
        """Display the plot window with results from the pipeline."""
        self.plot_window = PlotWindow(self._window, result)
        self.plot_window.show()

    def on_finished(self, result: dict) -> None:
        """Handle successful pipeline completion."""
        logger.info("Pipeline completed successfully.")
        self.run_button.setEnabled(True)
        self.run_button2.setEnabled(True)
        self.is_running = False
        self.handle_figures(result)

    def on_error(self, error_message: str) -> None:
        """Handle pipeline errors."""
        logger.error("Pipeline error: %s", error_message)
        QMessageBox.critical(self, "Error", error_message)
        self.run_button.setEnabled(True)
        self.run_button2.setEnabled(True)
        self.is_running = False

    # ── persistence ──────────────────────────────────────────────────────────

    def _save_last_file(self, file_path: str) -> None:
        """Persist *file_path* in application settings."""
        self._settings.setValue(_KEY_LAST_FILE, file_path)

    def _restore_last_file(self) -> None:
        """Populate the file field with the last used path if it still exists."""
        last = str(self._settings.value(_KEY_LAST_FILE, ""))
        if last and Path(last).exists():
            self.file_path_edit.setText(last)
            self.run_button.show()
            self.run_button2.show()
            self.buttons = True
