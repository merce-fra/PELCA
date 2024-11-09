import plotly.graph_objects as go
import plotly.io as pio
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__initUi()

    def __initUi(self):
        self.setWindowTitle("PySide & Plotly (En Mémoire)")

        # Création d'un graphique à barres
        fig = go.Figure(
            data=[
                go.Bar(name="Catégorie A", x=["A", "B", "C"], y=[10, 20, 30]),
                go.Bar(name="Catégorie B", x=["A", "B", "C"], y=[15, 25, 35]),
            ]
        )
        fig.update_layout(barmode="group", title="Graphique à barres")

        # Générer le contenu HTML avec les dépendances JavaScript via CDN
        html_content = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")

        # Charger le contenu HTML dans QWebEngineView
        view = QWebEngineView()
        view.setHtml(html_content, QUrl(""))

        self.setCentralWidget(view)
