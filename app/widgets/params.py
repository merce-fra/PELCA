import configparser

from PySide6.QtWidgets import (QApplication, QCheckBox, QDoubleSpinBox,
                               QFormLayout, QLabel, QLineEdit, QPushButton,
                               QSpinBox, QVBoxLayout, QWidget)


class FormWidget(QWidget):
    def __init__(self, config_file):
        # Create form fields for additional parameters

        super().__init__()

        print(config_file)

        self.setWindowTitle("Form Widget")

        # Create a form layout
        form_layout = QFormLayout()

        self.staircase_result_filename = QLineEdit("Example_staircase.xlsx")
        self.staircase_result_filename.setReadOnly(True)
        self.num_replac_unit = QSpinBox()
        self.num_replac_unit.setRange(0, 1000000)
        self.num_replac_unit.setValue(0)
        self.service_life = QSpinBox()
        self.service_life.setRange(0, 1000000)
        self.service_life.setValue(0)
        self.annual_usage_time = QDoubleSpinBox()
        self.annual_usage_time.setRange(0.0, 1000000.0)
        self.annual_usage_time.setValue(0.0)
        self.time_step = QSpinBox()
        self.time_step.setRange(0, 1000000)
        self.time_step.setValue(0)
        self.early_failure = QCheckBox()
        self.early_failure.setChecked(False)
        self.random_failure = QCheckBox()
        self.random_failure.setChecked(False)
        self.wearout_failure = QCheckBox()
        self.wearout_failure.setChecked(False)
        self.maintenance = QCheckBox()
        self.maintenance.setChecked(False)
        self.cost_price = QCheckBox()
        self.cost_price.setChecked(True)
        self.monte_carlo_iterations = QSpinBox()
        self.monte_carlo_iterations.setRange(0, 1000000)
        self.monte_carlo_iterations.setValue(0)
        self.plot_specific_env_impact = QSpinBox()
        self.plot_specific_env_impact.setRange(0, 1000000)
        self.plot_specific_env_impact.setValue(0)


        # Add additional form fields to the layout
        form_layout.addRow("Staircase result filename:", self.staircase_result_filename)
        form_layout.addRow("Number of Replac. Unit (RU):", self.num_replac_unit)
        form_layout.addRow("Service life (year):", self.service_life)
        form_layout.addRow("Annual usage time (hours/year):", self.annual_usage_time)
        form_layout.addRow("Time step (step/year):", self.time_step)
        form_layout.addRow("Early failure:", self.early_failure)
        form_layout.addRow("Random failure:", self.random_failure)
        form_layout.addRow("Wearout failure:", self.wearout_failure)
        form_layout.addRow("Maintenance:", self.maintenance)
        form_layout.addRow("Cost / Price:", self.cost_price)
        form_layout.addRow("Monte Carlo (number of iteration):", self.monte_carlo_iterations)
        form_layout.addRow("Plot specific env. impact:", self.plot_specific_env_impact)

        self.load_config(config_file)

        # Create a main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)


        self.setLayout(main_layout)

    def load_config(self, config_file):
        config = configparser.ConfigParser()
        config.optionxform = str  # Preserve case sensitivity of keys

        # Parse the config file
        with open(config_file, "r") as f:
            for line in f:
                if "," in line:
                    key, value = line.strip().split(",", 1)
                    self.set_field(key.strip(), value.strip())

    def set_field(self, key, value):
        if key == "filename_result_staircase":
            self.staircase_result_filename.setText(value)
        elif key == "num_replac_unit":
            self.num_replac_unit.setValue(int(value))
        elif key == "service_life":
            self.service_life.setValue(int(value))
        elif key == "num_hourPerYear":
            print("Setting annual usage time")

            self.annual_usage_time.setValue(float(value))
        elif key == "step":
            self.time_step.setValue(int(value))
        elif key == "Early_failure":
            self.early_failure.setChecked(value == "True")
        elif key == "Random_failure":
            self.random_failure.setChecked(value == "True")
        elif key == "Wearout_failure":
            self.wearout_failure.setChecked(value == "True")
        elif key == "Maintenance":
            self.maintenance.setChecked(value == "True")
        elif key == "Cost":
            self.cost_price.setChecked(value == "True")
        elif key == "nb_ite_MC":
            self.monte_carlo_iterations.setValue(int(value))
        elif key == "selected_EI":
            self.plot_specific_env_impact.setValue(int(value))
        else:
            print(f"Unknown key: {key}")
