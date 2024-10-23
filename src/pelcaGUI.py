import os
from tkinter import Text, filedialog, messagebox

import customtkinter as ctk
import matplotlib.pyplot as plt
from bw2data.errors import InvalidExchange
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image

import dictionary
import LCA
import plotting
import staircase
from utils import create_thumbnail, export_data, get_max_fig_size

# Define colors for the dark theme
BG_COLOR = "#2E2E2E"
FG_COLOR = "#FFFFFF"
BUTTON_COLOR = "#4E4E4E"
SEPARATOR_COLOR = "#242424"

# Set appearance mode to dark
ctk.set_appearance_mode("dark")

# Constants for icon and image paths
DEFAULT_ICON_PATH = os.path.join("assets", "icon.ico")
ICON_ENV_VAR = "ICON_PATH"
IMAGE_PATH = os.getenv("IMAGE_PATH", os.path.join("assets", "first_image.png"))


class PelcaGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.setup_window()
        self.initialize_variables()
        self.create_ui_elements()
        self.is_running = False
        self.figs = []

    def setup_window(self):
        self.title("PELCA")
        self.set_window_icon()
        self.configure(bg=BG_COLOR)
        self.current_index = 0
        self._add_top_image()

    def set_window_icon(self):
        icon_path = os.getenv(ICON_ENV_VAR, DEFAULT_ICON_PATH)
        self.after(201, lambda: self.iconbitmap(icon_path))

    def initialize_variables(self):
        self.var_EI = ctk.StringVar()
        self.var_EI_manu = ctk.StringVar()
        self.var_EI_use = ctk.StringVar()
        self.var_fault_cause = ctk.StringVar()
        self.var_RU_age = ctk.StringVar()

    def create_ui_elements(self):
        self.main_frame = self.create_main_frame()
        self.create_navigation_buttons()
        self.create_console_frame()
        self.create_file_selection_elements()
        self.create_run_button()
        self.create_loading_label()

    def create_main_frame(self):
        main_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)
        self.left_frame = self.create_left_frame(main_frame)
        self.right_frame = self.create_right_frame(main_frame)
        self.create_separator_frame(main_frame)
        return main_frame

    def create_left_frame(self, parent):
        left_frame = ctk.CTkFrame(parent, fg_color=BG_COLOR)
        left_frame.pack(side="left", padx=10, pady=10, fill="y")
        return left_frame

    def create_right_frame(self, parent):
        right_frame = ctk.CTkFrame(parent, fg_color=BG_COLOR)
        right_frame.pack(side="right", fill="both", expand=True)
        self.data_frame = self.create_data_frame(right_frame)
        return right_frame

    def create_separator_frame(self, parent):
        separator_frame = ctk.CTkFrame(parent, width=8, fg_color=SEPARATOR_COLOR)
        separator_frame.pack(side="left", fill="y")
        return separator_frame

    def create_data_frame(self, parent):
        data_frame = ctk.CTkFrame(parent, fg_color=BG_COLOR)
        data_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        self.add_checkboxes(data_frame)
        self.create_save_data_button(data_frame)
        return data_frame

    def add_checkboxes(self, parent):
        self.checkbox_EI = self.create_checkbox(parent, "Impact total", self.var_EI, "EI")
        self.checkbox_EI_manu = self.create_checkbox(parent, "Impact manufact.", self.var_EI_manu, "EI_manu")
        self.checkbox_EI_use = self.create_checkbox(parent, "Impact use", self.var_EI_use, "EI_use")
        self.checkbox_fault_cause = self.create_checkbox(parent, "Fault cause", self.var_fault_cause, "fault_cause")
        self.checkbox_RU_age = self.create_checkbox(parent, "RU age", self.var_RU_age, "RU_age")

    def create_checkbox(self, parent, text, variable, onvalue):
        checkbox = ctk.CTkCheckBox(parent, text=text, variable=variable, onvalue=onvalue, offvalue="", state="disabled")
        checkbox.pack(side="left", padx=5)
        return checkbox

    def create_save_data_button(self, parent):
        self.save_data_button = ctk.CTkButton(
            parent,
            text="Save Data",
            command=self.save_data_to_excel,
            fg_color=BUTTON_COLOR,
            text_color=FG_COLOR,
            state="disabled",
        )
        self.save_data_button.pack(side="left", padx=10)

    def create_navigation_buttons(self):
        nav_buttons_frame = ctk.CTkFrame(self.right_frame, fg_color=BG_COLOR)
        nav_buttons_frame.pack(side="top", fill="x", padx=10, pady=10)
        self.prev_button = self.create_nav_button(nav_buttons_frame, "Previous", self.show_prev_plot)
        self.next_button = self.create_nav_button(nav_buttons_frame, "Next", self.show_next_plot)
        self.save_selected_button = self.create_nav_button(nav_buttons_frame, "Save", self.save_selected_plot)
        self.save_button = self.create_nav_button(nav_buttons_frame, "Save All", self.save_plot)
        self.create_plot_and_selection_frames()

    def create_nav_button(self, parent, text, command):
        button = ctk.CTkButton(
            parent, text=text, command=command, fg_color=BUTTON_COLOR, text_color=FG_COLOR, state="disabled"
        )
        button.pack(side="left", padx=5, pady=5)
        return button

    def create_plot_and_selection_frames(self):
        self.plot_frame = ctk.CTkFrame(self.right_frame, fg_color=BG_COLOR)
        self.plot_frame.pack(side="left", padx=10, pady=10, expand=True)
        self.plot_frame.pack_propagate(False)
        self.selection_frame = ctk.CTkFrame(self.right_frame, fg_color=BG_COLOR)
        self.selection_frame.pack(side="right", fill="y", padx=10, pady=10)

    def create_console_frame(self):
        self.console_frame = ctk.CTkFrame(self.left_frame, fg_color=BG_COLOR)
        self.console_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="nswe")
        self.console_text = Text(self.console_frame, bg=BG_COLOR, fg=FG_COLOR, wrap="word", state="disabled")
        self.console_text.pack(padx=10, pady=10, fill="both", expand=True)

    def create_file_selection_elements(self):
        self.label_file_path = ctk.CTkLabel(
            self.left_frame, text="Select Input File:", fg_color=BG_COLOR, text_color=FG_COLOR
        )
        self.label_file_path.grid(row=0, column=0, padx=5, pady=5)
        self.entry_file_path = ctk.CTkEntry(self.left_frame, width=300, fg_color=BUTTON_COLOR, text_color=FG_COLOR)
        self.entry_file_path.grid(row=0, column=1, padx=5, pady=5)
        self.button_browse = ctk.CTkButton(
            self.left_frame, text="Browse", command=self.browse_file, fg_color=BUTTON_COLOR, text_color=FG_COLOR
        )
        self.button_browse.grid(row=0, column=2, padx=5, pady=5)

    def create_run_button(self):
        self.button_run = ctk.CTkButton(
            self.left_frame,
            text="Run Script",
            command=self.run_script_threaded,
            fg_color=BUTTON_COLOR,
            text_color=FG_COLOR,
        )
        self.button_run.grid(row=1, column=0, columnspan=3, pady=10)

    def create_loading_label(self):
        self.loading_label = ctk.CTkLabel(self.left_frame, text="", fg_color=BG_COLOR, text_color=FG_COLOR)
        self.loading_label.grid(row=2, column=0, columnspan=3, pady=5)

    def _add_top_image(self):
        top_image = ctk.CTkImage(dark_image=Image.open(IMAGE_PATH), size=(1654 // 4, 578 // 4))
        image_label = ctk.CTkLabel(self, image=top_image, text="")
        image_label.pack(pady=10)

    def browse_file(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            self.entry_file_path.delete(0, ctk.END)
            self.entry_file_path.insert(0, filepath)

    def save_data_to_excel(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            try:
                if self.var_EI.get():
                    export_data(folder_path, "Impact_total", EI)
                if self.var_EI_manu.get():
                    export_data(folder_path, "Impact_manu", EI_manu)
                if self.var_EI_use.get():
                    export_data(folder_path, "Impact_use", EI_use)
                if self.var_fault_cause.get():
                    export_data(folder_path, "fault_cause", fault_cause)
                if self.var_RU_age.get():
                    export_data(folder_path, "RU_age", RU_age)
                print(f"Selected data saved successfully in {folder_path}")
            except Exception as e:
                print(f"An error occurred while saving the data: {e}")

    def display_plot(self, index):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
        fig = self.figs[index]
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side="top", fill="both", expand=1)

    def show_next_plot(self):
        self.current_index = (self.current_index + 1) % len(self.figs)
        self.display_plot(self.current_index)

    def show_prev_plot(self):
        self.current_index = (self.current_index - 1) % len(self.figs)
        self.display_plot(self.current_index)

    def save_plot(self):
        if self.figs:
            folder_path = filedialog.askdirectory()
            if folder_path:
                try:
                    for idx, fig in enumerate(self.figs):
                        filepath = os.path.join(folder_path, f"plot_{idx+1}.svg")
                        fig.savefig(filepath, dpi=300)
                    print(f"All plots saved successfully in {folder_path}")
                except Exception as e:
                    print(f"An error occurred while saving the plots: {e}")

    def save_selected_plot(self):
        if self.figs and self.current_index is not None:
            folder_path = filedialog.askdirectory()
            if folder_path:
                try:
                    fig = self.figs[self.current_index]
                    filepath = os.path.join(folder_path, f"selected_plot_{self.current_index + 1}.svg")
                    fig.savefig(filepath, dpi=300)
                    print(f"Selected plot saved successfully as {filepath}")
                except Exception as e:
                    print(f"An error occurred while saving the selected plot: {e}")
        else:
            print("No plots available to save.")

    def update_ui(self, simulation_type):
        self.prev_button.configure(state="normal")
        self.next_button.configure(state="normal")
        self.save_button.configure(state="normal")
        self.save_selected_button.configure(state="normal")
        if simulation_type == "Analysis":
            self.save_data_button.configure(state="normal")
            self.checkbox_EI.configure(state="normal")
            self.checkbox_EI_manu.configure(state="normal")
            self.checkbox_EI_use.configure(state="normal")
            self.checkbox_fault_cause.configure(state="normal")
            self.checkbox_RU_age.configure(state="normal")

    def reset_interface(self):
        def do_reset():
            for widget in self.plot_frame.winfo_children():
                widget.destroy()
            for widget in self.selection_frame.winfo_children():
                widget.destroy()
            self.prev_button.configure(state="disabled")
            self.next_button.configure(state="disabled")
            self.save_button.configure(state="disabled")
            self.save_selected_button.configure(state="disabled")
            self.save_data_button.configure(state="disabled")
            self.var_EI.set("")
            self.var_EI_manu.set("")
            self.var_EI_use.set("")
            self.var_fault_cause.set("")
            self.var_RU_age.set("")
            self.checkbox_EI.configure(state="disabled")
            self.checkbox_EI_manu.configure(state="disabled")
            self.checkbox_EI_use.configure(state="disabled")
            self.checkbox_fault_cause.configure(state="disabled")
            self.checkbox_RU_age.configure(state="disabled")

        self.after(100, do_reset)

    def run_script(self):
        plt.close("all")
        self.button_run.configure(state="disabled")
        full_path_input = self.entry_file_path.get()
        if not full_path_input:
            messagebox.showerror("Error", "Please select an input file")
            return
        path_input = os.path.dirname(full_path_input)
        name_input = os.path.basename(full_path_input)
        self.loading_label.configure(text="Running script...")
        self.update_idletasks()

        try:
            dic = dictionary._init_dic(path_input, name_input)
            if dic["LCA"] == "yes":
                LCA.EI_calculation(dic, path_input, name_input)
            if dic["simulation"] == "Analysis":
                self.run_analysis(dic, path_input, name_input)
            elif dic["simulation"] == "Monte Carlo":
                self.run_monte_carlo(dic)
            self.finish_script_execution("Script executed successfully", dic["simulation"])
        except InvalidExchange:
            self.finish_script_execution("An error occurred: Exchange is missing ‘amount’ or ‘input’")
        except BaseException as e:
            self.finish_script_execution(f"An error occurred: {str(e)}")

    def run_analysis(self, dic, path_input, name_input):
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
        self.figs = [
            plot_instance.fig1,
            plot_instance.fig2,
            plot_instance.fig3,
            plot_instance.fig4,
            plot_instance.fig5,
            plot_instance.fig6,
        ]
        self.setup_plot_frame()

    def run_monte_carlo(self, dic):
        plot_instance = plotting.PLOT_MC(dic)
        self.figs = [plot_instance.fig1, plot_instance.fig2]
        self.setup_plot_frame()

    def setup_plot_frame(self):
        max_width, max_height = get_max_fig_size(self.figs)
        self.plot_frame.configure(width=max_width, height=max_height)
        self.plot_frame.pack_propagate(True)
        self.current_index = 0
        self.create_figure_buttons()
        self.display_plot(self.current_index)

    def finish_script_execution(self, message, simulation_type=None):
        self.button_run.configure(state="normal")
        self.loading_label.configure(text=message)
        if simulation_type:
            self.update_ui(simulation_type)

    def update_and_display_plot(self, index):
        self.current_index = index
        self.display_plot(index=index)

    def create_figure_buttons(self):
        for widget in self.selection_frame.winfo_children():
            widget.destroy()
        for idx, fig in enumerate(self.figs):
            thumb_image = create_thumbnail(fig)
            button = ctk.CTkButton(
                self.selection_frame,
                image=thumb_image,
                command=lambda i=idx: self.update_and_display_plot(i),
                fg_color=BUTTON_COLOR,
                text_color=FG_COLOR,
                width=120,
                height=60,
                text="",
            )
            button.image = thumb_image
            button.pack(fill="x", padx=5, pady=5)

    def run_script_threaded(self):
        import threading

        if self.is_running:
            self.reset_interface()
        threading.Thread(target=self.run_script).start()
        self.is_running = True
