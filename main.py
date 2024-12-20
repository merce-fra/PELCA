"""PELCA (Power Electronics Life Cycle Assessment) is an open-source project aimed at assessing the environmental impact over the life cycle of modular and diagnosable power electronics systems. The integration of modularity and diagnosability aligns with circular economy principles, promoting practices such as repair and reuse. This project provides a tool to calculate the environmental impacts associated with the manufacturing, usage, and replacement of power electronics products.
Copyright (C) Mitsubishi Electric R&D Centre Europe and SATIE 2024, author Briac Baudais baudaisbriac@gmail.com

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this program.  If not, see https://www.gnu.org/licenses/lgpl-3.0.html"""

"""
Created on 2024

@author: baudais, bdubus

"""

import sys

import matplotlib
from PySide6.QtGui import QColor, QPalette, QIcon
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow

matplotlib.use("Agg")


# Réinitialiser stdout et stderr quand l'application se ferme
def reset_streams():
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    print("Streams reset.")


if __name__ == "__main__":
    # Create an instance of QApplication

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(":/ressources/icons/icon.ico"))
    # Set the application style
    app.setStyle("Fusion")

    # Create the main window
    window = MainWindow()

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
