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
    """Exporte un fichier au format numpy"""

    file_name_pickel = file_name + ".npy"
    path_file_pickel = os.path.join(path, "", file_name_pickel)
    with open(path_file_pickel, "wb") as f:
        np.save(f, file)


def export_data_excel(path, file_name, file):
    """Exporte un fichier au format excel"""

    file_name_excel = file_name + ".xlsx"
    path_file_excel = os.path.join(path, "", file_name_excel)
    with pd.ExcelWriter(path_file_excel) as writer:
        if isinstance(file, np.ndarray):
            df = pd.DataFrame(file)
            df.to_excel(writer, sheet_name='Sheet1')
        elif isinstance(file, dict):
            for key, value in file.items():
                if isinstance(value, np.ndarray):
                    df = pd.DataFrame(value)
                    df.to_excel(writer, sheet_name=key)
                else:
                    value.to_excel(writer, sheet_name=key)
    print(f"Data saved to {path_file_excel}")









