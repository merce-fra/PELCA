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

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import weibull_min


def _wcdf(self, year, dic, nb_RU, weibull_Efault, weibull_Rfault, weibull_Wfault):
    weibull_E = np.array([[0 for i in range(nb_RU)] for z in range(dic["nb_ite_MC"])], dtype="float")
    weibull_R = np.array([[0 for i in range(nb_RU)] for z in range(dic["nb_ite_MC"])], dtype="float")
    weibull_W = np.array([[0 for i in range(nb_RU)] for z in range(dic["nb_ite_MC"])], dtype="float")

    indices = self.RU_age[year - 1, :, :]

    if dic["Early_failure"] == "True":
        weibull_E = weibull_Efault[indices, np.arange(nb_RU)]
    if dic["Random_failure"] == "True":
        weibull_R = weibull_Rfault[indices, np.arange(nb_RU)]

    if dic["Wearout_failure"] == "True":
        # weibull_W=weibull_Wfault[self.RU_age[year-1,:,:]][:,0,:]
        # weibull_W=1-np.prod(1 - weibull_Wfault[self.RU_age[year-1]][:,0,:], axis=1)
        weibull_W = weibull_Wfault[indices, np.arange(nb_RU)]  # shape: (1000, 2)

    wcdf = 1 - (1 - weibull_E) * (1 - weibull_R) * (1 - weibull_W)

    return wcdf


class STAIRCASE:
    # %%
    def __init__(self, path_input, name_input, dic):
        self.usage_time = dic["service_life"] * dic["step"]  # in month
        epsilon = 1e-10  # allow to avoid to divide by 0 during .../wcdf_sum
        self.t = np.linspace(epsilon, dic["service_life"], self.usage_time)

        excel = pd.ExcelFile(os.path.join(path_input, name_input))
        data = pd.read_excel(excel, sheet_name="Faults & Maintenance", index_col=0, skiprows=[0, 1, 2])
        # Extract the 6th column (index 5) into a variable named 'maintenance'
        dic["maintenance"] = data.iloc[:, 6].to_numpy()
        # Drop the 6th column (index 5) from the DataFrame and convert it to a NumPy array for 'beta_sigma_ERW'

        data_cost = pd.read_excel(excel, sheet_name='Cost - Price', skiprows=4, usecols="B:G")
        dic["RU_raw_cost"] = data_cost.iloc[:, 0].to_numpy()
        dic["RU_rep_cost"] = data_cost.iloc[:, 2].to_numpy()
        dic["RU_ass_cost"] = data_cost.iloc[:, 3].to_numpy()
        dic["RU_des_cost"] = data_cost.iloc[:, 4].to_numpy()
        dic["RU_kWh_cost"] = data_cost.iloc[:, 5].to_numpy()

        
        self.cost_manufacturing_total = dic["RU_raw_cost"].sum(axis=0)

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
        self.EI_use_onestep = df_EI_use_onestep.to_numpy() * dic["num_hourPerYear"] / dic["step"]

        self.cost_use_onestep = dic['RU_kWh_cost'] * dic['num_hourPerYear'] / dic['step']

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
        t = self.t

        if dic["pre_set_fail"] == False:
            random_fault_time = np.array(
                [[random.uniform(0, 1) for y in range(nb_ite_MC)] for y in range(nb_RU)], dtype="float"
            ).T
            random_fault_type = np.array(
                [[random.uniform(0, 1) for y in range(nb_ite_MC)] for y in range(nb_RU)], dtype="float"
            ).T

        self.RU_age = np.array([[[0 for i in range(nb_RU)] for z in range(nb_ite_MC)] for y in range(self.usage_time)])
        self.driver_age = np.array(
            [[[0 for i in range(nb_RU)] for z in range(nb_ite_MC)] for y in range(self.usage_time)]
        )
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
        self.cost_total = np.array([[self.cost_manufacturing_total for z in range (nb_ite_MC)] for y in range (self.usage_time)], dtype='float')
        self.cost_total_manufacturing = np.array([[self.cost_manufacturing_total for z in range (nb_ite_MC)] for y in range (self.usage_time)], dtype='float')
        self.cost_total_maintenance = np.array([[self.cost_manufacturing_total*0 for z in range (nb_ite_MC)] for y in range (self.usage_time)], dtype='float')
        self.cost_total_use = np.array([[self.cost_manufacturing_total*0 for z in range (nb_ite_MC)] for y in range (self.usage_time)], dtype='float')

        self.number_of_fault = np.array(
            [[[0 for i in range(nb_RU)] for z in range(nb_ite_MC)] for y in range(self.usage_time)]
        )

        self.fault_cause = np.array(
            [[["" for i in range(nb_RU)] for z in range(nb_ite_MC)] for y in range(self.usage_time)], dtype="<U10"
        )

        weibull_Efault = np.array([[0 for i in range(nb_RU)] for z in t], dtype="float")
        weibull_Rfault = np.array([[0 for i in range(nb_RU)] for z in t], dtype="float")
        weibull_Wfault = np.array([[0 for i in range(nb_RU)] for z in t], dtype="float")

        prob_weibull_Efault = np.array([[0 for i in range(nb_RU)] for z in t], dtype="float")
        prob_weibull_Rfault = np.array([[0 for i in range(nb_RU)] for z in t], dtype="float")
        prob_weibull_Wfault = np.array([[0 for i in range(nb_RU)] for z in t], dtype="float")

        time = np.array([t + 1 for i in range(nb_RU)]).T

        (row_r, col_r) = dic["Remplacement_matrix"].shape
        remplacement = np.array(
            [[[0 for y in range(col_r)] for z in range(row_r)] for i in range(nb_ite_MC)], dtype="float"
        )
        remplacement_or = np.array([[0 for y in range(nb_RU)] for i in range(nb_ite_MC)], dtype="float")

        if dic["Early_failure"] == "True":
            weibull_Efault = np.array(
                weibull_min.cdf(time - 1, dic["beta_early"][:], scale=dic["sigma_early"][:]), ndmin=2, dtype="float"
            )

        if dic["Random_failure"] == "True":
            weibull_Rfault = np.array(
                weibull_min.cdf(time - 1, dic["beta_random"][:], scale=dic["sigma_random"][:]), ndmin=2, dtype="float"
            )

        if dic["Wearout_failure"] == "True":
            weibull_Wfault = np.array(
                weibull_min.cdf(time - 1, dic["beta_wearout"], scale=dic["sigma_wearout"][:]), ndmin=2, dtype="float"
            )

        wcdf_sum = np.sum([weibull_Efault, weibull_Rfault, weibull_Wfault], axis=0)

        wcdf = 1 - (1 - weibull_Efault) * (1 - weibull_Rfault) * (1 - weibull_Wfault)
        self.wcdf_total = 1 - np.prod(1 - wcdf, axis=1)

        if dic["Early_failure"] == "True":
            prob_weibull_Efault = weibull_Efault / wcdf_sum
        if dic["Random_failure"] == "True":
            prob_weibull_Rfault = weibull_Rfault / wcdf_sum

        if dic["Wearout_failure"] == "True":
            prob_weibull_Wfault = np.divide(weibull_Wfault, wcdf_sum)

        wcdf_year = np.array([[0 for y in range(nb_ite_MC)] for y in range(nb_RU)], dtype="float").T

        for year in range(1, self.usage_time):
            self.RU_age[year, :, :] = self.RU_age[year - 1, :, :] + 1

            if dic["pre_set_fail"] == True:
                if year in dic["year_pre_set_fail"]:
                    indice_tuple = np.where(year == dic["year_pre_set_fail"])
                    indice = indice_tuple[0][0]
                    self.fault_cause[year, 0, dic["UR_set_fail"][indice]] = dic["typefault_pre_set_fail"][indice]
                    remplacement[0, dic["UR_set_fail"][indice], :] = (
                        dic["Remplacement_matrix"]
                        .loc[dic["Remplacement_matrix"]["Fault"] == dic["typefault_pre_set_fail"][indice]]
                        .drop(["Fault"], axis=1)
                        .reset_index(drop=True)
                        .loc[dic["UR_set_fail"][indice]]
                    )

            # part maintenance
            EI_maintenance = 0
            cost_maintenance = 0
            if dic["Maintenance"] == "True":
                # Mise à jour de la matrice remplacement et remise à zéro des composants lors de la maintenance
                maintenance_indices = np.where(
                    self.RU_age[year, :, :] == dic["maintenance"]
                )  # Trouver les composants dont l'année correspond à l'année de maintenance
                remplacement_or[maintenance_indices[0], maintenance_indices[1]] = 1

                # Remettre l'âge des composants à zéro (RU) pour ceux qui ont subi une maintenance
                self.RU_age[year, :, :] = np.round((1 - remplacement_or[:, :nb_RU])) * self.RU_age[year, :, :]
                EI_maintenance = self.EI_manufacturing.dot(remplacement_or.T).T
                cost_maintenance = remplacement_or.dot(dic["RU_raw_cost"] + dic["RU_des_cost"] + dic["RU_ass_cost"])
                remplacement_or = remplacement_or * 0

                # part faut

                # probabilité de défaillance individuelle de tout le système
                wcdf_oldyear = wcdf_year
                wcdf_year = _wcdf(self, year, dic, nb_RU, weibull_Efault, weibull_Rfault, weibull_Wfault)

                # détection des fautes pour chaque composant
                Fault = np.where((wcdf_oldyear <= random_fault_time) & (random_fault_time <= wcdf_year))
                notFault = np.where((wcdf_oldyear > random_fault_time) | (random_fault_time > wcdf_year))

                age_component = self.RU_age[year, Fault[0], Fault[1]]

                # Find the type of the fault for each RU
                Fault_E = np.where(
                    random_fault_type[Fault] <= prob_weibull_Efault[self.RU_age[year, Fault[0], Fault[1]], Fault[1]]
                )
                self.fault_cause[year, Fault[0][Fault_E], Fault[1][Fault_E]] = "Early"
                remplacement[Fault[0][Fault_E], Fault[1][Fault_E], :] = dic["Remplacement_matrix"].loc[
                    Fault[1][Fault_E]
                ]

                down = prob_weibull_Efault[self.RU_age[year, Fault[0], Fault[1]], Fault[1]]
                up = down + prob_weibull_Rfault[age_component, Fault[1]]
                Fault_R = np.where((random_fault_type[Fault] > down) & (random_fault_type[Fault] <= up))
                self.fault_cause[year, Fault[0][Fault_R], Fault[1][Fault_R]] = "Random"
                remplacement[Fault[0][Fault_R], Fault[1][Fault_R], :] = dic["Remplacement_matrix"].loc[
                    Fault[1][Fault_R]
                ]

                down = up
                Fault_W = np.where((random_fault_type[Fault] > down))
                self.fault_cause[year, Fault[0][Fault_W], Fault[1][Fault_W]] = "Wearout"
                remplacement[Fault[0][Fault_W], Fault[1][Fault_W], :] = dic["Remplacement_matrix"].loc[
                    Fault[1][Fault_W]
                ]

                # new random number for new component
                random_fault_time[Fault] = [random.uniform(0, 1) for y in Fault[1]]
                random_fault_type[Fault] = [random.uniform(0, 1) for y in Fault[1]]

            # Remplacement vector (RV)
            remplacement_or = remplacement.sum(axis=1)
            # Limiter les valeurs de remplacement_or à un maximum de 1
            remplacement_or = np.clip(remplacement_or, 0, 1)

            # Impact calculation
            self.EI_total_manu[year, :, :] = (
                self.EI_total_manu[year - 1, :, :] + self.EI_manufacturing.dot(remplacement_or.T).T + EI_maintenance
            )
            self.EI_total_use[year, :, :] = self.EI_total_use[year - 1, :, :] + self.EI_use_onestep_total
            self.EI_total[year, :, :] = self.EI_total_use[year, :, :] + self.EI_total_manu[year, :, :]
            self.EI_total_maintenance[year, :, :] = self.EI_total_maintenance[year - 1, :, :] + EI_maintenance

            # Calcul de l'âge moyen pondéré par rapport à la matrice de rempacement, arrondis à l'entier le plus proche
            self.RU_age[year, :, :] = np.round((1 - remplacement_or[:, :nb_RU])) * self.RU_age[year, :, :]

            self.number_of_fault[year, :, :] = self.number_of_fault[year - 1, :, :] + remplacement_or[:, :nb_RU]

            # initialise
            wcdf_oldyear[Fault[0][Fault_W], Fault[1][Fault_W]] = 0
            remplacement = remplacement * 0
            remplacement_or = remplacement_or * 0

    def get_variables(self, dic):
        index_labels = np.array(["Manufacture", "Use", "Replacement", "Maintenance"])
        manufacturing = self.EI_manufacturing_total
        use = np.mean(self.EI_total_use[dic["service_life"] - 1, :, :], axis=0)
        maintenance = np.mean(self.EI_total_maintenance[dic["service_life"] - 1, :, :], axis=0)
        replacement = np.mean(self.EI_total_manu[dic["service_life"] - 1, :, :], axis=0) - manufacturing - maintenance

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
            self.fault_cause,
            self.RU_age,
            self.EI_total_maintenance,
            self.cost_total_manufacturing,
            self.cost_total_use,
            self.cost_total_maintenance,
            self.cost_total,
        )
