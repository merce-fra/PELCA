"""PELCA (Power Electronics Life Cycle Assessment) is an open-source project aimed at assessing the environmental impact over the life cycle of modular and diagnosable power electronics systems. The integration of modularity and diagnosability aligns with circular economy principles, promoting practices such as repair and reuse. This project provides a tool to calculate the environmental impacts associated with the manufacturing, usage, and replacement of power electronics products.
Copyright (C) Mitsubishi Electric R&D Centre Europe and SATIE 2024, author Briac Baudais baudaisbriac@gmail.com

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this program.  If not, see https://www.gnu.org/licenses/lgpl-3.0.html"""

"""
Created on 2024

@author: baudais, bdubus
"""
from PySide6.QtCore import QObject, Signal


class IndexSwitcher(QObject):
    index_changed = Signal(int)

    def __init__(self, figs,):
        super().__init__()
        self.index = 0
        self.figs = figs

    def get_max_index(self):
        return len(self.figs["plots"]) - 1

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

