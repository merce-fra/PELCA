from PySide6.QtWidgets import QApplication, QWidget, QFormLayout, QLineEdit, QPushButton, QVBoxLayout
from PySide6.QtWidgets import QLabel, QCheckBox, QSpinBox, QDoubleSpinBox

class FormWidget(QWidget):
    def __init__(self):
        # Create form fields for additional parameters
       
        super().__init__()

        self.setWindowTitle("Form Widget")

        # Create a form layout
        form_layout = QFormLayout()

        self.staircase_result_filename = QLineEdit("Example_staircase.xlsx")
        self.num_replac_unit = QSpinBox()
        self.num_replac_unit.setValue(2)
        self.service_life = QSpinBox()
        self.service_life.setValue(30)
        self.annual_usage_time = QDoubleSpinBox()
        self.annual_usage_time.setValue(666)
        self.time_step = QSpinBox()
        self.time_step.setValue(1)
        self.early_failure = QCheckBox()
        self.early_failure.setChecked(True)
        self.random_failure = QCheckBox()
        self.random_failure.setChecked(False)
        self.wearout_failure = QCheckBox()
        self.wearout_failure.setChecked(True)
        self.maintenance = QCheckBox()
        self.maintenance.setChecked(True)
        self.cost_price = QCheckBox()
        self.cost_price.setChecked(True)
        self.monte_carlo_iterations = QSpinBox()
        self.monte_carlo_iterations.setValue(1000)
        self.plot_specific_env_impact = QSpinBox()
        self.plot_specific_env_impact.setValue(14)

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

        # Create a main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)

        self.setLayout(main_layout)

    
if __name__ == "__main__":
    app = QApplication([])

    widget = FormWidget()
    widget.show()

    app.exec()




