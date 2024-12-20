"""PELCA (Power Electronics Life Cycle Assessment) is an open-source project aimed at assessing the environmental impact over the life cycle of modular and diagnosable power electronics systems. The integration of modularity and diagnosability aligns with circular economy principles, promoting practices such as repair and reuse. This project provides a tool to calculate the environmental impacts associated with the manufacturing, usage, and replacement of power electronics products.
Copyright (C) Mitsubishi Electric R&D Centre Europe and SATIE 2024, author Briac Baudais baudaisbriac@gmail.com

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this program.  If not, see https://www.gnu.org/licenses/lgpl-3.0.html"""

"""
Created on 2024

@author: baudais, bdubus

"""

import csv
import os
import pickle
import shutil

import numpy as np
import pandas as pd


def _init_dir(path, directory):
    # Create the directory
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)
    print("Directory '% s' created" % directory)


# %% Init
def _init_dic(path_input, name_input, lca):
    def read_excel_sheet(excel, sheet_name, header, skiprows, usecols=None):
        return pd.read_excel(excel, sheet_name=sheet_name, header=header, skiprows=skiprows, usecols=usecols)

    def get_value_from_df(df, search_value, col_index=1):
        return df.iloc[df[df.isin([search_value]).any(axis=1)].index[0], col_index]

    def save_dict_to_file(dic, path, file_name, file_name_pickle):
        path_file = os.path.join(path, file_name)
        path_file_pickle = os.path.join(path, file_name_pickle)

        with open(path_file, "w") as csv_file:
            writer = csv.writer(csv_file)
            for key, value in dic.items():
                writer.writerow([key, value])

        with open(path_file_pickle, "wb") as fp:
            pickle.dump(dic, fp)

    excel = pd.ExcelFile(os.path.join(path_input, name_input))
    df = read_excel_sheet(excel, "LCA", header=None, skiprows=1)
    df_LCIA = read_excel_sheet(excel, "LCIA", header=0, skiprows=1)
    df_stair = read_excel_sheet(excel, "Staircase", header=None, skiprows=1)
    df_RM = read_excel_sheet(excel, "Curr. Maint. (replac. matrix)", header=None, skiprows=[0, 1, 2, 3], usecols=lambda x: x != 0)
    df_cost = read_excel_sheet(excel, "Cost - Price", header=None, skiprows=[0, 1, 2, 3, 4], usecols=lambda x: x != 0)
    excel.close()

    dic = {}

    dic["path_result_EI"] = get_value_from_df(df, "LCA result path")
    dic["filename_result_EI"] = "LCA output.xlsx"
    dic["filename_result_EI_MC"] =  "Monte Carlo output.xlsx"
    dic["simulation"] = get_value_from_df(df, "Type of simulation (Analysis\\Monte Carlo)")
    dic["directory"] = "Results PELCA"
    dic["LCA_path"] = os.path.join(dic["path_result_EI"], dic["directory"])
    path = os.path.join(path_input, dic["directory"])

    file_path = os.path.join(
        dic["path_result_EI"],
        dic["directory"],
        dic["filename_result_EI"] if dic["simulation"] == "Analysis" else dic["filename_result_EI_MC"],
    )

    if os.path.exists(file_path):
        excel = pd.ExcelFile(file_path)
        df_result = pd.read_excel(excel, header=0)
        excel.close()
        dic["EI_name"] = df_result["Method"].tolist()
        dic["LCIA_unit"] = df_result["Unit"].tolist()
        dic["proj_name"] = get_value_from_df(df, "Project name (brightway)")

    else:
        _init_dir(dic["LCA_path"], dic["directory"])
    dic["database_ecoinvent"] = get_value_from_df(df, "Database ecoinvent")
    dic["database_ecoinvent_path"] = get_value_from_df(df, "Ecoinvent path")
    dic["inventory_name"] = get_value_from_df(df, "Inventory name")
    dic["proj_name"] = get_value_from_df(df, "Project name (brightway)")
    dic["iterations"] = get_value_from_df(df, "Number of iterations (Monte Carlo)")

    dic["EI_name"] = df_LCIA["Acronym"].tolist()
    dic["LCIA_unit"] = df_LCIA["Unit"].tolist()
    dic["LCIA"] = df_LCIA


    dic["service_life"] = get_value_from_df(df_stair, "Service life (year)")
    dic["num_hourPerYear"] = get_value_from_df(df_stair, "Annual usage time (hours/year)")
    dic["step"] = get_value_from_df(df_stair, "Time step (step/year)")
    dic["filename_result_staircase"] = "Staircase output.xlsx"
    dic["nb_ite_MC"] = get_value_from_df(df_stair, "Monte Carlo (number of iteration)")
    dic["Early_failure"] = get_value_from_df(df_stair, "Early failure")
    dic["Random_failure"] = get_value_from_df(df_stair, "Random failure")
    dic["Wearout_failure"] = get_value_from_df(df_stair, "Wearout failure")
    dic["Maintenance"] = get_value_from_df(df_stair, "Preventive Maintenance")
    dic["pre_set_fail"] = False
    dic["Remplacement_matrix"] = df_RM
    dic["Cost_matrix"] = df_cost
    dic["selected_EI"] = get_value_from_df(df_stair, "Plot specific env. impact") - 1

    save_dict_to_file(dic, dic["LCA_path"], "dict_file.csv", "dict_file.pkl")
    print(dic["LCA_path"])
    print("dictionary saved successfully to file")

    return dic
