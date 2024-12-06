from PySide6.QtCore import QObject, Signal


class IndexSwitcher(QObject):
    index_changed = Signal(int)

    def __init__(self, figs,):
        super().__init__()
        self.index = 0
        self.figs = figs

    def get_max_index(self):
        return len(self.figs["plotly"])

    def set_index(self, index):
        self.index = index
        self.index_changed.emit(index)

    def get_index(self):
        return self.index

    def increment_index(self):
        self.index = (self.index + 1) % (self.get_max_index() + 1)
        self.index_changed.emit(self.index)

    def decrement_index(self):
        self.index = (self.index - 1) % (self.get_max_index() + 1)
        self.index_changed.emit(self.index)

