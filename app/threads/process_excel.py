import os

from bw2data.errors import InvalidExchange
from PySide6.QtCore import QThread, Signal

from app.utils import LCA, dictionary, plotting, staircase, plotting_MC


class ProcessExcel(QThread):
    """Worker thread for executing the script."""

    finished = Signal()
    error = Signal(str)
    figs = Signal(dict)
    data_dict = Signal(dict)

    def __init__(self, file_path, lca=False):
        super().__init__()
        self.file_path = file_path
        self.lca = lca

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
            cost_total_manufacturing,
            cost_total_use,
            cost_total_maintenance,
            cost_total,
        ) = staircase_instance.get_variables(dic)

        impact_eco = {
            "Manufacturing": cost_total_manufacturing,
            "Use": cost_total_use,
            "Maintenance": cost_total_maintenance,
            "Total": cost_total,
        }
        
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
            impact_eco,
        )
        figs = {
            "plots": plot_instance.figs,
            "plot_data": {
                "EI": EI,
                "EI_manu": EI_manu,
                "EI_use": EI_use,
                "usage_time": usage_time,
                "number_of_fault": number_of_fault,
                "wcdf": wcdf,
                "fault_cause": fault_cause,
                "RU_age": RU_age,
                "EI_maintenance": EI_maintenance,
                "impact_eco": impact_eco,
                "dic": dic,
            },
        }
        self.figs.emit(figs)
        print("Analysis completed.")

    def run_monte_carlo(self, dic):
        """Run Monte Carlo simulations."""
        try:
            print("Running Monte Carlo simulation...")
            plot_instance = plotting_MC.PLOT_MC(dic)
            figs = {"plot_data": {
                "dic": dic,
            }, "plots": plot_instance.figs}
            self.figs.emit(figs)
            self.finished.emit()
        except Exception as e:
            self.error.emit(f"An error occurred in Monte Carlo simulation: {str(e)}")

    def run(self):
        dic = {
            "path_result_EI": "",
            "filename_result_EI": "",   
            "filename_result_EI_MC": "",
            "simulation": "",
            "directory": "",
            "LCA_path": "",
            "EI_name": [],
            "LCIA_unit": [],
            "proj_name": "",
            "database_ecoinvent": "",
        }
        try:
            full_path_input = self.file_path
            print(f"Processing file: {full_path_input}")
            # Replace with actual dictionary initialization and script execution
            path_input = os.path.dirname(full_path_input)
            name_input = os.path.basename(full_path_input)
            dic = dictionary._init_dic(path_input, name_input, self.lca)
            self.data_dict.emit(dic)
            if self.lca:
                LCA.EI_calculation(dic, path_input, name_input)
            if "simulation" in dic:
                if dic["simulation"] == "Analysis":
                    self.run_analysis(dic, path_input, name_input)
                elif dic["simulation"] == "Monte Carlo":
                    self.run_monte_carlo(dic)
        except FileNotFoundError:
            self.error.emit(f"An error occurred: the LCA result {dic['filename_result_EI'] if dic and dic['simulation'] == 'Analysis' else dic['filename_result_EI_MC']} was not found in the LCA result path {os.path.join(dic['path_result_EI'],dic['directory']) if dic else 'unknown path'}")
        except InvalidExchange:
            self.error.emit("An error occurred: Exchange is missing ‘amount’ or ‘input’.")
        except KeyError as ke:
            self.error.emit(f"KeyError: Missing key in dictionary: {str(ke)}.")
        except Exception as e:
            self.error.emit(f"An error occurred: {str(e)}")
