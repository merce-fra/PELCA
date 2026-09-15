"""Save/export controls and thumbnail navigation for the results window.

Exposes ``ControlsWidget`` (save-all, save-selected, save data as numpy and
Excel buttons, delegating writes to ``app.io.export``) and
``ImageButtonsWidget`` (horizontal strip of per-figure thumbnail buttons that
drive ``IndexSwitcher`` to navigate the plot view).
"""

from __future__ import annotations

import io
import logging
from typing import TYPE_CHECKING

import plotly.io as pio
from PIL import Image
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.gui.header import HeaderWidget
from app.io.export import export_excel, export_html, export_numpy, export_png, export_svg

if TYPE_CHECKING:
    from app.gui.results.window import PlotWindow

logger = logging.getLogger(__name__)


class ControlsWidget(QWidget):
    def __init__(self, parent: PlotWindow) -> None:
        super().__init__()
        self._window = parent
        self.figs = parent.figs  # full result dict from PelcaRunner
        self.index = parent.index
        self._layout = QVBoxLayout()
        self.setup_ui()
        self.setLayout(self._layout)

    def _plots(self) -> list[dict]:
        return self.figs.get("plots", [])

    def _plot_dir(self):
        """Return the configured plot output directory (from config), or ask the user."""
        config = self.figs.get("config")
        if config is not None:
            return config.output.plot_dir
        return None

    def _numpy_dir(self):
        """Return the configured numpy output directory (from config), or ask the user."""
        config = self.figs.get("config")
        if config is not None:
            return config.output.numpy_dir
        return None

    def save_plots(self):
        """Save all figures to the configured output directory."""
        plot_dir = self._plot_dir()
        if plot_dir is None:
            plot_dir = QFileDialog.getExistingDirectory(self, "Select Folder to Save Plots")
            if not plot_dir:
                return
            from pathlib import Path

            plot_dir = Path(plot_dir)

        for entry in self._plots():
            fig = entry.get("plot")
            title = entry.get("title", "figure")
            if fig is None:
                continue
            try:
                export_png(fig, title, plot_dir)
                export_svg(fig, title, plot_dir)
                export_html(fig, title, plot_dir)
            except Exception as exc:
                logger.warning("Failed to export figure %r: %s", title, exc)
        logger.info("All plots saved to %s", plot_dir)

    def save_selected_plot(self):
        """Save the currently displayed figure."""
        plot_dir = self._plot_dir()
        if plot_dir is None:
            plot_dir = QFileDialog.getExistingDirectory(self, "Select Folder to Save Plot")
            if not plot_dir:
                return
            from pathlib import Path

            plot_dir = Path(plot_dir)

        plots = self._plots()
        idx = self.index.get_index()
        if not plots or idx >= len(plots):
            return
        entry = plots[idx]
        fig = entry.get("plot")
        title = entry.get("title", "figure")
        if fig is None:
            return
        try:
            export_png(fig, title, plot_dir)
            export_svg(fig, title, plot_dir)
            export_html(fig, title, plot_dir)
            logger.info("Plot %r saved to %s", title, plot_dir)
        except Exception as exc:
            logger.warning("Failed to save plot %r: %s", title, exc)

    def save_data(self):
        """Save simulation result arrays as .npy files."""
        numpy_dir = self._numpy_dir()
        if numpy_dir is None:
            numpy_dir = QFileDialog.getExistingDirectory(self, "Save data to numpy array")
            if not numpy_dir:
                return
            from pathlib import Path

            numpy_dir = Path(numpy_dir) / "numpy"

        env_result = self.figs.get("env_result")
        if env_result is None:
            logger.warning("No simulation result available to save.")
            return

        try:
            export_numpy("Impact_total", env_result.total, numpy_dir)
            export_numpy("Impact_manu", env_result.manufacturing, numpy_dir)
            export_numpy("Impact_use", env_result.use, numpy_dir)
            export_numpy("fault_cause", env_result.fault_cause, numpy_dir)
            export_numpy("RU_age", env_result.ru_age, numpy_dir)
            logger.info("NumPy data saved to %s", numpy_dir)
        except Exception as exc:
            logger.error("Failed to save NumPy data: %s", exc)

    def save_data_excel(self) -> None:
        """Save simulation result arrays as .xlsx files."""
        config = self.figs.get("config")
        default_dir = str(config.output.lca_dir) if config else ""
        folder_path = QFileDialog.getExistingDirectory(self, "Save data to Excel", default_dir)
        if not folder_path:
            return

        env_result = self.figs.get("env_result")
        if env_result is None:
            logger.warning("No simulation result available to save.")
            return

        try:
            from pathlib import Path

            excel_folder = Path(folder_path) / "excel"
            export_mapping = {
                "Impact_total": env_result.total,
                "Impact_manu": env_result.manufacturing,
                "Impact_use": env_result.use,
                "fault_cause": env_result.fault_cause,
                "RU_age": env_result.ru_age,
            }
            for base_name, data in export_mapping.items():
                export_excel(base_name, data, excel_folder)
            logger.info("Excel data saved to %s", excel_folder)
        except Exception as exc:
            logger.error("Failed to save Excel data: %s", exc)

    def setup_ui(self):
        # Title Label
        self._layout.addWidget(HeaderWidget())

        # Save plot buttons
        self.save_plot_button = QPushButton("Save current plot")
        self.save_plot_button.setFixedHeight(30)

        self.save_all_plot_button = QPushButton("Save all plots")
        self.save_all_plot_button.setFixedHeight(30)

        self.save_plot_button.clicked.connect(self.save_selected_plot)
        self.save_all_plot_button.clicked.connect(self.save_plots)

        # Adding a separator between title and buttons
        self.add_separator()

        self._layout.addWidget(self.save_plot_button)
        self._layout.addWidget(self.save_all_plot_button)
        self.add_separator()

        # Options Label
        options_label = QLabel("Select Options for data export :")
        options_label.setFixedHeight(20)
        self._layout.addWidget(options_label)

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

        self._layout.addWidget(self.save_data_button)
        self._layout.addWidget(self.save_excel_button)

    def add_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        self._layout.addWidget(separator)


class ImageButtonsWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self._window: PlotWindow = parent

        def create_thumbnail(fig, size=(100, 100)):
            """Generate a PIL thumbnail of a Plotly or Matplotlib figure
            for use as a button icon.
            """
            if fig["type"] == "plotly":
                img_bytes = pio.to_image(fig["plot"], format="png")
                img = Image.open(io.BytesIO(img_bytes))
                img.thumbnail(size)
                img = img.convert("RGBA")
                qimage = QImage(
                    img.tobytes(),
                    img.width,
                    img.height,
                    img.width * 4,
                    QImage.Format.Format_RGBA8888,
                )
                pixmap = QPixmap.fromImage(qimage)
                label = QLabel()
                label.setPixmap(pixmap)
                return label
            else:
                with io.BytesIO() as buf:
                    fig["plot"].savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
                    buf.seek(0)
                    img = Image.open(buf)
                    img.thumbnail(size)
                    qimage = QImage(
                        img.tobytes(), img.width, img.height, QImage.Format.Format_RGBA8888
                    )
                    pixmap = QPixmap.fromImage(qimage)
                    label = QLabel()
                    label.setPixmap(pixmap)
                    return label

        self._layout = QHBoxLayout()
        self.setLayout(self._layout)
        self.thumbnails = []
        for idx, fig in enumerate(parent.figs["plots"]):
            thumbnail = create_thumbnail(fig)
            button = QPushButton()
            button.setIcon(QIcon(thumbnail.pixmap()))
            button.setIconSize(thumbnail.pixmap().rect().size())
            button.clicked.connect(lambda checked, index=idx: self._window.index.set_index(index))
            self._layout.addWidget(button)
            self.thumbnails.append(button)
