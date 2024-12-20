from PySide6.QtCore import QObject, Signal


class EmittingStream(QObject):
    text_written = Signal(str)

    def write(self, text):
        """
        Émet le texte vers le signal. Ajoute un retour à la ligne si nécessaire.
        """
        if text:
            # Ajoute un retour à la ligne si le texte n'en contient pas à la fin
            if not text.endswith('\n'):
                text += '\n'
            self.text_written.emit(text)

    def flush(self):
        pass

    def fileno(self):
        return 1
