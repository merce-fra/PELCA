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
import random
import sys

import numpy as np
import pandas as pd
from scipy.stats import weibull_min

# Definition of Weibull Cumulative Density Function (WCDF)
def _wcdf(self, step, dic, nb_RU, weibull_Efault, weibull_Rfault, weibull_Wfault):
    # Initialisation of matrices 
    weibull_E = np.array([[0 for i in range(nb_RU)] for z in range(dic["nb_ite_MC"])], dtype="float")
    weibull_R = np.array([[0 for i in range(nb_RU)] for z in range(dic["nb_ite_MC"])], dtype="float")
    weibull_W = np.array([[0 for i in range(nb_RU)] for z in range(dic["nb_ite_MC"])], dtype="float")

    # Edit(AEP): The variable step is an index referencing the time step in the list of time steps.
    # The value of RU_age is in years (can be a fraction of years, e.g., 3.4years)
    # Variable indices contains indices expressed in time steps. Therefore, the values contained in RU_age need to be converted to their corresponding time steps.
    # This is done by multiplying RU_age with dic["step"] and converting it into an array of integers with .astype(np.int_) method
    indices = np.round(self.RU_age[step - 1, :, :] *dic["step"]).astype(np.int_)

    if dic["Early_failure"] == "True":
        weibull_E = weibull_Efault[indices, np.arange(nb_RU)]
    if dic["Random_failure"] == "True":
        weibull_R = weibull_Rfault[indices, np.arange(nb_RU)]

    if dic["Wearout_failure"] == "True":
        # weibull_W=weibull_Wfault[self.RU_age[step-1,:,:]][:,0,:]
        # weibull_W=1-np.prod(1 - weibull_Wfault[self.RU_age[step-1]][:,0,:], axis=1)
        weibull_W = weibull_Wfault[indices, np.arange(nb_RU)]  # shape: (1000, 2)

    wcdf = 1 - (1 - weibull_E) * (1 - weibull_R) * (1 - weibull_W)

    return wcdf


class STAIRCASE:
    # %%
    def __init__(self, path_input, name_input, dic):
        self.usage_time = dic["service_life"] * dic["step"]  # Edit(AEP): Total number of time steps (in time steps)
        epsilon = 1e-10  # allow to avoid to divide by 0 during .../wcdf_sum

        # Edit(AEP): list of times (in years), can contain fractions of years (e.g., 7.3 years), the number of elements is the total number of time steps
        self.t = np.linspace(epsilon, dic["service_life"], self.usage_time)
        
        excel = pd.ExcelFile(os.path.join(path_input, name_input))
        data = pd.read_excel(excel, sheet_name="Faults & Prev. Maint.", skiprows=[0, 1, 2], usecols="B:H")

        # Extract the 6th column into a variable named 'maintenance'.
        # Edit(AEP): This contains the preventive maintenance plan for each RU (in years)
        dic["maintenance"] = data.iloc[:, 6].to_numpy()
    
        data_cost = pd.read_excel(excel, sheet_name='Cost - Price', skiprows=4, usecols="B:E")
        dic["RU_raw_cost"] = data_cost.iloc[:, 0].to_numpy()
        dic["RU_ass_cost"] = data_cost.iloc[:, 1].to_numpy()
        dic["RU_des_cost"] = data_cost.iloc[:, 2].to_numpy()
        dic["RU_kWh_cost"] = data_cost.iloc[:, 3].to_numpy()

        # ---- Recovery of the Energy of units per hour for modeling of the economic cost ----
        # Read the full Excel sheet without headers (since it's a custom format with blocks)
        df = pd.read_excel(excel, sheet_name='Inventory - Use', header=None)
        # Initialize the final dictionary and a list to store extracted energy amounts
        list_energy_amount = {}
        energy_amount = []

        i = 0
        while i < len(df):
            try:
                # Detect the start of an activity block
                if str(df.iloc[i, 0]).strip().lower() == "activity":
                    # Get the activity name (from column B)
                    name = str(df.iloc[i, 1]).strip()
                    if not name:
                        print(f"Warning: Activity name missing at row {i + 1}. Skipping.")
                        i += 1
                        continue
                    i += 1

                    # Skip rows until we reach the "Exchanges" label
                    found_exchanges = False
                    while i < len(df):
                        if str(df.iloc[i, 0]).strip().lower() == "exchanges":
                            found_exchanges = True
                            break
                        i += 1

                    if not found_exchanges:
                        print(f"Error: 'Exchanges' section not found for activity '{name}'. Skipping.")
                        continue

                    # Capture the exchange table headers
                    if i + 1 >= len(df):
                        print(f"Error: Missing headers after 'Exchanges' for activity '{name}'. Skipping.")
                        continue
                    headers = df.iloc[i + 1]
                    i += 2

                    # Read each exchange row (until we hit a blank or next block)
                    while i < len(df) and pd.notna(df.iloc[i, 0]):
                        row = dict(zip(headers, df.iloc[i]))

                        if str(row.get("type", "")).lower() == "technosphere":
                            val = str(row.get("amount", "")).replace(",", ".")
                            try:
                                float_val = float(val)
                                list_energy_amount[name] = float_val
                                energy_amount.append(float_val)
                            except ValueError:
                                print(
                                    f"Warning: Invalid numeric amount '{val}' for activity '{name}' at row {i + 1}. Skipping value.")
                            break  # Only keep the first matching exchange
                        i += 1
                else:
                    i += 1
            except Exception as e:
                print(f"Unexpected error at row {i + 1}: {e}. Skipping row.")
                i += 1

        # Display
        print("\nConsumption of units per hour")
        for k, v in list_energy_amount.items():
            print(f"{k} - {v} kWh")
        print("\n")
        # -----------------------------------------------------------------------------------

        self.cost_manufacturing_total = dic["RU_raw_cost"].sum(axis=0)

        # Drop the 6th column (index 5) from the DataFrame and convert it to a NumPy array for 'beta_sigma_ERW'
        # rows: RU1; RU2 etc
        # columns: sigma_E, beta_E, sigma_R, beta_R, sigma_W, beta_W
        beta_sigma_ERW = data.drop(data.columns[6], axis=1).to_numpy()
        excel.close()

        excel = pd.ExcelFile(os.path.join(dic["LCA_path"], dic["filename_result_EI"]))

        print("Reading the Excel file...")
        print(os.path.join(dic["LCA_path"], dic["filename_result_EI"]))

      
        # EI manufacturing of each RU
        df_manufacturing = pd.read_excel(excel, sheet_name="Manufacturing", index_col=0)
        df_manufacturing = df_manufacturing.drop(columns=["Unit"])
        self.EI_manufacturing = df_manufacturing.to_numpy()

        # EI manufacturing of total RU
        self.EI_manufacturing_total = self.EI_manufacturing.sum(axis=1)

        # losses of each RU
        df_EI_use_onestep = pd.read_excel(excel, sheet_name="Use", index_col=0)
        df_EI_use_onestep = df_EI_use_onestep.drop(columns=["Unit"])
        self.EI_use_onestep = df_EI_use_onestep.to_numpy() * dic["num_hourPerYear"] / dic["step"] #  Edit(AEP): EI_use for one step

        ea = energy_amount[:]  # copy
        energy_amount = [0 if cost == 0 else ea.pop(0) for cost in dic['RU_kWh_cost']]
        self.cost_use_onestep = energy_amount * dic['RU_kWh_cost'] * dic["num_hourPerYear"] / dic["step"]  #  Edit(AEP): EI_use for one step

        # total losses
        self.EI_use_onestep_total = self.EI_use_onestep.sum(axis=1)

        self.cost_use_onestep_total = self.cost_use_onestep.sum(axis=0)

        # Number of component - remplacement unite
        dic["nb_RU"] = self.EI_manufacturing.shape[1]
        excel.close()

        

        if beta_sigma_ERW.shape[0] != dic["nb_RU"]:
            print(
                f"Error: number of RU's faults ({beta_sigma_ERW.shape[0]}) is different from the expected number of RU {dic['nb_RU']}."
            )
            sys.exit(1)

        # Checking for the presence of "NaN" values
        if np.isnan(beta_sigma_ERW).any():
            print("Error: The fault table contains NaN.")
            sys.exit(1)

        #  Edit(AEP): /!\ sigma unit is years
        dic["sigma_early"] = [sigma for sigma in beta_sigma_ERW[:, 0]]
        dic["sigma_random"] = [sigma for sigma in beta_sigma_ERW[:, 2]]
        dic["sigma_wearout"] = [sigma for sigma in beta_sigma_ERW[:, 4]]
        dic["beta_early"] = [sigma for sigma in beta_sigma_ERW[:, 1]]
        dic["beta_random"] = [sigma for sigma in beta_sigma_ERW[:, 3]]
        dic["beta_wearout"] = [sigma for sigma in beta_sigma_ERW[:, 5]]

        self.creation(dic)

    # %%
    def creation(self, dic):
        nb_RU = dic["nb_RU"]
        nb_ite_MC = dic["nb_ite_MC"]
        # Edit(AEP): list of times (in years), can contain fractions of years (e.g., 7.3 years), the number of elements is the total number of time steps
        t = self.t

        # Edit(AEP): Useless if statement ? In dictionary.py, dic["pre_set_fail"] is set to False, and this boolean is not retrieved from the input Excel file
        if dic["pre_set_fail"] == False:
            random_fault_time = np.array(
                [[random.uniform(0, 1) for y in range(nb_ite_MC)] for y in range(nb_RU)], dtype="float"
            ).T
            random_fault_type = np.array(
                [[random.uniform(0, 1) for y in range(nb_ite_MC)] for y in range(nb_RU)], dtype="float"
            ).T
        
        # Edit(AEP): RU_age matrix size: nb_RU x nb_ite_MC x usage_time
        # /!\ usage_time = Total number of time steps (in time steps)
        # RU_age is set to be an array of floats this is done by adding ', dtype="float"'. Otherwise, it could not contain fractions of years as encountered with number of steps different from 1.
        self.RU_age = np.array([[[0 for i in range(nb_RU)] for z in range(nb_ite_MC)] for y in range(self.usage_time)], dtype="float")

        # Edit(AEP): driver_age matrix seems unused
        self.driver_age = np.array(
            [[[0 for i in range(nb_RU)] for z in range(nb_ite_MC)] for y in range(self.usage_time)]
        )
        # Initialisation of EI matrices
        # /!\ usage_time = Total number of time steps (in time steps)
        self.EI_total = np.array(
            [[self.EI_manufacturing_total for z in range(nb_ite_MC)] for y in range(self.usage_time)], dtype="float"
        )
        self.EI_total_manu = np.array(
            [[self.EI_manufacturing_total for z in range(nb_ite_MC)] for y in range(self.usage_time)], dtype="float"
        )
        self.EI_total_maintenance = np.array(
            [[self.EI_manufacturing_total * 0 for z in range(nb_ite_MC)] for y in range(self.usage_time)], dtype="float"
        )
        self.EI_total_use = np.array(
            [[self.EI_manufacturing_total * 0 for z in range(nb_ite_MC)] for y in range(self.usage_time)], dtype="float"
        )
        # Initialisation of cost matrices
        self.cost_total = np.array(
            [[self.cost_manufacturing_total for z in range (nb_ite_MC)] for y in range (self.usage_time)], dtype='float'
        )
        self.cost_total_manufacturing = np.array(
            [[self.cost_manufacturing_total for z in range (nb_ite_MC)] for y in range (self.usage_time)], dtype='float'
        )
        self.cost_total_maintenance = np.array(
            [[self.cost_manufacturing_total*0 for z in range (nb_ite_MC)] for y in range (self.usage_time)], dtype='float'
        )
        self.cost_total_use = np.array(
            [[self.cost_manufacturing_total*0 for z in range (nb_ite_MC)] for y in range (self.usage_time)], dtype='float'
        )

        self.number_of_fault = np.array(
            [[[0 for i in range(nb_RU)] for z in range(nb_ite_MC)] for y in range(self.usage_time)]
        )

        self.fault_cause = np.array(
            [[["" for i in range(nb_RU)] for z in range(nb_ite_MC)] for y in range(self.usage_time)], dtype="<U10"
        )

        # Edit(AEP): t = list of times (in years), can contain fractions of years (e.g., 7.3 years), the number of elements is the total number of time steps
        weibull_Efault = np.array([[0 for i in range(nb_RU)] for z in t], dtype="float")
        weibull_Rfault = np.array([[0 for i in range(nb_RU)] for z in t], dtype="float")
        weibull_Wfault = np.array([[0 for i in range(nb_RU)] for z in t], dtype="float")

        prob_weibull_Efault = np.array([[0 for i in range(nb_RU)] for z in t], dtype="float")
        prob_weibull_Rfault = np.array([[0 for i in range(nb_RU)] for z in t], dtype="float")
        prob_weibull_Wfault = np.array([[0 for i in range(nb_RU)] for z in t], dtype="float")

        # Edit(AEP): size of time matrix: (total number of time steps) x nb_RU
        # Each time from t is incremented by 1 time step. 
        # The duration of one time step is equal to 1/dic["step"], therefore t + 1 is replaced by t + 1/dic["step"]
        time = np.array([t + 1/dic["step"] for i in range(nb_RU)]).T 

        (row_r, col_r) = dic["Remplacement_matrix"].shape
        remplacement = np.array(
            [[[0 for y in range(col_r)] for z in range(row_r)] for i in range(nb_ite_MC)], dtype="float"
        )

        # Random matrix for other RUs replacements
        random_replacement_ratio = np.array(
            [[[random.uniform(0, 1) for y in range(col_r)] for z in range(row_r)] for i in range(nb_ite_MC)], dtype="float"
        )
        
        remplacement_or = np.array([[0 for y in range(nb_RU)] for i in range(nb_ite_MC)], dtype="float")

        # Edit(AEP): /!\ sigma and time list should be in the same unit (years), otherwise, the probability is miscalculated.
        # In the following lines, time - 1 is replaced by time - 1/dic["step"]
        if dic["Early_failure"] == "True":
            weibull_Efault = np.array(
                weibull_min.cdf(time - 1/dic["step"], dic["beta_early"][:], scale=dic["sigma_early"][:]), ndmin=2, dtype="float"
            )

        if dic["Random_failure"] == "True":
            weibull_Rfault = np.array(
                weibull_min.cdf(time - 1/dic["step"], dic["beta_random"][:], scale=dic["sigma_random"][:]), ndmin=2, dtype="float"
            )

        if dic["Wearout_failure"] == "True":
            weibull_Wfault = np.array(
                weibull_min.cdf(time - 1/dic["step"], dic["beta_wearout"], scale=dic["sigma_wearout"][:]), ndmin=2, dtype="float"
            )

        wcdf_sum = np.sum([weibull_Efault, weibull_Rfault, weibull_Wfault], axis=0)

        wcdf = 1 - (1 - weibull_Efault) * (1 - weibull_Rfault) * (1 - weibull_Wfault)


        self.wcdf_per_RU = wcdf

        self.wcdf_total = 1 - np.prod(1 - wcdf, axis=1)

        if dic["Early_failure"] == "True":
            prob_weibull_Efault = weibull_Efault / wcdf_sum
        if dic["Random_failure"] == "True":
            prob_weibull_Rfault = weibull_Rfault / wcdf_sum

        if dic["Wearout_failure"] == "True":
            prob_weibull_Wfault = np.divide(weibull_Wfault, wcdf_sum)

        # Edit(AEP): Suggestion to rename the variable wcdf_year with wcdf_step
        wcdf_year = np.array([[0 for y in range(nb_ite_MC)] for y in range(nb_RU)], dtype="float").T

        
        for step in range(1, self.usage_time):
            # Edit(AEP): The age of RUs is increased by 1 time step i.e., by 1/dic["step"], therefore, + 1 is replaced by + 1/dic["step"]
            self.RU_age[step, :, :] = self.RU_age[step - 1, :, :] + 1/dic["step"]
            
            
            # Preventive Maintenance
            EI_maintenance = 0
            cost_maintenance = 0

            if dic["Maintenance"] == "True":
                # Mise à jour de la matrice remplacement et remise à zéro des composants lors de la maintenance

                # Edit(AEP): RU_age is in years (can be a fraction of years, e.g., 3.4years), dic["maintenance"] is in years
                # Because np.where can only compare integers, both RU_age and dic["maintenance"] need to be converted into the index of their corresponding time step
                # This is done by multiplying the two quantities by dic["step"] (number of steps per year) and converting them into int arrays with .astype(np.int_) method
                maintenance_indices = np.where(
                    (self.RU_age[step, :, :]*dic["step"]).astype(np.int_) == (dic["maintenance"]*dic["step"]).astype(np.int_)
                )  # Trouver les composants dont l'année correspond à l'année de maintenance
                remplacement_or[maintenance_indices[0], maintenance_indices[1]] = 1

                # Remettre l'âge des composants à zéro (RU) pour ceux qui ont subi une maintenance
                self.RU_age[step, :, :] = np.round((1 - remplacement_or[:, :nb_RU])) * self.RU_age[step, :, :]
                EI_maintenance = self.EI_manufacturing.dot(remplacement_or.T).T

                # /!\ remplacement_or is the matrix for preventive maintenance
                cost_maintenance = remplacement_or.dot((dic["RU_raw_cost"] + dic["RU_des_cost"] + dic["RU_ass_cost"]).T)
                remplacement_or = remplacement_or * 0
                
                 # new random number for new component
                random_fault_time[maintenance_indices] = [random.uniform(0, 1) for y in maintenance_indices[1]]
                random_fault_type[maintenance_indices] = [random.uniform(0, 1) for y in maintenance_indices[1]]
                random_replacement_ratio = np.array([[[random.uniform(0, 1) for y in range(col_r)] for z in range(row_r)] for i in range(nb_ite_MC)], dtype="float")

            # Curative Maintenance

            # probabilité de défaillance individuelle de tout le système
            # Edit(AEP): Suggestion to rename the variable wcdf_oldyear with wcdf_oldstep
            # Edit(AEP): Suggestion to rename the variable wcdf_year with wcdf_step
            wcdf_oldyear = wcdf_year
            wcdf_year = _wcdf(self, step, dic, nb_RU, weibull_Efault, weibull_Rfault, weibull_Wfault)

            # détection des fautes pour chaque composant
            Fault = np.where((wcdf_oldyear <= random_fault_time) & (random_fault_time <= wcdf_year))
            notFault = np.where((wcdf_oldyear > random_fault_time) | (random_fault_time > wcdf_year))

            # Edit(AEP): age_component is in years (can be a fraction of years, e.g. 3.4years)
            age_component = self.RU_age[step, Fault[0], Fault[1]]

            # Find the type of the fault for each RU
            # Early Faults
            # Edit(AEP): In the next lines, the elements stored in age_component and RU_age are used as indices, therefore they should beintegers.
            # Both age_component and RU_age are initially expressed in years (can be a fraction of years, e.g. 3.4years),
            # and therefore needs to be converted into arrays storing the corresponding time step indices.
            # This is done by multiplying them with dic["step"] and converting them into arrays of integers with .astype(np.int_) method
            Fault_E = np.where(
                random_fault_type[Fault] <= prob_weibull_Efault[np.round(self.RU_age[step, Fault[0], Fault[1]]*dic["step"]).astype(np.int_), Fault[1]]
            )
            self.fault_cause[step, Fault[0][Fault_E], Fault[1][Fault_E]] = "Early"
            remplacement[Fault[0][Fault_E], Fault[1][Fault_E], :] = dic["Remplacement_matrix"].loc[
                Fault[1][Fault_E]
            ]
            # Random Faults
            down = prob_weibull_Efault[np.round(self.RU_age[step, Fault[0], Fault[1]]*dic["step"]).astype(np.int_), Fault[1]] 
            up = down + prob_weibull_Rfault[np.round(age_component*dic["step"]).astype(np.int_), Fault[1]]
            Fault_R = np.where((random_fault_type[Fault] > down) & (random_fault_type[Fault] <= up))
            self.fault_cause[step, Fault[0][Fault_R], Fault[1][Fault_R]] = "Random"
            remplacement[Fault[0][Fault_R], Fault[1][Fault_R], :] = dic["Remplacement_matrix"].loc[
                Fault[1][Fault_R]
            ]
            # Wearout Faults
            down = up
            Fault_W = np.where((random_fault_type[Fault] > down))
            self.fault_cause[step, Fault[0][Fault_W], Fault[1][Fault_W]] = "Wearout"
            remplacement[Fault[0][Fault_W], Fault[1][Fault_W], :] = dic["Remplacement_matrix"].loc[
                Fault[1][Fault_W]
            ]

            # Determine RUs that should be replaced based on Excel replacement matrix
            # A random number is drawn, if the random number is below the "replacement ratio", the RU has to be replaced
            # 1 is set for the corresponding RU in the replacement matrix

            # Searching the indices corresponding to random_number <= replacement ratio -> 1
            below_replacement_ratio = np.where(
                remplacement >= random_replacement_ratio
                )
            # Searching the indices corresponding to random_number > replacement ratio -> 0
            above_replacement_ratio = np.where(
                remplacement < random_replacement_ratio
                )
            # Searching the indices corresponding to 0 element in replacement matrix -> 0
            no_fault_replacement = np.where(
                remplacement == 0
                )
            remplacement[below_replacement_ratio] = 1
            remplacement[above_replacement_ratio] = 0
            remplacement[no_fault_replacement] = 0

            # new random number for new component
            random_fault_time[Fault] = [random.uniform(0, 1) for y in Fault[1]]
            random_fault_type[Fault] = [random.uniform(0, 1) for y in Fault[1]]
            random_replacement_ratio = np.array([[[random.uniform(0, 1) for y in range(col_r)] for z in range(row_r)] for i in range(nb_ite_MC)], dtype="float")

            # Remplacement vector (RV)
            remplacement_or = remplacement.sum(axis=1)
            # Limiter les valeurs de remplacement_or à un maximum de 1
            remplacement_or = np.clip(remplacement_or, 0, 1)

            # Impact calculation
            self.EI_total_manu[step, :, :] = (
                self.EI_total_manu[step - 1, :, :] + self.EI_manufacturing.dot(remplacement_or.T).T + EI_maintenance
            )
            self.EI_total_use[step, :, :] = self.EI_total_use[step - 1, :, :] + self.EI_use_onestep_total
            self.EI_total[step, :, :] = self.EI_total_use[step, :, :] + self.EI_total_manu[step, :, :]
            self.EI_total_maintenance[step, :, :] = self.EI_total_maintenance[step - 1, :, :] + EI_maintenance

            # Cost Calculation
            self.cost_total_manufacturing[step,:] = self.cost_total_manufacturing[step-1,:]+remplacement_or.dot((dic["RU_raw_cost"]+dic["RU_des_cost"]+dic["RU_ass_cost"]).T) +cost_maintenance
            self.cost_total_use[step,:] = self.cost_total_use[step-1,:]+self.cost_use_onestep_total
            self.cost_total_maintenance[step,:] = self.cost_total_maintenance[step-1,:]+cost_maintenance
            self.cost_total[step,:] = self.cost_total_use[step,:]+self.cost_total_manufacturing[step,:]

            # Calcul de l'âge moyen pondéré par rapport à la matrice de rempacement, arrondis à l'entier le plus proche
            self.RU_age[step, :, :] = np.round((1 - remplacement_or[:, :nb_RU])) * self.RU_age[step, :, :]

            self.number_of_fault[step, :, :] = self.number_of_fault[step - 1, :, :] + remplacement_or[:, :nb_RU]

            # initialise
            wcdf_oldyear[Fault[0][Fault_W], Fault[1][Fault_W]] = 0
            remplacement = remplacement * 0
            remplacement_or = remplacement_or * 0

    def get_variables(self, dic):
        index_labels = np.array(["Manufacture", "Use", "Replacement", "Maintenance"])
        manufacturing = self.EI_manufacturing_total
        # Edit(AEP): In the following lines, mean values of EIs and costs are calculated at the last time step.
        # Therefore, dic["service_life"] is replaced with dic["service_life"]*dic["step"]
        use = np.mean(self.EI_total_use[dic["service_life"]*dic["step"] - 1, :, :], axis=0)
        maintenance = np.mean(self.EI_total_maintenance[dic["service_life"]*dic["step"] - 1, :, :], axis=0)
        replacement = np.mean(self.EI_total_manu[dic["service_life"]*dic["step"] - 1, :, :], axis=0) - manufacturing - maintenance

        manufacturing_cost = self.cost_manufacturing_total
        use_cost = np.mean(self.cost_total_use[dic["service_life"]*dic["step"] - 1, :], axis=0)
        maintenance_cost = np.mean(self.cost_total_maintenance[dic["service_life"]*dic["step"] - 1, :], axis=0)
        replacement_cost = np.mean(self.cost_total_manufacturing[dic["service_life"]*dic["step"] - 1, :], axis=0) - manufacturing_cost - maintenance_cost

        # Créer un DataFrame avec les données
        data = {
            "Method": dic["EI_name"],
            "LCIA Unit": dic["LCIA_unit"],
            "Manufacture": manufacturing,
            "Use": use,
            "Replacement": replacement,
            "Maintenance": maintenance,
        }

        df = pd.DataFrame(data)

        # Ajouter l'impact économique au dataframe
        df.loc[len(df)] = ["ECO", "Euros", manufacturing_cost, use_cost, replacement_cost, maintenance_cost]

        # Définir le chemin du fichier Excel
        excel_path = os.path.join(dic["path_result_EI"], dic["directory"], dic["filename_result_staircase"])

        # Écrire le DataFrame dans un fichier Excel
        df.to_excel(excel_path, index=False)

        print(f"The data were written to the Excel file: : {excel_path}")

        return (
            self.EI_total,
            self.EI_total_manu,
            self.EI_total_use,
            self.usage_time,
            self.number_of_fault,
            self.wcdf_total,
            self.wcdf_per_RU,
            self.fault_cause,
            self.RU_age,
            self.EI_total_maintenance,
            self.cost_total_manufacturing,
            self.cost_total_use,
            self.cost_total_maintenance,
            self.cost_total,
        )
