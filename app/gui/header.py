"""Shared banner image widget.

Exposes ``HeaderWidget``, a ``QWidget`` that renders the PELCA header image
from the embedded Qt resource file. Used by both ``MainWindow`` and
``ControlsWidget``.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget


class HeaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._setup_ui()

    def _setup_ui(self):
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
