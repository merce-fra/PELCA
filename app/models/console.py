from PySide6.QtCore import QObject, Signal


class ConsoleOutputRedirector(QObject):
    """Signal-based console output redirector to update console text from threads safely."""

    new_text = Signal(str)

    def write(self, text):
        """Emit text signal with stripped trailing newlines."""
        self.new_text.emit(text.rstrip("\n"))

    def flush(self):
        """Required to comply with io.TextIOBase."""
        pass
