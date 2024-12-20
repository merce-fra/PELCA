"""PELCA (Power Electronics Life Cycle Assessment) is an open-source project aimed at assessing the environmental impact over the life cycle of modular and diagnosable power electronics systems. The integration of modularity and diagnosability aligns with circular economy principles, promoting practices such as repair and reuse. This project provides a tool to calculate the environmental impacts associated with the manufacturing, usage, and replacement of power electronics products.
Copyright (C) Mitsubishi Electric R&D Centre Europe and SATIE 2024, author Briac Baudais baudaisbriac@gmail.com

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this program.  If not, see https://www.gnu.org/licenses/lgpl-3.0.html"""

"""
Created on 2024

@author: baudais, bdubus
"""

import plotly.io as pio
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (QHBoxLayout, QSplitter, QStackedWidget,
                               QToolButton, QVBoxLayout, QWidget, QLabel)

from app.models.plot import IndexSwitcher
from app.widgets.plot_window.controls import ControlsWidget, ImageButtonsWidget




class PlotWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.figs = parent.figs
        self.layout = QVBoxLayout()
        self.setup_ui()
        self.setLayout(self.layout)

    # def init_plotly_plot(self):
    #     print("Initializing plotly plot")
    #     fig = self.figs["plotly"][self.parent.index.get_index()]
    #     html_content = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
    #     self.html_browser = QWebEngineView()
    #     self.html_browser.setHtml(html_content, QUrl(""))
    #     self.layout.addWidget(self.html_browser)
    #     self.html_browser.hide()
    #     self.html_browser.show()

    def get_web_engine(self, fig):
        """Retourne un QWebEngineView avec un graphique Plotly"""
        config = {
            'displaylogo': False,
            'modeBarButtonsToRemove': ['toImage'],
            'responsive': True
        }
        html_content = pio.to_html(fig, full_html=False, include_plotlyjs="cdn", config=config)
        html_browser = QWebEngineView()
        html_browser.setHtml(html_content, QUrl(""))
        return html_browser

    def get_figure_canvas(self, fig):
        """Retourne un FigureCanvas pour un graphique Matplotlib"""
        canvas = FigureCanvas(fig)
        return canvas

    def setup_ui(self):
        """Initialisation de l'interface utilisateur"""
        self.parent.index.index_changed.connect(self.update_plot)
        self.index = self.parent.index

        # Créer la liste des widgets de type Plotly ou Matplotlib
        self.widget_list = []
        
        for fig in self.figs["plots"]:
            if fig["type"] == "plotly":
                widget = self.get_web_engine(fig["plot"])
            elif fig["type"] == "matplotlib":
                widget = self.get_figure_canvas(fig["plot"])
            self.widget_list.append(widget)

        self.stacked_widget = QStackedWidget()

        # Ajouter les widgets à la pile
        for widget in self.widget_list:
            self.stacked_widget.addWidget(widget)

        # Ajouter le QStackedWidget au layout principal


        # Crée un layout vertical pour l'ensemble (navigation + ImageButtonsWidget)
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked_widget)


        # Crée un layout horizontal pour les boutons de navigation
        navigation_layout = QHBoxLayout()

        # Bouton précédent
        self.prev_button = QToolButton()
        self.prev_button.setIcon(QIcon(":/ressources/icons/previous.svg"))
        self.title_label = QLabel("Graphiques")
        self.prev_button.clicked.connect(self.parent.index.decrement_index)
        navigation_layout.addWidget(self.prev_button)

        # Bouton suivant
        self.next_button = QToolButton()
        self.next_button.setIcon(QIcon(":/ressources/icons/next.svg"))
        self.next_button.clicked.connect(self.parent.index.increment_index)
        # navigation_layout.addWidget(self.title_label)

        navigation_layout.addWidget(self.next_button)

        # Ajouter le layout horizontal des boutons à l'ensemble principal
        main_layout.addLayout(navigation_layout)

        # Ajouter ImageButtonsWidget en dessous des boutons de navigation
        main_layout.addWidget(ImageButtonsWidget(self))

        # Crée un QStackedWidget pour afficher dynamiquement les graphiques
        
        # Ajouter le layout principal à votre layout global
        self.layout.addLayout(main_layout)

    def update_plot(self, index):
        """Met à jour l'affichage du graphique basé sur l'index"""
        # Changer l'index du QStackedWidget pour afficher le bon graphique
        self.title_label.setText(self.figs["plots"][index]["title"])
        self.stacked_widget.setCurrentIndex(index)


    # def update_plot(self, index):
    #     fig = self.figs["plotly"][index]
    #     html_content = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
    #     self.html_browser.setHtml(html_content, QUrl(""))
    #     self.html_browser.show()

class PlotWindow(QWidget):
    def __init__(self, parent, figs):
        super().__init__()
        self.setWindowTitle(f"Pelca Results")
        self.setWindowIcon(QIcon(":/ressources/icons/icon.ico"))

        self.index = IndexSwitcher(figs)
        x = parent.pos().x() + 500
        y = parent.pos().y()
        self.figs = figs
        self.layout = QHBoxLayout()
        self.setup_ui()
        self.setLayout(self.layout)

    def setup_ui(self):
            """Set up the user interface with controls and plot areas."""
            self.controls_widget = ControlsWidget(parent=self)
            self.plot_widget = PlotWidget(parent=self)

            # Create a splitter for resizable widgets
            splitter = QSplitter(Qt.Horizontal)
            splitter.addWidget(self.controls_widget)
            splitter.addWidget(self.plot_widget)

            # Set stretch factors: 1 for controls, 4 for plot (total 1 + 4 = 5)
            splitter.setStretchFactor(0, 1)  # Index 0: controls_widget
            splitter.setStretchFactor(1, 4)  # Index 1: plot_widget

            # Initialize sizes based on a 20/80 ratio
            splitter.setSizes([200, 800])

            self.layout.addWidget(splitter)

    def resizeEvent(self, event):
        """Force a 20/80 split on resize."""
        total_width = self.width()
        controls_width = total_width * 0.2
        plot_width = total_width * 0.8

        self.layout.itemAt(0).widget().setSizes([controls_width, plot_width])
        super().resizeEvent(event)
