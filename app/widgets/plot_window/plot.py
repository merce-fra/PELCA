import plotly.io as pio
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon
# from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (QHBoxLayout, QSplitter, QStackedWidget,
                               QToolButton, QVBoxLayout, QWidget)

from app.models.plot import IndexSwitcher, ModeSwitcher
from app.widgets.plot_window.controls import ControlsWidget


class PlotWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.figs = parent.figs
        self.layout = QVBoxLayout()
        self.setup_ui()
        self.setLayout(self.layout)

    def update_plot_mode(self, plotly_mode):
        # if plotly_mode:
        #     # self.stack.hide()
        #     # self.html_browser.show()
        # else:
        #     # self.html_browser.hide()
        self.stack.show()

    # def init_plotly_plot(self):
    #     fig = self.figs["plotly"][self.parent.index.get_index()]
    #     html_content = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
    #     self.html_browser = QWebEngineView()
    #     self.html_browser.setHtml(html_content, QUrl(""))
    #     self.layout.addWidget(self.html_browser)
    #     self.html_browser.hide()

    def init_matplotlib_plot(self):
        self.stack = QStackedWidget()
        for fig in self.figs["matplotlib"]:
            canvas = FigureCanvas(fig)
            self.stack.addWidget(canvas)
        self.layout.addWidget(self.stack)
        self.stack.show()

    def setup_ui(self):
        self.parent.mode_switcher.mode_changed.connect(self.update_plot_mode)
        self.parent.index.index_changed.connect(self.update_plot)

        # self.init_plotly_plot()
        self.init_matplotlib_plot()

        navigation_layout = QHBoxLayout()
        self.prev_button = QToolButton()
        self.prev_button.setIcon(QIcon(":/ressources/icons/previous.svg"))
        self.prev_button.clicked.connect(self.parent.index.decrement_index)
        navigation_layout.addWidget(self.prev_button)

        self.next_button = QToolButton()
        self.next_button.setIcon(QIcon(":/ressources/icons/next.svg"))
        self.next_button.clicked.connect(self.parent.index.increment_index)
        navigation_layout.addWidget(self.next_button)

        self.layout.addLayout(navigation_layout)

    def update_plot(self, index):
        if self.parent.mode_switcher.plotly_mode:
            fig = self.figs["plotly"][index]
            html_content = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
            self.html_browser.setHtml(html_content, QUrl(""))
        else:
            self.stack.setCurrentIndex(index)


class PlotWindow(QWidget):
    def __init__(self, parent, figs):
        super().__init__()
        self.setWindowTitle(f"Pelca Results")
        self.mode_switcher = ModeSwitcher()
        self.index = IndexSwitcher(figs, self.mode_switcher)
        x = parent.pos().x() + 500
        y = parent.pos().y()
        self.figs = figs
        self.setGeometry(x, y, 800, 600)
        self.layout = QHBoxLayout()
        self.setup_ui()
        self.setLayout(self.layout)

    def setup_ui(self):
        self.controls_widget = ControlsWidget(parent=self)
        self.plot_widget = PlotWidget(parent=self)
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.controls_widget)
        splitter.addWidget(self.plot_widget)
        self.layout.addWidget(splitter)
