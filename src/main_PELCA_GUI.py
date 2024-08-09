"""                   GNU LESSER GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.


  This version of the GNU Lesser General Public License incorporates
the terms and conditions of version 3 of the GNU General Public
License, supplemented by the additional permissions listed below.

  0. Additional Definitions.

  As used herein, "this License" refers to version 3 of the GNU Lesser
General Public License, and the "GNU GPL" refers to version 3 of the GNU
General Public License.

  "The Library" refers to a covered work governed by this License,
other than an Application or a Combined Work as defined below.

  An "Application" is any work that makes use of an interface provided
by the Library, but which is not otherwise based on the Library.
Defining a subclass of a class defined by the Library is deemed a mode
of using an interface provided by the Library.

  A "Combined Work" is a work produced by combining or linking an
Application with the Library.  The particular version of the Library
with which the Combined Work was made is also called the "Linked
Version".

  The "Minimal Corresponding Source" for a Combined Work means the
Corresponding Source for the Combined Work, excluding any source code
for portions of the Combined Work that, considered in isolation, are
based on the Application, and not on the Linked Version.

  The "Corresponding Application Code" for a Combined Work means the
object code and/or source code for the Application, including any data
and utility programs needed for reproducing the Combined Work from the
Application, but excluding the System Libraries of the Combined Work.

  1. Exception to Section 3 of the GNU GPL.

  You may convey a covered work under sections 3 and 4 of this License
without being bound by section 3 of the GNU GPL.

  2. Conveying Modified Versions.

  If you modify a copy of the Library, and, in your modifications, a
facility refers to a function or data to be supplied by an Application
that uses the facility (other than as an argument passed when the
facility is invoked), then you may convey a copy of the modified
version:

   a) under this License, provided that you make a good faith effort to
   ensure that, in the event an Application does not supply the
   function or data, the facility still operates, and performs
   whatever part of its purpose remains meaningful, or

   b) under the GNU GPL, with none of the additional permissions of
   this License applicable to that copy.

  3. Object Code Incorporating Material from Library Header Files.

  The object code form of an Application may incorporate material from
a header file that is part of the Library.  You may convey such object
code under terms of your choice, provided that, if the incorporated
material is not limited to numerical parameters, data structure
layouts and accessors, or small macros, inline functions and templates
(ten or fewer lines in length), you do both of the following:

   a) Give prominent notice with each copy of the object code that the
   Library is used in it and that the Library and its use are
   covered by this License.

   b) Accompany the object code with a copy of the GNU GPL and this license
   document.

  4. Combined Works.

  You may convey a Combined Work under terms of your choice that,
taken together, effectively do not restrict modification of the
portions of the Library contained in the Combined Work and reverse
engineering for debugging such modifications, if you also do each of
the following:

   a) Give prominent notice with each copy of the Combined Work that
   the Library is used in it and that the Library and its use are
   covered by this License.

   b) Accompany the Combined Work with a copy of the GNU GPL and this license
   document.

   c) For a Combined Work that displays copyright notices during
   execution, include the copyright notice for the Library among
   these notices, as well as a reference directing the user to the
   copies of the GNU GPL and this license document.

   d) Do one of the following:

       0) Convey the Minimal Corresponding Source under the terms of this
       License, and the Corresponding Application Code in a form
       suitable for, and under terms that permit, the user to
       recombine or relink the Application with a modified version of
       the Linked Version to produce a modified Combined Work, in the
       manner specified by section 6 of the GNU GPL for conveying
       Corresponding Source.

       1) Use a suitable shared library mechanism for linking with the
       Library.  A suitable mechanism is one that (a) uses at run time
       a copy of the Library already present on the user's computer
       system, and (b) will operate properly with a modified version
       of the Library that is interface-compatible with the Linked
       Version.

   e) Provide Installation Information, but only if you would otherwise
   be required to provide such information under section 6 of the
   GNU GPL, and only to the extent that such information is
   necessary to install and execute a modified version of the
   Combined Work produced by recombining or relinking the
   Application with a modified version of the Linked Version. (If
   you use option 4d0, the Installation Information must accompany
   the Minimal Corresponding Source and Corresponding Application
   Code. If you use option 4d1, you must provide the Installation
   Information in the manner specified by section 6 of the GNU GPL
   for conveying Corresponding Source.)

  5. Combined Libraries.

  You may place library facilities that are a work based on the
Library side by side in a single library together with other library
facilities that are not Applications and are not covered by this
License, and convey such a combined library under terms of your
choice, if you do both of the following:

   a) Accompany the combined library with a copy of the same work based
   on the Library, uncombined with any other library facilities,
   conveyed under the terms of this License.

   b) Give prominent notice with the combined library that part of it
   is a work based on the Library, and explaining where to find the
   accompanying uncombined form of the same work.

  6. Revised Versions of the GNU Lesser General Public License.

  The Free Software Foundation may publish revised and/or new versions
of the GNU Lesser General Public License from time to time. Such new
versions will be similar in spirit to the present version, but may
differ in detail to address new problems or concerns.

  Each version is given a distinguishing version number. If the
Library as you received it specifies that a certain numbered version
of the GNU Lesser General Public License "or any later version"
applies to it, you have the option of following the terms and
conditions either of that published version or of any later version
published by the Free Software Foundation. If the Library as you
received it does not specify a version number of the GNU Lesser
General Public License, you may choose any version of the GNU Lesser
General Public License ever published by the Free Software Foundation.

  If the Library as you received it specifies that a proxy can decide
whether future versions of the GNU Lesser General Public License shall
apply, that proxy's public statement of acceptance of any version is
permanent authorization for you to choose that version for the
Library."""

"""
Created on 2024

@author: baudais
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox, Text, END, Frame
from PIL import Image
import os
import sys
import LCA
import dictionary
import staircase
import plotting
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from io import BytesIO
from customtkinter import CTkImage
import io
import queue
import threading
import pandas as pd
import numpy as np

is_running = False

def reset_interface():
    """ Réinitialise l'interface graphique à son état initial. """

    # Fonction pour effectuer la réinitialisation dans le thread principal
    def do_reset():
        # Effacer les graphiques
        for widget in plot_frame.winfo_children():
            widget.destroy()
        
        # Effacer les miniatures des boutons
        for widget in selection_frame.winfo_children():
            widget.destroy()

        
        # Réinitialiser les états des boutons
        prev_button.configure(state="disabled")
        next_button.configure(state="disabled")
        save_button.configure(state="disabled")
        save_selected_button.configure(state="disabled")
        save_data_button.configure(state="disabled")

        # Réinitialiser les cases à cocher
        var_EI.set("")
        var_EI_manu.set("")
        var_EI_use.set("")
        var_fault_cause.set("")
        var_RU_age.set("")
        checkbox_EI.configure(state="disabled")
        checkbox_EI_manu.configure(state="disabled")
        checkbox_EI_use.configure(state="disabled")
        checkbox_fault_cause.configure(state="disabled")
        checkbox_RU_age.configure(state="disabled")

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
    """ Crée une image miniature de la figure pour la compatibilité CTkImage """
    with BytesIO() as buf:
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
        buf.seek(0)
        img = Image.open(buf)
        img.thumbnail(size)
        return CTkImage(dark_image=img, size=size)

def create_figure_buttons():
    # Efface les boutons précédents
    for widget in selection_frame.winfo_children():
        widget.destroy()

    for idx, fig in enumerate(figs):
        thumb_image = create_thumbnail(fig)
        button = ctk.CTkButton(
            selection_frame,
            image=thumb_image,
            command=lambda i=idx: update_and_display_plot(i),
            fg_color=button_color,
            text_color=fg_color,
            width=120,
            height=120,
            text=''
        )
        button.image = thumb_image  # Garder une référence pour éviter la collecte de déchets
        button.pack(fill='x', padx=5, pady=5)

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
        self.console_widget.configure(state='normal')
        self.console_widget.insert(END, string)
        self.console_widget.configure(state='disabled')
        self.console_widget.see(END)
        self.flush()  # Assurez-vous que le tampon est vidé

    def flush(self):
        # Appelez explicitement flush sur la classe parente pour gérer le tampon
        super().flush()

def browse_file():
    filepath = filedialog.askopenfilename()
    if filepath:
        entry_file_path.delete(0, ctk.END)
        entry_file_path.insert(0, filepath)

def get_max_fig_size(figs):
    """ Retourne la taille de la plus grande figure """
    max_width = 0
    max_height = 0
    for fig in figs:
        fig_width, fig_height = fig.get_size_inches() * fig.dpi
        max_width = max(max_width, fig_width)
        max_height = max(max_height, fig_height)
    return (int(max_width), int(max_height))

def display_plot(index):
    # Efface le graphique précédent
    for widget in plot_frame.winfo_children():
        widget.destroy()

    # Affiche le graphique actuel
    fig = figs[index]
    
    # Ajuster la taille de la figure si nécessaire
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
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
                    filepath = os.path.join(folder_path, f"plot_{idx+1}.png")
                    fig.savefig(filepath, dpi=1200)
                print(f"All plots saved successfully in {folder_path}")
            except Exception as e:
                print(f"An error occurred while saving the plots: {e}")

def save_selected_plot():
    """ Sauvegarde le graphique actuellement affiché """
    if figs:
        if current_index is not None:
            folder_path = filedialog.askdirectory()
            if folder_path:
                try:
                    fig = figs[current_index]
                    filepath = os.path.join(folder_path, f"selected_plot_{current_index + 1}.png")
                    fig.savefig(filepath, dpi=1200)
                    print(f"Selected plot saved successfully as {filepath}")
                except Exception as e:
                    print(f"An error occurred while saving the selected plot: {e}")
        else:
            print("No plot is currently displayed.")
    else:
        print("No plots available to save.") 

def _export_data(path,file_name,file):
    file_name_pickel=file_name +'.npy'
    path_file_pickel = os.path.join(path,"",file_name_pickel)
    with open(path_file_pickel, 'wb') as f:
        np.save(f,file)

def save_data_to_excel():
    folder_path = filedialog.askdirectory()
    if folder_path:
        try:
            if var_EI.get():
                _export_data(folder_path, "Impact_total", EI)
            if var_EI_manu.get():
                _export_data(folder_path, "Impact_manu", EI_manu)
            if var_EI_use.get():
                _export_data(folder_path, "Impact_use", EI_use)
            if var_fault_cause.get():
                _export_data(folder_path, "fault_cause", fault_cause)
            if var_RU_age.get():
                _export_data(folder_path, "RU_age", RU_age)
            print(f"Selected data saved successfully in {folder_path}")
        except Exception as e:
            print(f"An error occurred while saving the data: {e}")

output_queue = queue.Queue()

def update_console():
    while True:
        try:
            message = output_queue.get_nowait()
            console_text.configure(state='normal')
            console_text.insert(END, message)
            console_text.configure(state='disabled')
            console_text.see(END)
        except queue.Empty:
            break
    root.after(100, update_console)  # Vérifier les nouveaux messages toutes les 100 ms

def update_ui(simulation_type):
    prev_button.configure(state="normal")
    next_button.configure(state="normal")
    save_button.configure(state="normal")
    save_selected_button.configure(state="normal")
    if simulation_type == 'Analysis':
        save_data_button.configure(state="normal")
        checkbox_EI.configure(state="normal")
        checkbox_EI_manu.configure(state="normal")
        checkbox_EI_use.configure(state="normal")
        checkbox_fault_cause.configure(state="normal")
        checkbox_RU_age.configure(state="normal")

def run_script():
    global figs
    global current_index
    global EI, EI_manu, EI_use, RU_age, fault_cause
    
    full_path_input = entry_file_path.get()
    if not full_path_input:
        messagebox.showerror("Error", "Please select an input file")
        return
    
    path_input = os.path.dirname(full_path_input)
    name_input = os.path.basename(full_path_input)

    def finish_script_execution(message):
        loading_label.configure(text=message)
        root.after(0, update_ui(dic["simulation"]))  # Planifie la mise à jour de l'UI dans le thread principal

    loading_label.configure(text="Running script...")
    root.update_idletasks()  # Met à jour l'interface pour afficher le message de chargement

    try:
        # Init du dictionnaire
        dic = dictionary._init_dic(path_input, name_input)

        # LCA
        if dic["LCA"] == 'yes':
            LCA.EI_calculation(dic, path_input, name_input)
        
        if dic["simulation"] == 'Analysis':
            # Création de la courbe de l'escalier
            print("\nCreating the Staircase Curve...")
            staircase_instance = staircase.STAIRCASE(path_input, name_input, dic)
            EI, EI_manu, EI_use, usage_time, number_of_fault, wcdf, fault_cause, RU_age = staircase_instance.get_variables()
            print("\n... Staircase Curve Completed")
            
            print("\nDisplaying the results...")
            plot_instance = plotting.PLOT(dic, EI, EI_manu, EI_use, usage_time, fault_cause, dic["nb_RU"], dic["nb_ite_MC"], dic["step"], wcdf)
            figs = [plot_instance.fig1, plot_instance.fig2, plot_instance.fig3, plot_instance.fig4, plot_instance.fig5]
            
            print("\nPELCA executed successfully\n")

        if dic["simulation"] == 'Monte Carlo':
            print("\nDisplaying the results...")
            plot_instance = plotting.PLOT_MC(dic)
            figs = [plot_instance.fig1, plot_instance.fig2]
            print("\nPELCA executed successfully\n")
            
        # Calculer la taille maximale des figures
        max_width, max_height = get_max_fig_size(figs)
        
        # Définir la taille de plot_frame
        plot_frame.configure(width=max_width, height=max_height)
        plot_frame.pack_propagate(False)  # Empêche le cadre de se redimensionner pour s'adapter à son contenu

        current_index = 0

        display_plot(current_index)
        
        # Créer les boutons de sélection des figures avec des miniatures
        create_figure_buttons()

        finish_script_execution("Script executed successfully")

    except Exception as e:
        finish_script_execution("An error occurred: " + str(e))

# Créez la fenêtre principale
root = ctk.CTk()
root.title("PELCA")

# Définir les couleurs du thème sombre
bg_color = "#2E2E2E"
fg_color = "#FFFFFF"
button_color = "#4E4E4E"
separator_color = "#242424"

root.configure(bg=bg_color)

# Récupérer les chemins des variables d'environnement
icon_path = os.getenv('ICON_PATH', 'assets/icon.ico')
image_path = os.getenv('IMAGE_PATH', 'assets/first_image.png')

# Charger l'icône
root.after(201, lambda: root.iconbitmap(icon_path))

# Charger l'image du haut
top_image = ctk.CTkImage(dark_image=Image.open(image_path), size=(1654//4, 578//4))
image_label = ctk.CTkLabel(root, image=top_image, text='')
image_label.pack(pady=10)

# Créez et placez les widgets
main_frame = ctk.CTkFrame(root, fg_color=bg_color)
main_frame.pack(padx=10, pady=10, fill='both', expand=True)

left_frame = ctk.CTkFrame(main_frame, fg_color=bg_color)
left_frame.pack(side='left', padx=10, pady=10, fill='y')

right_frame = ctk.CTkFrame(main_frame, fg_color=bg_color)
right_frame.pack(side='right', fill='both', expand=True)

separator_frame = ctk.CTkFrame(main_frame, width=8, height=600, fg_color=separator_color)
separator_frame.pack(side='left', fill='y')

# Frame pour les données et le bouton de sauvegarde
data_frame = ctk.CTkFrame(right_frame, fg_color=bg_color)
data_frame.pack(side='bottom', fill='x', padx=10, pady=10)

var_EI = ctk.StringVar()
var_EI_manu = ctk.StringVar()
var_EI_use = ctk.StringVar()
var_fault_cause = ctk.StringVar()
var_RU_age = ctk.StringVar()

checkbox_EI = ctk.CTkCheckBox(data_frame, text="Impact total", variable=var_EI, onvalue='EI', offvalue='', state="disabled")
checkbox_EI.pack(side='left', padx=5)

checkbox_EI_manu = ctk.CTkCheckBox(data_frame, text="Impact manufact.", variable=var_EI_manu, onvalue='EI_manu', offvalue='', state="disabled")
checkbox_EI_manu.pack(side='left', padx=5)

checkbox_EI_use = ctk.CTkCheckBox(data_frame, text="Impact use", variable=var_EI_use, onvalue='EI_use', offvalue='', state="disabled")
checkbox_EI_use.pack(side='left', padx=5)

checkbox_fault_cause = ctk.CTkCheckBox(data_frame, text="Fault cause", variable=var_fault_cause, onvalue='fault_cause', offvalue='', state="disabled")
checkbox_fault_cause.pack(side='left', padx=5)

checkbox_RU_age = ctk.CTkCheckBox(data_frame, text="RU age", variable=var_RU_age, onvalue='RU_age', offvalue='', state="disabled")
checkbox_RU_age.pack(side='left', padx=5)

save_data_button = ctk.CTkButton(data_frame, text="Save Data", command=save_data_to_excel, fg_color=button_color, text_color=fg_color, state="disabled")
save_data_button.pack(side='left', padx=10)

# Frame pour les boutons de navigation en haut
nav_buttons_frame = ctk.CTkFrame(right_frame, fg_color=bg_color)
nav_buttons_frame.pack(side='top', fill='x', padx=10, pady=10)

# Frame pour les graphiques, centrée dans le frame droit
plot_frame = ctk.CTkFrame(right_frame, fg_color=bg_color)
plot_frame.pack(side='left', padx=10, pady=10, expand=True)
plot_frame.pack_propagate(False)

# Frame pour la sélection des graphiques, placée à droite des graphiques
selection_frame = ctk.CTkFrame(right_frame, fg_color=bg_color)
selection_frame.pack(side='right', fill='y', padx=10, pady=10)

# Frame pour les espaces en haut et en bas
top_spacer = Frame(right_frame, bg=bg_color)
top_spacer.pack(side='top', fill='both', expand=True)

bottom_spacer = Frame(right_frame, bg=bg_color)
bottom_spacer.pack(side='bottom', fill='both', expand=True)

# Créez les boutons de navigation dans la nouvelle frame
prev_button = ctk.CTkButton(nav_buttons_frame, text="Previous", command=show_prev_plot, fg_color=button_color, text_color=fg_color, state="disabled")
next_button = ctk.CTkButton(nav_buttons_frame, text="Next", command=show_next_plot, fg_color=button_color, text_color=fg_color, state="disabled")
save_button = ctk.CTkButton(nav_buttons_frame, text="Save All", command=save_plot, fg_color=button_color, text_color=fg_color, state="disabled")
save_selected_button = ctk.CTkButton(nav_buttons_frame, text="Save", command=save_selected_plot, fg_color=button_color, text_color=fg_color, state="disabled")

prev_button.pack(side='left', padx=5, pady=5)
next_button.pack(side='left', padx=5, pady=5)
save_selected_button.pack(side='left', padx=5, pady=5)
save_button.pack(side='top', fill='x', padx=5, pady=10)

nav_buttons_frame.grid_columnconfigure(0, weight=1)
nav_buttons_frame.grid_columnconfigure(1, weight=1)
nav_buttons_frame.grid_columnconfigure(2, weight=1)

# Créez les widgets pour left_frame (inchangé)
label_file_path = ctk.CTkLabel(left_frame, text="Select Input File:", fg_color=bg_color, text_color=fg_color)
label_file_path.grid(row=0, column=0, padx=5, pady=5)

entry_file_path = ctk.CTkEntry(left_frame, width=300, fg_color=button_color, text_color=fg_color)
entry_file_path.grid(row=0, column=1, padx=5, pady=5)

button_browse = ctk.CTkButton(left_frame, text="Browse", command=browse_file, fg_color=button_color, text_color=fg_color)
button_browse.grid(row=0, column=2, padx=5, pady=5)

button_run = ctk.CTkButton(left_frame, text="Run Script", command=run_script_threaded, fg_color=button_color, text_color=fg_color)
button_run.grid(row=1, column=0, columnspan=3, pady=10)

loading_label = ctk.CTkLabel(left_frame, text="", fg_color=bg_color, text_color=fg_color)
loading_label.grid(row=2, column=0, columnspan=3, pady=5)

# Créez le widget console
console_frame = ctk.CTkFrame(left_frame, fg_color=bg_color)
console_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky='nswe')

console_text = Text(console_frame, bg=bg_color, fg=fg_color, wrap='word', state='disabled')
console_text.pack(padx=10, pady=10, fill='both', expand=True)

# Redirigez stdout et stderr
sys.stdout = RedirectText(console_text)
sys.stderr = RedirectText(console_text)

# Initialisez l'index courant
current_index = 0

# Démarrez la boucle principale
root.mainloop()
root.after(100, update_console)  # Démarrer la boucle de mise à jour

