"""PELCA (Power Electronics Life Cycle Assessment) is an open-source project aimed at assessing the environmental impact over the life cycle of modular and diagnosable power electronics systems. The integration of modularity and diagnosability aligns with circular economy principles, promoting practices such as repair and reuse. This project provides a tool to calculate the environmental impacts associated with the manufacturing, usage, and replacement of power electronics products.
Copyright (C) Mitsubishi Electric R&D Centre Europe and SATIE 2024, author Briac Baudais baudaisbriac@gmail.com

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this program.  If not, see https://www.gnu.org/licenses/lgpl-3.0.html"""


"""
Created on 2024

@author: baudais
"""

import sys
from tkinter import END

import matplotlib

from pelcaGUI import PelcaGUI

matplotlib.use("Agg")  # Utiliser un backend non interactif
import io
import queue

import numpy as np


def on_closing():
    root.destroy()  # Ferme l'application proprement
    # Restaurer stdout et stderr
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__


class RedirectText(io.StringIO):
    def __init__(self, console_widget):
        super().__init__()
        self.console_widget = console_widget

    def write(self, string):
        super().write(string)
        self.console_widget.configure(state="normal")
        self.console_widget.insert(END, string)
        self.console_widget.configure(state="disabled")
        self.console_widget.see(END)
        self.flush()  # Assurez-vous que le tampon est vidé

    def flush(self):
        # Appelez explicitement flush sur la classe parente pour gérer le tampon
        super().flush()


output_queue = queue.Queue()


def update_console():
    try:
        while True:
            message = output_queue.get_nowait()  # Récupérer le message sans bloquer
            root.console_text.configure(state="normal")
            root.console_text.insert(END, message)
            root.console_text.configure(state="disabled")
            root.console_text.see(END)
    except queue.Empty:
        pass  # Ne rien faire si la queue est vide

    # Planifier la prochaine exécution de update_console dans le thread principal
    root.after(100, update_console)  # Vérifier les nouveaux messages toutes les 100 ms


root = PelcaGUI()

# Redirigez stdout et stderr
redirector = RedirectText(root.console_text)
sys.stdout = redirector
sys.stderr = redirector

# Initialisez l'index courant
current_index = 0

# Liaison de la fonction on_closing à l'événement de fermeture
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
root.after(100, update_console)  # Démarrer la boucle de mise à jour
