"""PELCA (Power Electronics Life Cycle Assessment) is an open-source project aimed at assessing the environmental impact over the life cycle of modular and diagnosable power electronics systems. The integration of modularity and diagnosability aligns with circular economy principles, promoting practices such as repair and reuse. This project provides a tool to calculate the environmental impacts associated with the manufacturing, usage, and replacement of power electronics products.
Copyright (C) Mitsubishi Electric R&D Centre Europe and SATIE 2024, author Briac Baudais baudaisbriac@gmail.com

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this program.  If not, see https://www.gnu.org/licenses/lgpl-3.0.html"""


"""
Created on 2024

@author: baudais
"""

import os
import sys
from tkinter import END, filedialog, messagebox

import customtkinter as ctk
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image

import dictionary
import LCA
import plotting
import staircase
from pelcaGUI import BUTTON_COLOR, FG_COLOR, PelcaGUI

matplotlib.use("Agg")  # Utiliser un backend non interactif
import io
import queue
import threading
from io import BytesIO

import numpy as np
from bw2data.errors import InvalidExchange
from customtkinter import CTkImage

is_running = False


def on_closing():
    root.destroy()  # Ferme l'application proprement
    # Restaurer stdout et stderr
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__


def reset_interface():
    """Réinitialise l'interface graphique à son état initial."""

    # Fonction pour effectuer la réinitialisation dans le thread principal
    def do_reset():
        # Effacer les graphiques
        for widget in root.plot_frame.winfo_children():
            widget.destroy()

        # Effacer les miniatures des boutons
        for widget in root.selection_frame.winfo_children():
            widget.destroy()

        # Réinitialiser les états des boutons
        root.prev_button.configure(state="disabled")
        root.next_button.configure(state="disabled")
        root.save_button.configure(state="disabled")
        root.save_selected_button.configure(state="disabled")
        root.save_data_button.configure(state="disabled")

        # Réinitialiser les cases à cocher
        root.var_EI.set("")
        root.var_EI_manu.set("")
        root.var_EI_use.set("")
        root.var_fault_cause.set("")
        root.var_RU_age.set("")
        root.checkbox_EI.configure(state="disabled")
        root.checkbox_EI_manu.configure(state="disabled")
        root.checkbox_EI_use.configure(state="disabled")
        root.checkbox_fault_cause.configure(state="disabled")
        root.checkbox_RU_age.configure(state="disabled")

    # Planifier la réinitialisation pour le thread principal
    root.after(100, do_reset)


def run_script_threaded():
    global is_running
    if is_running:
        # Réinitialiser l'interface
        reset_interface()
    # Exécuter la fonction run_script dans un thread séparé après un petit délai
    threading.Thread(target=run_script).start()
    is_running = True


def create_thumbnail(fig, size=(100, 100)):
    """Crée une image miniature de la figure pour la compatibilité CTkImage"""
    with BytesIO() as buf:
        fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
        buf.seek(0)
        img = Image.open(buf)
        img.thumbnail(size)
        return CTkImage(dark_image=img, size=size)


def create_figure_buttons():
    for widget in root.selection_frame.winfo_children():
        widget.destroy()

    for idx, fig in enumerate(figs):
        thumb_image = create_thumbnail(fig)
        button = ctk.CTkButton(
            root.selection_frame,
            image=thumb_image,
            command=lambda i=idx: update_and_display_plot(i),
            fg_color=BUTTON_COLOR,
            text_color=FG_COLOR,
            width=120,
            height=60,
            text="",
        )
        button.image = thumb_image  # Garder une référence pour éviter la collecte de déchets
        button.pack(fill="x", padx=5, pady=5)


def update_and_display_plot(i):
    global current_index
    current_index = i
    display_plot(i)


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


def browse_file():
    filepath = filedialog.askopenfilename()
    if filepath:
        root.entry_file_path.delete(0, ctk.END)
        root.entry_file_path.insert(0, filepath)


def get_max_fig_size(figs):
    """Retourne la taille de la plus grande figure"""
    max_width = 0
    max_height = 0
    for fig in figs:
        fig_width, fig_height = fig.get_size_inches() * fig.dpi
        max_width = max(max_width, fig_width)
        max_height = max(max_height, fig_height)
    return (int(max_width), int(max_height))


def display_plot(index):
    # Efface le graphique précédent
    for widget in root.plot_frame.winfo_children():
        widget.destroy()

    # Affiche le graphique actuel
    fig = figs[index]

    # Ajuster la taille de la figure si nécessaire
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=root.plot_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side="top", fill="both", expand=1)


def show_next_plot():
    global current_index
    if current_index < len(figs) - 1:
        current_index += 1
        display_plot(current_index)
    elif current_index == len(figs) - 1:
        current_index = 0
        display_plot(current_index)


def show_prev_plot():
    global current_index
    if current_index > 0:
        current_index -= 1
        display_plot(current_index)
    elif current_index == 0:
        current_index = len(figs) - 1
        display_plot(current_index)


def save_plot():
    print("Saving plots...")
    if figs:
        folder_path = filedialog.askdirectory()
        if folder_path:
            try:
                for idx, fig in enumerate(figs):
                    filepath = os.path.join(folder_path, f"plot_{idx+1}.svg")
                    fig.savefig(filepath, dpi=300)
                print(f"All plots saved successfully in {folder_path}")
            except Exception as e:
                print(f"An error occurred while saving the plots: {e}")


def save_selected_plot():
    """Sauvegarde le graphique actuellement affiché"""
    if figs:
        if current_index is not None:
            folder_path = filedialog.askdirectory()
            if folder_path:
                try:
                    fig = figs[current_index]
                    filepath = os.path.join(folder_path, f"selected_plot_{current_index + 1}.svg")
                    fig.savefig(filepath, dpi=300)
                    print(f"Selected plot saved successfully as {filepath}")
                except Exception as e:
                    print(f"An error occurred while saving the selected plot: {e}")
        else:
            print("No plot is currently displayed.")
    else:
        print("No plots available to save.")


def _export_data(path, file_name, file):
    file_name_pickel = file_name + ".npy"
    path_file_pickel = os.path.join(path, "", file_name_pickel)
    with open(path_file_pickel, "wb") as f:
        np.save(f, file)


def save_data_to_excel():
    folder_path = filedialog.askdirectory()
    if folder_path:
        try:
            if root.var_EI.get():
                _export_data(folder_path, "Impact_total", EI)
            if root.var_EI_manu.get():
                _export_data(folder_path, "Impact_manu", EI_manu)
            if root.var_EI_use.get():
                _export_data(folder_path, "Impact_use", EI_use)
            if root.var_fault_cause.get():
                _export_data(folder_path, "fault_cause", fault_cause)
            if root.var_RU_age.get():
                _export_data(folder_path, "RU_age", RU_age)
            print(f"Selected data saved successfully in {folder_path}")
        except Exception as e:
            print(f"An error occurred while saving the data: {e}")


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


def update_ui(simulation_type):
    root.prev_button.configure(state="normal")
    root.next_button.configure(state="normal")
    root.save_button.configure(state="normal")
    root.save_selected_button.configure(state="normal")
    if simulation_type == "Analysis":
        root.save_data_button.configure(state="normal")
        root.checkbox_EI.configure(state="normal")
        root.checkbox_EI_manu.configure(state="normal")
        root.checkbox_EI_use.configure(state="normal")
        root.checkbox_fault_cause.configure(state="normal")
        root.checkbox_RU_age.configure(state="normal")


def run_script():
    global figs
    global current_index
    global EI, EI_manu, EI_use, RU_age, fault_cause

    # Ferme toutes les figures ouvertes
    plt.close("all")

    full_path_input = root.entry_file_path.get()
    if not full_path_input:
        messagebox.showerror("Error", "Please select an input file")
        return

    path_input = os.path.dirname(full_path_input)
    name_input = os.path.basename(full_path_input)

    def finish_script_execution(message):
        root.loading_label.configure(text=message)
        root.after(0, update_ui(dic["simulation"]))  # Planifie la mise à jour de l'UI dans le thread principal

    root.loading_label.configure(text="Running script...")
    root.update_idletasks()  # Met à jour l'interface pour afficher le message de chargement

    try:
        # Init du dictionnaire
        dic = dictionary._init_dic(path_input, name_input)

        # LCA
        if dic["LCA"] == "yes":
            LCA.EI_calculation(dic, path_input, name_input)

        if dic["simulation"] == "Analysis":
            # Création de la courbe de l'escalier
            print("\nCreating the Staircase Curve...")
            staircase_instance = staircase.STAIRCASE(path_input, name_input, dic)
            (
                EI,
                EI_manu,
                EI_use,
                usage_time,
                number_of_fault,
                wcdf,
                fault_cause,
                RU_age,
                EI_maintenance,
            ) = staircase_instance.get_variables(dic)
            print("\n... Staircase Curve Completed")

            print("\nDisplaying the results...")
            plot_instance = plotting.PLOT(
                dic,
                EI,
                EI_manu,
                EI_use,
                usage_time,
                fault_cause,
                dic["nb_RU"],
                dic["nb_ite_MC"],
                dic["step"],
                wcdf,
                EI_maintenance,
            )
            figs = [
                plot_instance.fig1,
                plot_instance.fig2,
                plot_instance.fig3,
                plot_instance.fig4,
                plot_instance.fig5,
                plot_instance.fig6,
            ]

            print("\nPELCA executed successfully\n")

        if dic["simulation"] == "Monte Carlo":
            print("\nDisplaying the results...")
            plot_instance = plotting.PLOT_MC(dic)
            figs = [plot_instance.fig1, plot_instance.fig2]
            print("\nPELCA executed successfully\n")

        # Calculer la taille maximale des figures
        max_width, max_height = get_max_fig_size(figs)

        # Définir la taille de plot_frame
        root.plot_frame.configure(width=max_width, height=max_height)
        root.plot_frame.pack_propagate(True)  # Empêche le cadre de se redimensionner pour s'adapter à son contenu

        current_index = 0

        display_plot(current_index)

        # Créer les boutons de sélection des figures avec des miniatures
        create_figure_buttons()

        finish_script_execution("Script executed successfully")

    except InvalidExchange:
        finish_script_execution("An error occurred : Exchange is missing ‘amount’ or ‘input’")
    except BaseException as e:
        finish_script_execution("An error occurred: " + str(e))


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
