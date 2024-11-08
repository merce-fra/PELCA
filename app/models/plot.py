from PySide6.QtCore import QObject, Signal


class IndexSwitcher(QObject):
    index_changed = Signal(int)

    def __init__(self, figs, mode_switcher):
        super().__init__()
        self.index = 0
        self.figs = figs
        self.mode_switcher = mode_switcher

    def get_max_index(self):
        return len(self.figs["plotly"] if self.mode_switcher.plotly_mode else self.figs["matplotlib"]) - 1

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


class ModeSwitcher(QObject):
    mode_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.plotly_mode = False

    def switch_mode(self):
        self.plotly_mode = not self.plotly_mode
        self.mode_changed.emit(self.plotly_mode)
