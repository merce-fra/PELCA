import os

import numpy as np


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
    file_name_pickel = file_name + ".npy"
    path_file_pickel = os.path.join(path, "", file_name_pickel)
    with open(path_file_pickel, "wb") as f:
        np.save(f, file)
