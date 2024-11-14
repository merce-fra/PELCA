from PySide6.QtCore import QObject, Signal

class EmittingStream(QObject):
    text_written = Signal(str)

    def write(self, text):
        if text.strip():
            self.text_written.emit(text)

    def flush(self):
        pass