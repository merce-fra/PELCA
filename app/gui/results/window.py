"""Results window: figure display with index-based navigation.

Exposes ``PlotWindow`` (top-level results ``QWidget``), ``PlotWidget`` (stacked
figure renderer supporting both Plotly via ``QWebEngineView`` and Matplotlib via
``FigureCanvasQTAgg``), and ``IndexSwitcher`` (``QObject`` signal model that
coordinates the current plot index between ``PlotWidget`` and
``ImageButtonsWidget``).
"""

from __future__ import annotations

import plotly.io as pio
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtCore import QObject, Qt, QUrl, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSplitter,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.gui.results.controls import ControlsWidget, ImageButtonsWidget


class IndexSwitcher(QObject):
    """Manage the current plot index and notify listeners on change."""

    index_changed = Signal(int)

    def __init__(self, figs: dict) -> None:
        super().__init__()
        self.index = 0
        self.figs = figs

    def get_max_index(self) -> int:
        return len(self.figs["plots"]) - 1

    def set_index(self, index: int) -> None:
        self.index = index
        self.index_changed.emit(index)

    def get_index(self) -> int:
        return self.index

    def increment_index(self) -> None:
        self.index = (self.index + 1) % (self.get_max_index() + 1)
        self.index_changed.emit(self.index)

    def decrement_index(self) -> None:
        self.index = (self.index - 1) % (self.get_max_index() + 1)
        self.index_changed.emit(self.index)


class PlotWidget(QWidget):
    """Stacked widget that renders each figure (Plotly or Matplotlib) with navigation controls."""

    def __init__(self, parent: PlotWindow) -> None:
        super().__init__()
        self._window = parent
        self.figs = parent.figs
        self._layout = QVBoxLayout()
        self.setup_ui()
        self.setLayout(self._layout)

    def get_web_engine(self, fig) -> QWebEngineView:
        """Return a QWebEngineView rendering a Plotly figure."""
        config = {
            "displaylogo": False,
            "modeBarButtonsToRemove": ["toImage"],
            "responsive": True,
        }
        html_content = pio.to_html(fig, full_html=False, include_plotlyjs="cdn", config=config)
        # type: ignore[arg-type]
        html_browser = QWebEngineView()
        html_browser.setHtml(html_content, QUrl(""))
        return html_browser

    def get_figure_canvas(self, fig) -> FigureCanvas:
        """Return a FigureCanvasQTAgg for a Matplotlib figure."""
        return FigureCanvas(fig)

    def setup_ui(self) -> None:
        """Build the stacked widget, navigation buttons, and thumbnail strip."""
        self._window.index.index_changed.connect(self.update_plot)
        self.index = self._window.index

        self.widget_list: list[QWebEngineView | FigureCanvas] = []
        for fig in self.figs["plots"]:
            if fig["type"] == "plotly":
                widget: QWebEngineView | FigureCanvas = self.get_web_engine(fig["plot"])
            elif fig["type"] == "matplotlib":
                widget = self.get_figure_canvas(fig["plot"])
            else:
                raise ValueError(f"Unknown figure type: {fig['type']!r}")
            self.widget_list.append(widget)

        self.stacked_widget = QStackedWidget()
        for widget in self.widget_list:
            self.stacked_widget.addWidget(widget)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked_widget)

        navigation_layout = QHBoxLayout()

        self.prev_button = QToolButton()
        self.prev_button.setIcon(QIcon(":/ressources/icons/previous.svg"))
        self.title_label = QLabel("Plots")
        self.prev_button.clicked.connect(self._window.index.decrement_index)
        navigation_layout.addWidget(self.prev_button)

        self.next_button = QToolButton()
        self.next_button.setIcon(QIcon(":/ressources/icons/next.svg"))
        self.next_button.clicked.connect(self._window.index.increment_index)
        navigation_layout.addWidget(self.next_button)

        main_layout.addLayout(navigation_layout)
        main_layout.addWidget(ImageButtonsWidget(self))

        self._layout.addLayout(main_layout)

    def update_plot(self, index: int) -> None:
        """Switch the stacked widget to the figure at *index*."""
        self.title_label.setText(self.figs["plots"][index]["title"])
        self.stacked_widget.setCurrentIndex(index)


class PlotWindow(QWidget):
    """Top-level results window: ControlsWidget (20 %) and PlotWidget (80 %) in a splitter."""

    def __init__(self, parent: QWidget | None, figs: dict) -> None:
        super().__init__()
        self.setWindowTitle("Pelca Results")
        self.setWindowIcon(QIcon(":/ressources/icons/icon.ico"))
        self.index = IndexSwitcher(figs)
        self.figs = figs
        self._layout = QHBoxLayout()
        self.setup_ui()
        self.setLayout(self._layout)

    def setup_ui(self) -> None:
        """Set up the splitter with controls (20 %) and plot area (80 %)."""
        self.controls_widget = ControlsWidget(parent=self)
        self.plot_widget = PlotWidget(parent=self)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.addWidget(self.controls_widget)
        self._splitter.addWidget(self.plot_widget)
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 4)
        self._splitter.setSizes([200, 800])

        self._layout.addWidget(self._splitter)

    def resizeEvent(self, event) -> None:
        """Maintain a 20/80 width ratio between controls and plot area on resize."""
        total_width = self.width()
        self._splitter.setSizes([int(total_width * 0.2), int(total_width * 0.8)])
        super().resizeEvent(event)
