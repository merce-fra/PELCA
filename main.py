import sys

import matplotlib
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from brightway2 import *


matplotlib.use("Agg")

# Réinitialiser stdout et stderr quand l'application se ferme
def reset_streams():
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    print("Streams reset.")

if __name__ == "__main__":
    # Create an instance of QApplication

    app = QApplication(sys.argv)

    # Set the application style
    app.setStyle("Fusion")

    # Create the main window
    window = MainWindow()
    bw2setup()

    # Apply the dark palette
    dark_palette = QPalette()
    dark_colors = {
        QPalette.ColorRole.Window: QColor(53, 53, 53),
        QPalette.ColorRole.WindowText: QColor(255, 255, 255),
        QPalette.ColorRole.Base: QColor(35, 35, 35),
        QPalette.ColorRole.AlternateBase: QColor(53, 53, 53),
        QPalette.ColorRole.ToolTipBase: QColor(255, 255, 255),
        QPalette.ColorRole.ToolTipText: QColor(255, 255, 255),
        QPalette.ColorRole.Text: QColor(255, 255, 255),
        QPalette.ColorRole.Button: QColor(53, 53, 53),
        QPalette.ColorRole.ButtonText: QColor(255, 255, 255),
        QPalette.ColorRole.BrightText: QColor(255, 0, 0),
        QPalette.ColorRole.Link: QColor(42, 130, 218),
        QPalette.ColorRole.Highlight: QColor(42, 130, 218),
        QPalette.ColorRole.HighlightedText: QColor(0, 0, 0),
    }
    for role, color in dark_colors.items():
        dark_palette.setColor(role, color)
    app.setPalette(dark_palette)

    # Show the main window
    window.show()

    app.aboutToQuit.connect(reset_streams)
    # Execute the application
    sys.exit(app.exec())
