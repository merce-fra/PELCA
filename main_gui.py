"""PELCA GUI entry point.

Initialises the Qt application, applies the dark Fusion theme, and opens
``MainWindow``. Also provides ``reset_streams()`` to restore standard I/O on exit.
"""

import logging
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

# Import the compiled Qt resource module so embedded assets are available
# before QApplication is created (required for the splash screen pixmap).
from app.gui.resources import ressources_rc  # type: ignore # noqa: F401

VERSION = "PELCA V2.0.0"

_log = logging.getLogger(__name__)


def reset_streams():
    """Restore stdout/stderr when the application exits."""
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    _log.debug("Streams reset.")


if __name__ == "__main__":
    # Must be set before QApplication is instantiated (required by OpenGL-based widgets).
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    # Create the application and set the icon
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(":/ressources/icons/icon.ico"))

    # Show a splash screen immediately so the user knows the app is loading.
    # First launch can be slow due to brightway2 database initialisation.
    splash_pixmap = QPixmap(":/ressources/images/first_image.png")
    # Scale the logo to half its original size.
    splash_pixmap = splash_pixmap.scaled(
        splash_pixmap.width() // 2,
        splash_pixmap.height() // 2,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    # Composite onto an opaque background so the alpha channel of the PNG
    # does not make the splash window appear transparent.
    opaque_pixmap = QPixmap(splash_pixmap.size())
    opaque_pixmap.fill(QColor(53, 53, 53))
    painter = QPainter(opaque_pixmap)
    painter.drawPixmap(0, 0, splash_pixmap)
    painter.end()
    splash = QSplashScreen(opaque_pixmap, Qt.WindowType.WindowStaysOnTopHint)
    # Use a large bold font so the message stands out clearly.
    splash_font = QFont()
    splash_font.setPointSize(14)
    splash_font.setBold(True)
    splash.setFont(splash_font)
    splash.showMessage(
        "Loading PELCA, please wait\u2026",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        QColor(255, 220, 50),
    )
    splash.show()
    # Process pending events so the splash is painted before the heavy import chain runs.
    app.processEvents()

    # Defer the import so brightway2 and the full app initialise while the splash is visible.
    from app.gui.main import MainWindow  # noqa: PLC0415

    # Apply the dark "Fusion" theme
    # (consistent cross-platform baseline for the dark palette overrides)
    app.setStyle("Fusion")

    # Define and apply a custom dark palette
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

    # Create the main window
    window = MainWindow(VERSION)
    window.show()

    # Dismiss the splash screen now that the main window is visible.
    splash.finish(window)

    # Restore standard streams before Qt tears down its event loop.
    app.aboutToQuit.connect(reset_streams)

    # Execute the application
    sys.exit(app.exec())
