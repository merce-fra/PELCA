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
