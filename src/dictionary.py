"""PELCA (Power Electronics Life Cycle Assessment) is an open-source project aimed at assessing the environmental impact over the life cycle of modular and diagnosable power electronics systems. The integration of modularity and diagnosability aligns with circular economy principles, promoting practices such as repair and reuse. This project provides a tool to calculate the environmental impacts associated with the manufacturing, usage, and replacement of power electronics products.
Copyright (C) 2024 Briac Baudais baudaisbriac@gmail.com

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this program.  If not, see https://www.gnu.org/licenses/lgpl-3.0.html"""

"""
Created on 2024

@author: baudais
"""

import numpy as np
import pandas as pd
import os
import csv
import shutil
import pickle
  
def _init_dir(path,directory):
      
    # Create the directory
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)
    print("Directory '% s' created" % directory)
      
#%% Init  
def _init_dic(path_input,name_input):
    #%%
    
    excel = pd.ExcelFile(os.path.join(path_input,name_input))
    df = pd.read_excel(excel, sheet_name='LCA', header=None, skiprows=1)
    df_LCIA = pd.read_excel(excel, sheet_name='LCIA', header=0, skiprows=1)
    df_stair = pd.read_excel(excel, sheet_name='Staircase', header=None, skiprows=1)
    df_RM = pd.read_excel(excel, sheet_name='Replac. Matrix', header=None, skiprows=[0,1,2,3], usecols=lambda x: x != 0)
    excel.close()
    dic = {}
    ##################### Used to create the test case #####################
    # dic[""] = 
    
    #%% LCA
    dic["path_result_EI"] =df.iloc[df[df.isin(['LCA result path']).any(axis=1)].index[0], 1]
    dic["filename_result_EI"] =df.iloc[df[df.isin(['LCA result filename']).any(axis=1)].index[0], 1]
    dic["filename_result_EI_MC"] =df.iloc[df[df.isin(['LCA Monte Carlo result filename']).any(axis=1)].index[0], 1]
    
    dic["simulation"] =df.iloc[df[df.isin(['Type of simulation (Analysis\Monte Carlo)']).any(axis=1)].index[0], 1]
    
    dic["directory"] ="Results PELCA"
    dic["LCA_path"] =os.path.join(dic["path_result_EI"],dic["directory"])
    path = os.path.join(path_input, dic["directory"])
    
    if dic["simulation"] == "Analysis":
        file_path=os.path.join(dic["path_result_EI"],dic["directory"],dic["filename_result_EI"])
    elif dic["simulation"] == "Monte Carlo":
        file_path=os.path.join(dic["path_result_EI"],dic["directory"],dic["filename_result_EI_MC"])
    
    if os.path.exists(file_path):
         print("LCA is already calculated.")
         dic["LCA"]='no'
         excel = pd.ExcelFile(file_path)
         df_result = pd.read_excel(excel, header=0)
         excel.close()
         dic["EI_name"] = df_result['Method'].tolist()
         dic["LCIA_unit"] = df_result['Unit'].tolist()
    else:
         print("LCA not yet calculated.")
         dic["LCA"]='yes'
         _init_dir(dic["LCA_path"],dic["directory"])
         
         dic["database_ecoinvent"] =df.iloc[df[df.isin(['Database ecoinvent']).any(axis=1)].index[0], 1]
         dic["database_ecoinvent_path"]=df.iloc[df[df.isin(['Ecoinvent path']).any(axis=1)].index[0], 1]
         dic["inventory_name"] =df.iloc[df[df.isin(['Inventory name']).any(axis=1)].index[0], 1]
         dic["proj_name"] =df.iloc[df[df.isin(['Project name (brightway)']).any(axis=1)].index[0], 1]
         dic["iterations"] =df.iloc[df[df.isin(['Number of iterations (Monte Carlo)']).any(axis=1)].index[0], 1]        
         
         dic["EI_name"] = df_LCIA['Acronym'].tolist()
         dic["LCIA_unit"] = df_LCIA['Unit'].tolist()
         dic["LCIA"] = df_LCIA

    #%% Operating cycle
    
    dic["service_life"] = df_stair.iloc[df_stair[df_stair.isin(['Service life (year)']).any(axis=1)].index[0], 1]
    dic["num_hourPerYear"] =df_stair.iloc[df_stair[df_stair.isin(['Annual usage time (hours/year)']).any(axis=1)].index[0], 1]
    dic["step"] =df_stair.iloc[df_stair[df_stair.isin(['Time step (step/year)']).any(axis=1)].index[0], 1]
    
    #%% Staircase curve
  
    # Monte carlo
    dic["nb_ite_MC"] =df_stair.iloc[df_stair[df_stair.isin(['Monte Carlo (number of iteration)']).any(axis=1)].index[0], 1]

    # Select type of fault
    dic["Early_failure"]=df_stair.iloc[df_stair[df_stair.isin(['Early failure']).any(axis=1)].index[0], 1]
    dic["Random_failure"]=df_stair.iloc[df_stair[df_stair.isin(['Early failure']).any(axis=1)].index[0], 1]
    dic["Wearout_failure"]=df_stair.iloc[df_stair[df_stair.isin(['Early failure']).any(axis=1)].index[0], 1]
    
    dic["pre_set_fail"]=False
    
    # Replacement rate, replacement matrix
    
    dic["Remplacement_matrix"] = df_RM
    
    #plot
    dic["selected_EI"]=df_stair.iloc[df_stair[df_stair.isin(['Plot specific env. impact']).any(axis=1)].index[0], 1]-1
    #%% Saving dictionary

    # Path
    file_name='dict_file.csv'
    path_file = os.path.join(dic["LCA_path"],file_name)
    file_name_pickel='dict_file.pkl'
    path_file_pickel = os.path.join(dic["LCA_path"],file_name_pickel)
    
    #save csv
    with open(path_file, 'w') as csv_file:  
        writer = csv.writer(csv_file)
        for key, value in dic.items():
            writer.writerow([key, value])
    
    #save pickel
    with open(path_file_pickel, 'wb') as fp:
        pickle.dump(dic, fp)
    print('dictionary saved successfully to file')

    #how to open
    # with open(path_file_pickel, 'rb') as fp:
    #     dic = pickle.load(fp)
    
    return dic