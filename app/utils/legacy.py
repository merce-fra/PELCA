"""PELCA (Power Electronics Life Cycle Assessment) is an open-source project aimed at assessing the environmental impact over the life cycle of modular and diagnosable power electronics systems. The integration of modularity and diagnosability aligns with circular economy principles, promoting practices such as repair and reuse. This project provides a tool to calculate the environmental impacts associated with the manufacturing, usage, and replacement of power electronics products.
Copyright (C) Mitsubishi Electric R&D Centre Europe and SATIE 2024, author Briac Baudais baudaisbriac@gmail.com

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this program.  If not, see https://www.gnu.org/licenses/lgpl-3.0.html"""

"""
Created on 2024

@author: baudais, bdubus
"""

import os

import numpy as np
import pandas as pd


def get_max_fig_size(figs):
    """Retourne la taille de la plus grande figure"""
    max_width = 0
    max_height = 0
    for fig in figs:
        fig_width, fig_height = fig.get_size_inches() * fig.dpi
        max_width = max(max_width, fig_width)
        max_height = max(max_height, fig_height)
    return (int(max_width), int(max_height))


def export_data(path, file_name, file):
    """Exports a file in numpy format"""

    file_name_pickle = file_name + ".npy"
    path_file_pickle = os.path.join(path, "", file_name_pickle)
    with open(path_file_pickle, "wb") as f:
        np.save(f, file)


def export_data_excel(folder_path, file_name, data):
    """
    Exports data to an Excel file after handling dimensions.

    Args:
        folder_path (str): Path to the folder where the file will be saved.
        file_name (str): Name of the Excel file (without extension).
        data (numpy.ndarray, list, or pd.DataFrame): The data to export.

    Returns:
        None
    """
    # Create the full path for the Excel file
    file_path = os.path.join(folder_path, f"{file_name}.xlsx")
    
    # Prepare the data for export
    if isinstance(data, (np.ndarray, list)):
        data = np.array(data)  # Convert to NumPy array if necessary
        if len(data.shape) > 2:  # Reduce dimensions if 3D or more
            data = data.reshape(data.shape[0], -1)  # Combine dimensions after the first
        df = pd.DataFrame(data)  # Convert to Pandas DataFrame
    elif isinstance(data, pd.DataFrame):
        df = data
    else:
        raise ValueError("Data must be a NumPy array, a list, or a Pandas DataFrame.")
    
    # Create the directory if necessary
    os.makedirs(folder_path, exist_ok=True)
    
    # Export to Excel
    try:
        df.to_excel(file_path, index=False)
        print(f"File successfully exported: {file_path}")
    except Exception as e:
        print(f"Error exporting data: {e}")
