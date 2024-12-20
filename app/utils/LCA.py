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

import brightway2 as bw
import numpy as np
import pandas as pd
from brightway2 import *
from stats_arrays import *
import shutil

def delete_cache(target_string):
    """
    Deletes folders in the user's AppData directory and its subdirectories
    that contain the specified `target_string` in their name.

    :param target_string: The string to search for in folder names.
    :raises ValueError: If the AppData directory does not exist.
    """
    # Construct the AppData path based on the user's profile
    user_profile = os.path.expandvars("%USERPROFILE%")
    base_dir = os.path.join(user_profile, "AppData")

    print(f"Searching for folders containing '{target_string}' in '{base_dir}'")

    if not os.path.isdir(base_dir):
        raise ValueError(f"The directory {base_dir} does not exist.")

    # Flag to check if any folder is deleted
    deleted_any = False

    # Recursively search the directory
    for root, dirs, _ in os.walk(base_dir):
        for dir_name in dirs:
            if target_string in dir_name:  # Check if folder name contains the target string
                folder_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(folder_path)  # Delete the folder and its contents
                    print(f"Deleted folder: {folder_path}")
                    deleted_any = True
                except Exception as e:
                    print(f"Error deleting {folder_path}: {e}")

    if not deleted_any:
        print("No cache to delete.")


def EI_calculation(dic, path_input, name_input):
    # open project
    print("Project name : ", dic["proj_name"])
    delete_cache(dic["proj_name"])  # Supprimer les caches ecoinvent

    projects.set_current(dic["proj_name"])  # Creating/accessing the project

    bw2setup()  # Importing elementary flows, LCIA methods and some other data

    # ecoinvent
    if dic["database_ecoinvent"] in bw.databases:
        print("Database has already been imported.")
    else:
        # mind that the ecoinvent file must be unzipped; then: path to the datasets subfolder
        print("Database hasn't been imported.")
        fpei37cut = dic["database_ecoinvent_path"]
        # the "r" makes sure that the path is read as a string - especially useful when you have spaces in your string
        ei37cutoff = bw.SingleOutputEcospold2Importer(fpei37cut, dic["database_ecoinvent"], use_mp=False)
        ei37cutoff
        ei37cutoff.apply_strategies()
        ei37cutoff.statistics()
        ei37cutoff.write_database()

    bw.create_core_migrations()

    # Export excel
    imp = bw.ExcelImporter(os.path.join(path_input, name_input))
    imp.apply_strategies()
    imp.match_database(fields=("name", "reference product", "unit", "location"))
    imp.match_database(dic["database_ecoinvent"], fields=("name", "reference product", "unit", "location"))
    imp.statistics()

    # imp.write_excel()  # ou can check whether the import went as expected by having a look at an Excel sheet, that includes our process data.

    imp.write_database()  # Having imported the data, we also need to write it to a database to save it

    print("\n")
    activities = bw.Database(dic["inventory_name"])  # activities presentation
    for act in activities:
        print(act)

    act_LCA = activities
    methods = []

    for index, row in dic["LCIA"].iterrows():
        method_tuple = (row["Method name"], row["Impact category"], row["Specific context"])
        methods.append(method_tuple)

    results = []

    print("\n")
    print("Starting LCA calculation :")
    for act in act_LCA:
        print(act)
        lca = bw.LCA({act: 1})
        lca.lci()
        for method in methods:
            lca.switch_method(method)
            lca.lcia()
            results.append((act["name"], method[1].title(), lca.score))
    # results

    # Mise en forme des résultats
    results_df = pd.DataFrame(results, columns=["Name", "Method", "Score"])
    method_order = results_df["Method"].unique()
    results_df = results_df.pivot(index="Method", columns="Name", values="Score")
    results_df = results_df.reindex(method_order)
    new_methods = dic["EI_name"]
    rename_dict = dict(zip(method_order, new_methods))
    results_df = results_df.rename(index=rename_dict)

    results_df

    # Basic LCA

    # Diviser le DataFrame en deux parties : avec et sans 'energy per hours'
    excel = pd.ExcelFile(os.path.join(path_input, name_input))
    df = pd.read_excel(excel, sheet_name="Inventory - Use", header=None)
    df_RU = pd.read_excel(excel, sheet_name="Inventory - Manufacturing", header=None)

    excel.close()

    # Initialiser une liste pour stocker les nom des RU
    list_RU = []
    # Parcourir chaque ligne du DataFrame
    for index, row in df_RU.iterrows():
        # Vérifier si le contenu de la colonne 0 est 'activity'
        if row[0] == "Activity":
            # Ajouter la valeur de la colonne 1 à la liste
            list_RU.append(row[1])

    # Initialiser une liste pour stocker les valeurs
    list_energy = []
    # Parcourir chaque ligne du DataFrame
    for index, row in df.iterrows():
        # Vérifier si le contenu de la colonne 0 est 'activity'
        if row[0] == "Activity":
            # Ajouter la valeur de la colonne 1 à la liste
            list_energy.append(row[1])
    df_without_energy = results_df.drop(columns=list_energy).copy()
    df_energy_only = results_df[list_energy].copy()

    # Ajouter la colonne des unités de mesure
    df_without_energy["Unit"] = dic["LCIA_unit"]
    df_energy_only["Unit"] = dic["LCIA_unit"]

    # Réorganiser les colonnes pour placer "Unit" en deuxième position
    df_without_energy = df_without_energy[["Unit"] + [col for col in df_without_energy.columns if col != "Unit"]]
    df_without_energy = df_without_energy[["Unit"] + [col for col in list_RU if col in df_without_energy.columns]]
    df_energy_only = df_energy_only[["Unit"] + [col for col in df_energy_only.columns if col != "Unit"]]
    df_energy_only = df_energy_only[["Unit"] + [col for col in list_energy if col in df_energy_only.columns]]

    # Écrire chaque partie dans une feuille différente
    excel_path = os.path.join(dic["path_result_EI"], dic["directory"], dic["filename_result_EI"])
    with pd.ExcelWriter(excel_path, engine="xlsxwriter") as writer:
        # Écrire chaque partie dans une feuille différente
        df_without_energy.to_excel(writer, sheet_name="Manufacturing", index=True)
        df_energy_only.to_excel(writer, sheet_name="Use", index=True)

    # Monte Carlo part
    if dic["simulation"] == "Monte Carlo":
        # Lire les données d'Inventory - Use pour la simulation
        df_inventory_use = pd.read_excel(
            os.path.join(path_input, name_input), sheet_name="Inventory - Use", header=None
        )
        excel.close()

        # Modifier les quantités pour Monte Carlo
        updated_factors = df_inventory_use[df_inventory_use[0] == "Activity"][1].apply(
            lambda x: x * dic["num_hourPerYear"] * dic["service_life"]
        )
        activity_updates = dict(zip(df_inventory_use[df_inventory_use[0] == "Activity"][1], updated_factors))

        # define the function for MC simulation
        iterations = dic["iterations"]

        def multiImpactMonteCarloLCA(functional_unit, list_methods, iterations):
            # Step 1
            MC_lca = bw.MonteCarloLCA(functional_unit)
            MC_lca.lci()  # take time
            # Step 2
            C_matrices = {}
            # Step 3
            for method in list_methods:
                MC_lca.switch_method(method)
                C_matrices[method] = MC_lca.characterization_matrix
            # Step 4
            results = np.empty((len(list_methods), iterations))
            # Step 5
            i = 0
            for iteration in range(iterations):
                next(MC_lca)  # take time
                i = i + 1
                print("Iteration : ", iteration)
                for method_index, method in enumerate(list_methods):
                    results[method_index, iteration] = (C_matrices[method] * MC_lca.inventory).sum()
            return results

        # Update the functional unit with the modified quantities
        fu = {act: activity_updates.get(act, 1) for act in activities}

        # let it run!
        print("\nMonte Carlo : ", dic["proj_name"])
        test_results = multiImpactMonteCarloLCA(fu, methods, iterations)

        st_dev_list = []
        mean_list = []
        mean_list_norm = []
        max_list_norm = []
        min_list_norm = []
        for i in range(0, len(test_results)):
            st_dev = np.std(test_results[i, :])
            st_dev_list.append(st_dev)
            mean = np.mean(test_results[i, :])
            mean_print = 100
            mean_list.append(mean)
            mean_list_norm.append(mean_print)
            maxi = mean + 2 * st_dev
            max_list_norm.append(maxi)
            minim = mean - 2 * st_dev
            min_list_norm.append(minim)

        list_results_MC = list(zip(dic["LCIA_unit"], mean_list, st_dev_list, max_list_norm, min_list_norm))
        results_df_MC = pd.DataFrame(list_results_MC, columns=["Unit", "Mean", "SD", "Max", "Min"])
        results_df_MC.index = dic["EI_name"]
        results_df_MC = results_df_MC.reset_index()
        results_df_MC = results_df_MC.rename(columns={"index": "Method"})
        results_df_MC.to_excel(os.path.join(dic["path_result_EI"], dic["directory"], dic["filename_result_EI_MC"]))
