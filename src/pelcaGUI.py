import customtkinter as ctk
import os
from PIL import Image
from tkinter import Text  # Import Text from tkinter if you haven't already

# Define colors for the dark theme
BG_COLOR = "#2E2E2E"
FG_COLOR = "#FFFFFF"
BUTTON_COLOR = "#4E4E4E"
SEPARATOR_COLOR = "#242424"

# Set appearance mode to dark
ctk.set_appearance_mode("dark")

# Constants for icon and image paths
DEFAULT_ICON_PATH = os.path.join('assets', 'icon.ico')
ICON_ENV_VAR = 'ICON_PATH'
IMAGE_PATH = os.getenv('IMAGE_PATH', os.path.join('assets', 'first_image.png'))


class PelcaGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window settings
        self.title("PELCA")
        self.set_window_icon()
        self.configure(bg=BG_COLOR)

        self.add_top_image()

        # Create main frame
        self.main_frame = self.create_main_frame()

        # Add top image

        # Initialize variables
        self.initialize_variables()

        # Create UI elements
        self.create_navigation_buttons()

        self.label_file_path = ctk.CTkLabel(self.left_frame, text="Select Input File:", fg_color=BG_COLOR, text_color=FG_COLOR)
        self.label_file_path.grid(row=0, column=0, padx=5, pady=5)

        self.entry_file_path = ctk.CTkEntry(self.left_frame, width=300, fg_color=BUTTON_COLOR, text_color=FG_COLOR)
        self.entry_file_path.grid(row=0, column=1, padx=5, pady=5)

        self.button_browse = ctk.CTkButton(self.left_frame, text="Browse", command=self.browse_file, fg_color=BUTTON_COLOR, text_color=FG_COLOR)
        self.button_browse.grid(row=0, column=2, padx=5, pady=5)

        self.button_run = ctk.CTkButton(self.left_frame, text="Run Script", command=self.run_script_threaded, fg_color=BUTTON_COLOR, text_color=FG_COLOR)
        self.button_run.grid(row=1, column=0, columnspan=3, pady=10)

        self.loading_label = ctk.CTkLabel(self.left_frame, text="", fg_color=BG_COLOR, text_color=FG_COLOR)
        self.loading_label.grid(row=2, column=0, columnspan=3, pady=5)

        self.create_console_frame()
       

    def create_console_frame(self):
        self.console_frame = ctk.CTkFrame(self.left_frame, fg_color=BG_COLOR)
        self.console_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky='nswe')

        self.console_text = Text(self.console_frame, bg=BG_COLOR, fg=FG_COLOR, wrap='word', state='disabled')
        self.console_text.pack(padx=10, pady=10, fill='both', expand=True)


    def set_window_icon(self):
        """Set window icon from environment variable or default location."""
        icon_path = os.getenv(ICON_ENV_VAR, DEFAULT_ICON_PATH)
        self.after(201, lambda: self.iconbitmap(icon_path))

    def create_main_frame(self):
        """Create and return the main frame."""
        main_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        main_frame.pack(padx=10, pady=10, fill='both', expand=True)

        # Create and store the left frame
        self.left_frame = self.create_left_frame(main_frame)

        # Create and store the right frame
        self.right_frame = self.create_right_frame(main_frame)

        # Create the separator frame
        self.create_separator_frame(main_frame)

        return main_frame

    def create_left_frame(self, parent):
        """Create and return the left frame."""
        left_frame = ctk.CTkFrame(parent, fg_color=BG_COLOR)
        left_frame.pack(side='left', padx=10, pady=10, fill='y')
        return left_frame

    def create_right_frame(self, parent):
        """Create and return the right frame."""
        right_frame = ctk.CTkFrame(parent, fg_color=BG_COLOR)
        right_frame.pack(side='right', fill='both', expand=True)

        # Create and store the data frame
        self.data_frame = self.create_data_frame(right_frame)

        return right_frame

    def create_data_frame(self, parent):
        """Create and return the data frame in the right frame."""
        data_frame = ctk.CTkFrame(parent, fg_color=BG_COLOR)
        data_frame.pack(side='bottom', fill='x', padx=10, pady=10)

        # Add checkboxes
        self.add_checkboxes(data_frame)

        # Create Save Data button
        self.create_save_data_button(data_frame)

        return data_frame

    def create_separator_frame(self, parent):
        """Create and return the separator frame."""
        separator_frame = ctk.CTkFrame(parent, width=8, fg_color=SEPARATOR_COLOR)
        separator_frame.pack(side='left', fill='y')
        return separator_frame

    def add_checkboxes(self, parent):
        """Add checkboxes to the data frame."""
        self.var_EI = ctk.StringVar()
        self.var_EI_manu = ctk.StringVar()
        self.var_EI_use = ctk.StringVar()
        self.var_fault_cause = ctk.StringVar()
        self.var_RU_age = ctk.StringVar()

        checkbox_EI = ctk.CTkCheckBox(parent, text="Impact total", variable=self.var_EI, onvalue='EI', offvalue='', state="disabled")
        checkbox_EI.pack(side='left', padx=5)

        checkbox_EI_manu = ctk.CTkCheckBox(parent, text="Impact manufact.", variable=self.var_EI_manu, onvalue='EI_manu', offvalue='', state="disabled")
        checkbox_EI_manu.pack(side='left', padx=5)

        checkbox_EI_use = ctk.CTkCheckBox(parent, text="Impact use", variable=self.var_EI_use, onvalue='EI_use', offvalue='', state="disabled")
        checkbox_EI_use.pack(side='left', padx=5)

        checkbox_fault_cause = ctk.CTkCheckBox(parent, text="Fault cause", variable=self.var_fault_cause, onvalue='fault_cause', offvalue='', state="disabled")
        checkbox_fault_cause.pack(side='left', padx=5)

        checkbox_RU_age = ctk.CTkCheckBox(parent, text="RU age", variable=self.var_RU_age, onvalue='RU_age', offvalue='', state="disabled")
        checkbox_RU_age.pack(side='left', padx=5)

    def create_save_data_button(self, parent):
        """Create a save data button."""
        save_data_button = ctk.CTkButton(parent, text="Save Data", command=self.save_data_to_excel, fg_color=BUTTON_COLOR, text_color=FG_COLOR, state="disabled")
        save_data_button.pack(side='left', padx=10)

    def create_navigation_buttons(self):
        """Create navigation buttons frame."""
        nav_buttons_frame = ctk.CTkFrame(self.right_frame, fg_color=BG_COLOR)
        nav_buttons_frame.pack(side='top', fill='x', padx=10, pady=10)

        # Create navigation buttons
        self.prev_button = ctk.CTkButton(nav_buttons_frame, text="Previous", command=self.show_prev_plot, fg_color=BUTTON_COLOR, text_color=FG_COLOR, state="disabled")
        self.next_button = ctk.CTkButton(nav_buttons_frame, text="Next", command=self.show_next_plot, fg_color=BUTTON_COLOR, text_color=FG_COLOR, state="disabled")
        self.save_button = ctk.CTkButton(nav_buttons_frame, text="Save All", command=self.save_plot, fg_color=BUTTON_COLOR, text_color=FG_COLOR, state="disabled")
        self.save_selected_button = ctk.CTkButton(nav_buttons_frame, text="Save", command=self.save_selected_plot, fg_color=BUTTON_COLOR, text_color=FG_COLOR, state="disabled")

        self.prev_button.pack(side='left', padx=5, pady=5)
        self.next_button.pack(side='left', padx=5, pady=5)
        self.save_selected_button.pack(side='left', padx=5, pady=5)
        self.save_button.pack(side='top', fill='x', padx=5, pady=10)

        nav_buttons_frame.grid_columnconfigure(0, weight=1)
        nav_buttons_frame.grid_columnconfigure(1, weight=1)
        nav_buttons_frame.grid_columnconfigure(2, weight=1)

        # Create plot frame and selection frame
        self.create_plot_and_selection_frames()

    def create_plot_and_selection_frames(self):
        """Create plot and selection frames in the right frame."""
        plot_frame = ctk.CTkFrame(self.right_frame, fg_color=BG_COLOR)
        plot_frame.pack(side='left', padx=10, pady=10, expand=True)
        plot_frame.pack_propagate(False)

        selection_frame = ctk.CTkFrame(self.right_frame, fg_color=BG_COLOR)
        selection_frame.pack(side='right', fill='y', padx=10, pady=10)

        # Create spacers
        self.create_spacers()

    def create_spacers(self):
        """Create spacers in the right frame."""
        top_spacer = ctk.CTkFrame(self.right_frame, fg_color=BG_COLOR)
        top_spacer.pack(side='top', fill='both', expand=True)

        bottom_spacer = ctk.CTkFrame(self.right_frame, fg_color=BG_COLOR)
        bottom_spacer.pack(side='bottom', fill='both', expand=True)

    def add_top_image(self):
        """Add the top image to the GUI."""
        top_image = ctk.CTkImage(dark_image=Image.open(IMAGE_PATH), size=(1654 // 4, 578 // 4))
        image_label = ctk.CTkLabel(self, image=top_image, text='')
        image_label.pack(pady=10)

    def initialize_variables(self):
        """Initialize string variables."""
        self.var_EI = ctk.StringVar()
        self.var_EI_manu = ctk.StringVar()
        self.var_EI_use = ctk.StringVar()
        self.var_fault_cause = ctk.StringVar()
        self.var_RU_age = ctk.StringVar()

    def save_data_to_excel(self):
        """Placeholder for save data to Excel functionality."""
        print("Data saved to Excel")

    def show_prev_plot(self):
        """Placeholder for showing previous plot functionality."""
        print("Showing previous plot")

    def show_next_plot(self):
        """Placeholder for showing next plot functionality."""
        print("Showing next plot")

    def save_plot(self):
        """Placeholder for saving all plots functionality."""
        print("All plots saved")

    def save_selected_plot(self):
        """Placeholder for saving selected plot functionality."""
        print("Selected plot saved")

    def browse_file(self):
        """Placeholder for file browsing functionality."""
        print("Browse for file")

    def run_script_threaded(self):
        """Placeholder for running script in a threaded way."""
        print("Script running in thread")


