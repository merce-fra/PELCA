"""PELCA (Power Electronics Life Cycle Assessment) is an open-source project aimed at assessing the environmental impact over the life cycle of modular and diagnosable power electronics systems. The integration of modularity and diagnosability aligns with circular economy principles, promoting practices such as repair and reuse. This project provides a tool to calculate the environmental impacts associated with the manufacturing, usage, and replacement of power electronics products.
Copyright (C) Mitsubishi Electric R&D Centre Europe and SATIE 2024, author Briac Baudais baudaisbriac@gmail.com

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this program.  If not, see https://www.gnu.org/licenses/lgpl-3.0.html"""

"""
Created on 2024

@author: baudais, bdubus
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget


class HeaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self._add_header_image(layout)

        self.setLayout(layout)

    def _add_header_image(self, layout):
        """Add a centered header image to the layout."""
        header_label = QLabel()
        header_pixmap = QPixmap(":/ressources/images/first_image.png").scaled(
            413, 145, Qt.AspectRatioMode.KeepAspectRatio
        )
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
