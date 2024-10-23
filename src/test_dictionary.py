import os
import shutil
import unittest

import pandas as pd

from dictionary import _init_dic, _init_dir


class TestDictionaryFunctions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a temporary directory for testing
        cls.test_dir = "test_dir"
        os.mkdir(cls.test_dir)

        # Create a sample Excel file for testing
        cls.excel_path = os.path.join(cls.test_dir, "test_data.xlsx")
        with pd.ExcelWriter(cls.excel_path) as writer:
            pd.DataFrame(
                {
                    "A": [
                        "LCA result path",
                        "LCA result filename",
                        "LCA Monte Carlo result filename",
                        "Type of simulation (Analysis\\Monte Carlo)",
                        "Database ecoinvent",
                        "Ecoinvent path",
                        "Inventory name",
                        "Project name (brightway)",
                        "Number of iterations (Monte Carlo)",
                    ],
                    "B": [
                        "test_path",
                        "result.csv",
                        "result_mc.csv",
                        "Analysis",
                        "ecoinvent",
                        "ecoinvent_path",
                        "inventory",
                        "project",
                        1000,
                    ],
                }
            ).to_excel(writer, sheet_name="LCA", index=False, header=False)
            pd.DataFrame({"Acronym": ["GWP", "ODP"], "Unit": ["kg CO2 eq", "kg CFC-11 eq"]}).to_excel(
                writer, sheet_name="LCIA", index=False
            )
            pd.DataFrame(
                {
                    "A": [
                        "Service life (year)",
                        "Annual usage time (hours/year)",
                        "Time step (step/year)",
                        "Staircase result filename",
                        "Monte Carlo (number of iteration)",
                        "Early failure",
                        "Random failure",
                        "Wearout failure",
                        "Maintenance",
                        "Plot specific env. impact",
                    ],
                    "B": [10, 8760, 1, "staircase.csv", 100, 0.01, 0.02, 0.03, 0.04, 1],
                }
            ).to_excel(writer, sheet_name="Staircase", index=False, header=False)
            pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]}).to_excel(
                writer, sheet_name="Replac. Matrix", index=False, header=False
            )

    @classmethod
    def tearDownClass(cls):
        # Remove the temporary directory and files after tests
        shutil.rmtree(cls.test_dir)

    def test_init_dic(self):
        dic = _init_dic(self.test_dir, "test_data.xlsx")
        self.assertEqual(dic["path_result_EI"], "test_path")
        self.assertEqual(dic["filename_result_EI"], "result.csv")
        self.assertEqual(dic["filename_result_EI_MC"], "result_mc.csv")
        self.assertEqual(dic["simulation"], "Analysis")
        self.assertEqual(dic["database_ecoinvent"], "ecoinvent")
        self.assertEqual(dic["database_ecoinvent_path"], "ecoinvent_path")
        self.assertEqual(dic["inventory_name"], "inventory")
        self.assertEqual(dic["proj_name"], "project")
        self.assertEqual(dic["iterations"], 1000)
        self.assertEqual(dic["EI_name"], ["GWP", "ODP"])
        self.assertEqual(dic["LCIA_unit"], ["kg CO2 eq", "kg CFC-11 eq"])
        self.assertEqual(dic["service_life"], 10)
        self.assertEqual(dic["num_hourPerYear"], 8760)
        self.assertEqual(dic["step"], 1)
        self.assertEqual(dic["filename_result_staircase"], "staircase.csv")
        self.assertEqual(dic["nb_ite_MC"], 100)
        self.assertEqual(dic["Early_failure"], 0.01)
        self.assertEqual(dic["Random_failure"], 0.02)
        self.assertEqual(dic["Wearout_failure"], 0.03)
        self.assertEqual(dic["Maintenance"], 0.04)
        self.assertEqual(dic["selected_EI"], 0)

    def test_init_dir(self):
        test_path = os.path.join(self.test_dir, "new_dir")
        _init_dir(test_path, "new_dir")
        self.assertTrue(os.path.exists(test_path))
        shutil.rmtree(test_path)
