import os

from bw2data.errors import InvalidExchange
from PySide6.QtCore import QThread, Signal

from app.utils import LCA, dictionary, plotting, staircase


class ProcessExcel(QThread):
    """Worker thread for executing the script."""

    finished = Signal()
    error = Signal(str)
    figs = Signal(object)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

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

        figs = [
            plot_instance.fig1,
            plot_instance.fig2,
            plot_instance.fig3,
            plot_instance.fig4,
            plot_instance.fig5,
            plot_instance.fig6,
        ]
        self.figs.emit(figs)
        print("Analysis completed.")

    def run_monte_carlo(self, dic):
        """Run Monte Carlo simulations."""
        try:
            print("Running Monte Carlo simulation...")
            plot_instance = plotting.PLOT_MC(dic)
            figs = [plot_instance.fig1, plot_instance.fig2]
            self.figs.emit(figs)
            self.finished.emit()
        except Exception as e:
            self.error.emit(f"An error occurred in Monte Carlo simulation: {str(e)}")

    def run(self):
        try:
            full_path_input = self.file_path
            # Replace with actual dictionary initialization and script execution
            path_input = os.path.dirname(full_path_input)
            name_input = os.path.basename(full_path_input)
            dic = dictionary._init_dic(path_input, name_input)

            if "LCA" in dic and dic["LCA"] == "yes":
                LCA.EI_calculation(dic, path_input, name_input)
            if "simulation" in dic:
                if dic["simulation"] == "Analysis":
                    self.run_analysis(dic, path_input, name_input)
                elif dic["simulation"] == "Monte Carlo":
                    self.run_monte_carlo(dic)
        except InvalidExchange:
            self.error.emit("An error occurred: Exchange is missing ‘amount’ or ‘input’")
        except KeyError as ke:
            self.error.emit(f"KeyError: Missing key in dictionary: {str(ke)}")
        except Exception as e:
            self.error.emit(f"An error occurred: {str(e)}")
