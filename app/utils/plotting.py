"""PELCA (Power Electronics Life Cycle Assessment) is an open-source project aimed at assessing the environmental impact over the life cycle of modular and diagnosable power electronics systems. The integration of modularity and diagnosability aligns with circular economy principles, promoting practices such as repair and reuse. This project provides a tool to calculate the environmental impacts associated with the manufacturing, usage, and replacement of power electronics products.
Copyright (C) Mitsubishi Electric R&D Centre Europe and SATIE 2024, author Briac Baudais baudaisbriac@gmail.com

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this program.  If not, see https://www.gnu.org/licenses/lgpl-3.0.html"""

"""
Created on 2024

@author: baudais
"""
import ctypes
import math
import os
import tkinter as tk

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.subplots as sp


def get_screen_size():
    root = tk.Tk()
    root.withdraw()  # Cache la fenêtre principale
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    return screen_width, screen_height


def get_dpi_scaling():
    if os.name == "nt":  # Windows
        hdc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # 88 est le LOGPIXELSX
        ctypes.windll.user32.ReleaseDC(0, hdc)
        scaling_factor = dpi / 96.0  # 96 DPI est la référence pour 100% de mise à l'échelle
    else:  # Linux et autres systèmes
        root = tk.Tk()
        root.withdraw()  # Ne pas afficher la fenêtre
        dpi = root.winfo_fpixels("1i")  # Obtenir les pixels par pouce
        scaling_factor = dpi / 96.0  # 96 DPI est la référence pour 100% de mise à l'échelle
        root.destroy()  # Détruire la fenêtre après utilisation

    return scaling_factor


def adjust_figure_size(fig, ax):
    screen_width, screen_height = get_screen_size()
    scaling_factor = get_dpi_scaling()

    # Ajustement des dimensions de la figure en tenant compte de la mise à l'échelle
    fig_width = (screen_width / 210) / scaling_factor  # Adapter à la mise à l'échelle
    fig_height = (screen_height / 210) / scaling_factor
    fig.set_size_inches(fig_width, fig_height)


def adjust_fontsize(fig, ax):
    # Ajuster les tailles des polices en fonction de la taille de la figure
    fig_width, fig_height = fig.get_size_inches()
    base_font_size = min(fig_width, fig_height) * 2.5  # Ajustez ce coefficient selon vos besoins

    # Ajustement des éléments du graphique
    for item in [ax.title, ax.xaxis.label, ax.yaxis.label] + ax.get_xticklabels() + ax.get_yticklabels():
        item.set_fontsize(base_font_size)

    # Ajuster la taille des légendes
    if ax.get_legend() is not None:
        for legend in ax.get_legend().get_texts():
            legend.set_fontsize(base_font_size * 1)


def _decile(
    data,
    ax,
    var,
    display_decile,
    display_median,
    display_mean,
    display_max,
    display_legend,
    xlabel,
    ylabel,
    title,
    symlog=0,
    y_legend=1,
    xlog=False,
    ylim_min=0,
    x_legend=0.3,
):
    # Plot

    n_percentile = 10
    percent = np.linspace(0, 100 * (1 - 1 / n_percentile), n_percentile)[1:]
    n_ite = len(data)
    n_percentile = len(percent)
    n_var = len(var)
    data_plot = np.zeros((n_var, n_percentile))
    data_max = np.zeros((n_var))
    data_min = np.zeros((n_var))
    for k in range(n_var):
        data_plot[k] = np.percentile(data[k], percent)
        data_max[k] = np.max(data[k])
        data_min[k] = np.min(data[k])
    if display_decile:
        for k in range(n_percentile):
            fill = ax.fill_between(
                var, data_plot[:, k], data_plot[:, n_percentile - 1 - k], color="b", alpha=0.1, linewidth=0
            )
        fill.set_label("Decile")
    if display_median:
        ax.plot(var, data_plot[:, int(n_percentile / 2)], "b", alpha=0.7, label="Median")
    if display_mean:
        ax.plot(var, np.mean(data_plot, axis=1), "r", alpha=0.7, label="Mean")
    if xlog:
        ax.set_xscale("log")
    if display_max:
        ax.plot(var, data_min, "b--", alpha=0.2, label="min max")
        ax.plot(var, data_max, "b--", alpha=0.2)
    if symlog != 0:
        ax.set_yscale("symlog", linthresh=symlog)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: "{:g}".format(y)))

    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: "{:g}".format(y)))
    # ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel, rotation=0, ha="right", va="bottom")  # va="center" / "bottom"
    # ax.set_title(title)
    if display_legend:
        ax.legend(bbox_to_anchor=(x_legend, y_legend), loc="upper right")
    ax.set(xlim=(min(var), max(var)), ylim=(ylim_min, None))
    return ax





class PLOT:
    def __init__(self, dic, EI, EI_manu, EI_use, usage_time, fault_cause, nb_RU, nb_ite_MC, step, wcdf, EI_maintenance, impact_eco):
        self.fig4 = self.plot_selectEI(dic, EI, EI_manu, EI_use, usage_time, nb_RU, nb_ite_MC, step)
        self.fig5 = self.plot_allEI(dic, EI, EI_manu, EI_use, usage_time, nb_RU, nb_ite_MC, step)
        self.fig6 = self.plot_allEIatServicelife(dic, EI, EI_manu, EI_use, EI_maintenance, nb_RU, nb_ite_MC, step)
        self.eco = self.plot_selectEI_eco(dic, impact_eco['Total'], impact_eco['Manufacturing'], impact_eco['Use'], usage_time, nb_RU, nb_ite_MC, step)

        self.allEI_manufacturing = self.plot_allEI_manufacturing_plotly(dic, EI, EI_manu, EI_use, usage_time, nb_RU, nb_ite_MC, step)
        self.fig8 = self.plotCDF_plotly(wcdf, usage_time)
        self.fig9 = self.fault_repartition_plotly(dic, fault_cause)
        self.fig10 = self.plot_selectEI_plotly(dic, EI, EI_manu, EI_use, usage_time, nb_RU, nb_ite_MC, step)
        self.fig11 = self.plot_allEI_plotly(dic, EI, EI_manu, EI_use, usage_time, nb_RU, nb_ite_MC, step)
        self.fig12 = self.plot_allEIatServicelife_plotly(dic, EI, EI_manu, EI_use, EI_maintenance, nb_RU, nb_ite_MC, step)

        self.figs = [
            {
                "title" : "All EI Manufacturing",
                "plot": self.allEI_manufacturing,
                "type": "plotly"
            },
            {
                "title" : "CDF",
                "plot": self.fig8,
                "type": "plotly"
            },
            {
                "title" : "Fault Repartition",
                "plot": self.fig9,
                "type": "plotly"
            },
            # {
            #     "title" : "Select EI", 
            #     "plot": self.fig10,
            #     "type": "plotly"
            # },
            {
                "title" : "Select EI (Matplotlib)",
                "plot": self.fig4,
                "type": "matplotlib"
            },
            {
                "title" : "All EI",
                "plot": self.fig11,
                "type": "plotly"
            },
            {
                "title" : "All EI (Matplotlib)",
                "plot": self.fig5,
                "type": "matplotlib"
            },
            {
                "title" : "All EI at Service Life",
                "plot": self.fig12,
                "type": "plotly"
            },
            # {
            #     "title" : "All EI at Service Life (Matplotlib)",
            #     "plot": self.fig6,
            #     "type": "matplotlib"
            # },
            {
                "title" : "Economic Impact",
                "plot": self.eco,
                "type": "matplotlib"
            }
        ]

        
        
    def fault_repartition_plotly(self, dic, fault_cause):
        if dic["Wearout_failure"] == "False" and dic["Random_failure"] == "False" and dic["Early_failure"] == "False":
            # Afficher un message "no fault selected" si toutes les défaillances sont False
            fig = go.Figure()
            fig.add_trace(go.Pie(
                labels=["No fault selected"],
                values=[1],
                marker=dict(colors=["lightgrey"]),
                textinfo="label",
                showlegend=False
            ))

            fig.update_layout(
                title="No Fault Selected",
                title_x=0.5,
                title_font=dict(size=24)
            )
        else:
            # Données
            tableau_1d = fault_cause.flatten()
            count_early = np.sum(tableau_1d == "Early")
            count_random = np.sum(tableau_1d == "Random")
            count_wearout = np.sum(tableau_1d == "Wearout")
            nombres = [count_early, count_random, count_wearout]
            etiquettes = ["Early fault", "Random fault", "Wearout fault"]

            # Filtrer les valeurs nulles
            filtered_nombres = [n for n in nombres if n > 0]
            filtered_etiquettes = [label for n, label in zip(nombres, etiquettes) if n > 0]

            # Couleurs correspondantes
            couleurs = px.colors.qualitative.Plotly

            # Création du diagramme en camembert
            fig = go.Figure(data=[go.Pie(
                labels=filtered_etiquettes,
                values=filtered_nombres,
                marker=dict(colors=couleurs[:len(filtered_nombres)]),
                textinfo="label+percent",
                pull=[0.1] * len(filtered_nombres)  # Décaler légèrement les tranches pour l'effet visuel
            )])

            fig.update_layout(
                title="Distribution of Defects",
                title_x=0.5,
                title_font=dict(size=24),
                showlegend=False
            )

        return fig

    def plot_allEI_manufacturing_plotly(self, dic, EI, EI_manu, EI_use, usage_time, nb_RU, nb_ite_MC, step):
      
        excel = pd.ExcelFile(os.path.join(dic["LCA_path"], dic["filename_result_EI"]))

        # EI manufacturing of each RU
        self.EI_manufacturing = pd.read_excel(excel, sheet_name="Manufacturing", index_col=0)
        self.EI_manufacturing = self.EI_manufacturing.drop(columns=["Unit"])
        index_labels = self.EI_manufacturing.columns.to_numpy()
        self.EI_manufacturing = self.EI_manufacturing.to_numpy()

        # EI manufacturing of total RU
        self.EI_manufacturing_total = self.EI_manufacturing.sum(axis=1)
        normalized_EI_manu = self.EI_manufacturing * 100 / self.EI_manufacturing_total[:, np.newaxis]

        # Récupérer les noms des lignes
        line_names = dic["EI_name"]
        combined_labels = [f"{name} ({unit})" for name, unit in zip(line_names, dic["LCIA_unit"])]

        # Utilisation d'une colormap pour obtenir les couleurs
        colors = px.colors.qualitative.Plotly

        fig = go.Figure()

        # Barres empilées
        for j in range(len(index_labels)):
            fig.add_trace(
                go.Bar(
                    x=combined_labels,
                    y=normalized_EI_manu[:, j],
                    name=index_labels[j],
                    marker_color=colors[j % len(colors)],
                    text=[f"{val:.1e}" for val in self.EI_manufacturing[:, j]],
                    textposition="inside",
                )
            )

        fig.update_layout(
            barmode="stack",
            title="Manufacturing env. impact",
            xaxis_title="",
            yaxis_title="Normalized Value (%)",
            legend_title="",
            yaxis=dict(range=[0, 100]),
        )

        return fig
    
    def plot_selectEI_eco(self, dic, EI, EI_manu, EI_use, usage_time, nb_RU, nb_ite_MC, step):
        t = np.arange(0, usage_time, 1)
        result_MC = EI[:, :]
        result = EI[:, :]
        result_fab = EI_manu[:, :]
        result_use = EI_use[:,  :]

        if nb_ite_MC != 1:
            if result_MC.ndim == 1:
                result_MC = result_MC.reshape(1, -1)  # Transforme en tableau 2D si nécessaire
            result_MC = result_MC[:, result_MC[0, :].argsort()]
            result_MC = pd.DataFrame(result_MC)

        fig, ax = plt.subplots(1, 1)
        var = np.arange(result_MC.shape[0]) / step

        if nb_ite_MC > 1:
            ax = _decile(
                result_MC.T,
                ax,
                var,
                display_decile=True,
                display_median=True,
                display_mean=True,
                display_max=True,
                display_legend=True,
                xlabel=True,
                ylabel=True,
                title=False,
            )
        else:
            fab_use = pd.concat(
                [pd.DataFrame(result_fab.T, index=["Manufacturing"]).T, pd.DataFrame(result_use.T, index=["Use"]).T],
                axis=1,
            )
            w = 0.1
            ax.bar(var, fab_use["Manufacturing"], color=["blue"], width=w)
            ax.bar(var, fab_use["Use"], bottom=fab_use["Manufacturing"], color=["pink"], width=w)
            ax.plot(var, pd.DataFrame(result.T, index=["Total"]).T)
            ax.legend(["Total", "Manufacturing", "Use"], loc="upper left")

        # Appel à adjust_fontsize pour ajuster dynamiquement la taille des polices
        adjust_fontsize(fig, ax)

        # Ajuster les tailles des polices
        ax.set_ylabel("Cost/Price (€)", rotation=90)
        ax.set_xlabel("Time (years)")
        ax.grid(True)
        adjust_figure_size(fig, ax)
        return fig
    

    def plot_selectEI(self, dic, EI, EI_manu, EI_use, usage_time, nb_RU, nb_ite_MC, step):
        t = np.arange(0, usage_time, 1)
        result_MC = EI[:, :, dic["selected_EI"]]
        result = EI[:, :, dic["selected_EI"]]
        result_fab = EI_manu[:, :, dic["selected_EI"]]
        result_use = EI_use[:, :, dic["selected_EI"]]

        if nb_ite_MC != 1:
            result_MC = result_MC[:, result_MC[0, :].argsort()]
            result_MC = pd.DataFrame(result_MC)

        fig, ax = plt.subplots(1, 1)
        var = np.arange(result_MC.shape[0]) / step

        if nb_ite_MC > 1:
            ax = _decile(
                result_MC.T,
                ax,
                var,
                display_decile=True,
                display_median=True,
                display_mean=True,
                display_max=True,
                display_legend=True,
                xlabel=True,
                ylabel=True,
                title=False,
            )
        else:
            fab_use = pd.concat(
                [pd.DataFrame(result_fab.T, index=["Manufacturing"]).T, pd.DataFrame(result_use.T, index=["Use"]).T],
                axis=1,
            )
            w = 0.1
            ax.bar(var, fab_use["Manufacturing"], color=["blue"], width=w)
            ax.bar(var, fab_use["Use"], bottom=fab_use["Manufacturing"], color=["pink"], width=w)
            ax.plot(var, pd.DataFrame(result.T, index=["Total"]).T)
            ax.legend(["Total", "Manufacturing", "Use"], loc="upper left")

        # Appel à adjust_fontsize pour ajuster dynamiquement la taille des polices
        adjust_fontsize(fig, ax)

        # Ajuster les tailles des polices
        ax.set_ylabel(dic["EI_name"][dic["selected_EI"]], rotation=90)
        ax.set_xlabel("Time (years)")
        ax.grid(True)
        adjust_figure_size(fig, ax)
        return fig
    
    def plot_selectEI_plotly(self, dic, EI, EI_manu, EI_use, usage_time, nb_RU, nb_ite_MC, step):
        t = np.arange(0, usage_time, 1)
        result_MC = EI[:, :, dic["selected_EI"]]
        result = EI[:, :, dic["selected_EI"]]
        result_fab = EI_manu[:, :, dic["selected_EI"]]
        result_use = EI_use[:, :, dic["selected_EI"]]

        if nb_ite_MC != 1:
            result_MC = result_MC[:, result_MC[0, :].argsort()]
            result_MC = pd.DataFrame(result_MC)

        var = np.arange(result_MC.shape[0]) / step

        fig = go.Figure()

        if nb_ite_MC > 1:
            # Ajout des déciles et statistiques
            df = result_MC.T
            fig.add_trace(go.Scatter(
                x=var,
                y=df.median(axis=1),
                mode="lines",
                name="Median",
                line=dict(color="blue", width=2)
            ))
            fig.add_trace(go.Scatter(
                x=var,
                y=df.mean(axis=1),
                mode="lines",
                name="Mean",
                line=dict(color="green", width=2, dash="dash")
            ))
            fig.add_trace(go.Scatter(
                x=var,
                y=df.min(axis=1),
                mode="lines",
                name="Min",
                line=dict(color="red", width=1, dash="dot"),
                opacity=0.6
            ))
            fig.add_trace(go.Scatter(
                x=var,
                y=df.max(axis=1),
                mode="lines",
                name="Max",
                line=dict(color="purple", width=1, dash="dot"),
                opacity=0.6
            ))
        else:
            # Visualisation des données de fabrication et d'utilisation
            fab_use = pd.concat(
                [
                    pd.DataFrame(result_fab.T, index=["Manufacturing"]).T,
                    pd.DataFrame(result_use.T, index=["Use"]).T,
                ],
                axis=1,
            )
            fig.add_trace(go.Bar(
                x=var,
                y=fab_use["Manufacturing"],
                name="Manufacturing",
                marker_color="blue"
            ))
            fig.add_trace(go.Bar(
                x=var,
                y=fab_use["Use"],
                name="Use",
                marker_color="pink",
                base=fab_use["Manufacturing"]
            ))
            fig.add_trace(go.Scatter(
                x=var,
                y=result.sum(axis=0),
                mode="lines",
                name="Total",
                line=dict(color="black", width=2)
            ))

        # Mise en forme du graphique
        fig.update_layout(
            title="Impact environnemental : {}".format(dic["EI_name"][dic["selected_EI"]]),
            xaxis_title="Time (years)",
            yaxis_title=dic["EI_name"][dic["selected_EI"]],
            barmode="stack",
            template="plotly_white",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        return fig

    def plotCDF_plotly(self, wcdf, usage_time):
        import plotly.graph_objects as go

        t = np.arange(0, usage_time, 1)

        # Create a figure with the trace
        fig = go.Figure()

        # Add the CDF trace (line plot)
        fig.add_trace(go.Scatter(x=t, y=wcdf, mode="lines", line=dict(color="mediumvioletred", width=2)))

        # Update the layout (title, labels, etc.)
        fig.update_layout(
            title="Cumulative Distribution Function - All RU",
            xaxis_title="Time",
            yaxis_title="CDF",
            title_font=dict(size=16, family="Arial", color="black"),
            xaxis=dict(showgrid=True),
            yaxis=dict(showgrid=True),
            plot_bgcolor="white",  # Background color of the plot
        )

        fig.update_layout(
            xaxis=dict(
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=1
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=1
            )
        )
        
        return fig
    
    def plot_allEIatServicelife(self, dic, EI, EI_manu, EI_use, EI_maintenance, nb_RU, nb_ite_MC, step):
        # Charger les données à partir du fichier Excel
        excel = pd.ExcelFile(os.path.join(dic["LCA_path"], dic["filename_result_EI"]))

        # Lire les données de la feuille Manufacturing
        self.EI_manufacturing = pd.read_excel(excel, sheet_name="Manufacturing", index_col=0)
        self.EI_manufacturing = self.EI_manufacturing.drop(columns=["Unit"])
        self.EI_manufacturing = self.EI_manufacturing.to_numpy()
        self.EI_manufacturing = np.sum(self.EI_manufacturing, axis=1)

        # Calculer la moyenne des EI pour les autres catégories
        self.EI_use = np.mean(EI_use[dic["service_life"] - 1, :, :], axis=0)
        self.EI_maintenance = np.mean(EI_maintenance[dic["service_life"] - 1, :, :], axis=0)
        self.EI_replacement = (
            np.mean(EI_manu[dic["service_life"] - 1, :, :], axis=0) - self.EI_manufacturing - self.EI_maintenance
        )

        # Calculer le total des EI
        self.EI_total = np.mean(EI[dic["service_life"] - 1, :, :], axis=0)

        # Normaliser les valeurs
        normalized_EI_manu = self.EI_manufacturing * 100 / self.EI_total
        normalized_EI_use = self.EI_use * 100 / self.EI_total
        normalized_EI_replacement = self.EI_replacement * 100 / self.EI_total
        normalized_EI_maintenance = self.EI_maintenance * 100 / self.EI_total

        # Empiler les valeurs
        combined_EI = np.column_stack((self.EI_manufacturing, self.EI_use, self.EI_replacement, self.EI_maintenance))
        combined_normalized_EI = np.column_stack(
            (normalized_EI_manu, normalized_EI_use, normalized_EI_replacement, normalized_EI_maintenance)
        )

        # Création du graphique en barres empilées
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Nombre de lignes et colonnes pour les barres empilées
        num_rows = normalized_EI_manu.shape[0]
        num_columns = 4

        # Récupérer les noms des lignes
        line_names = dic["EI_name"]

        # Créer des étiquettes combinées
        combined_labels = [f"{name} ({unit})" for name, unit in zip(line_names, dic["LCIA_unit"])]

        # Utilisation d'une colormap pour les couleurs
        cmap = matplotlib.cm.get_cmap("tab20b")
        colors = [cmap(i) for i in np.linspace(0, 1, num_columns)]

        # Ajuster la taille des polices
        fig_width, fig_height = fig.get_size_inches()
        font_size = min(fig_width, fig_height) * 1.3

        # Tracer les barres empilées
        for i in range(num_rows):
            bottom = 0
            for j in range(num_columns):
                bar_color = colors[j % len(colors)]  # Utiliser les couleurs cycliquement
                ax.bar(i, combined_normalized_EI[i, j], color=bar_color, bottom=bottom)

                # Annotation pour chaque barre
                height = combined_normalized_EI[i, j]
                val = combined_EI[i, j]
                ax.text(
                    i,
                    bottom + height / 2,
                    f"{val:.1e}",
                    ha="center",
                    va="center",
                    fontsize=font_size,
                    color="black",
                    rotation=45,
                    bbox=dict(facecolor="white", alpha=0.5, edgecolor="none", boxstyle="round,pad=0.2"),
                )

                bottom += height

        # Configuration des axes
        ax.set_ylabel("Normalized Value (%)")
        ax.set_title(f'Total environmental impact at {dic["service_life"]} years (Mean)', weight="bold")
        ax.set_xticks(range(num_rows))
        ax.set_xticklabels(combined_labels, rotation=45, ha="right")
        ax.set_ylim(0, 100)
        ax.set_yticks(np.arange(0, 101, 10))
        ax.grid(True, axis="y", alpha=0.7)

        # Ajouter une légende
        index_labels = ["Manufacture", "Use", "Replacement", "Maintenance"]
        ax.legend(index_labels, loc="center left", bbox_to_anchor=(1, 0.5))

        return fig
    
    def plot_allEIatServicelife_plotly(self, dic, EI, EI_manu, EI_use, EI_maintenance, nb_RU, nb_ite_MC, step):
        # Charger les données à partir du fichier Excel
        excel = pd.ExcelFile(os.path.join(dic["LCA_path"], dic["filename_result_EI"]))

        # Lire et traiter les données de fabrication
        self.EI_manufacturing = pd.read_excel(excel, sheet_name="Manufacturing", index_col=0)
        self.EI_manufacturing = self.EI_manufacturing.drop(columns=["Unit"]).to_numpy()
        self.EI_manufacturing = np.sum(self.EI_manufacturing, axis=1)

        # Calculer les EI moyens pour d'autres catégories
        self.EI_use = np.mean(EI_use[dic["service_life"] - 1, :, :], axis=0)
        self.EI_maintenance = np.mean(EI_maintenance[dic["service_life"] - 1, :, :], axis=0)
        self.EI_replacement = (
            np.mean(EI_manu[dic["service_life"] - 1, :, :], axis=0) - self.EI_manufacturing - self.EI_maintenance
        )

        # Calculer le total des EI
        self.EI_total = np.mean(EI[dic["service_life"] - 1, :, :], axis=0)

        # Normaliser les valeurs
        normalized_EI_manu = self.EI_manufacturing * 100 / self.EI_total
        normalized_EI_use = self.EI_use * 100 / self.EI_total
        normalized_EI_replacement = self.EI_replacement * 100 / self.EI_total
        normalized_EI_maintenance = self.EI_maintenance * 100 / self.EI_total

        # Combiner les valeurs pour les barres empilées
        combined_EI = np.column_stack((self.EI_manufacturing, self.EI_use, self.EI_replacement, self.EI_maintenance))
        combined_normalized_EI = np.column_stack(
            (normalized_EI_manu, normalized_EI_use, normalized_EI_replacement, normalized_EI_maintenance)
        )

        # Labels pour les barres
        categories = ["Manufacturing", "Use", "Replacement", "Maintenance"]
        labels = [f"{name} ({unit})" for name, unit in zip(dic["EI_name"], dic["LCIA_unit"])]

        # Création du graphique interactif
        fig = go.Figure()

        for i, category in enumerate(categories):
            fig.add_trace(go.Bar(
                x=labels,
                y=combined_normalized_EI[:, i],
                name=category,
                text=[f"{val:.1e}" for val in combined_EI[:, i]],  # Valeurs affichées
                textposition="inside",
                hoverinfo="text",
            ))

        # Mise en forme du graphique
        fig.update_layout(
            barmode="stack",
            title=f"Total Environmental Impact at {dic['service_life']} years (Mean)",
            xaxis=dict(title="Environmental Impact Categories", tickangle=-45),
            yaxis=dict(title="Normalized Value (%)", range=[0, 100]),
            legend=dict(title="Categories", orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            template="plotly_white",
        )

        # Retourne la figure Plotly
        return fig
    




    def plot_allEI(self, dic, EI, EI_manu, EI_use, usage_time, nb_RU, nb_ite_MC, step):
        methods = dic["EI_name"]

        number_of_EI = len(dic["EI_name"])

        EI_plot = [[[1 for y in range(usage_time)] for y in range(nb_RU)] for z in range(nb_ite_MC)]
        # result=[[1 for y in range(usage_time)] for z in range(nb_ite_MC)]
        t = np.arange(0, usage_time, 1)

        column, row = nb_ite_MC, usage_time
        result_MC = np.ones((row, column, number_of_EI))
        result = np.ones((column, row, number_of_EI))
        result_fab = np.ones((column, row, number_of_EI))
        result_use = np.ones((column, row, number_of_EI))

        #
        result_MC = EI[:, :, :]
        result = EI[:, :, :]
        result_fab = EI_manu[:, :, :]
        result_use = EI_use[:, :, :]

        row_fig = 0
        col_fig = 0

        # Calculer le nombre de lignes et de colonnes pour une grille carrée
        num_cols = int(math.ceil(math.sqrt(number_of_EI)))
        num_rows = int(math.ceil(number_of_EI / num_cols))

        # Créer les sous-graphiques
        fig, ax = plt.subplots(num_rows, num_cols, figsize=(10, 5), sharex=True)

        # Si num_rows ou num_cols est 1, axs peut être un tableau 1D ou 2D
        if num_rows == 1 or num_cols == 1:
            ax = np.reshape(ax, (num_rows, num_cols))  # Redimensionner en tableau 2D

        plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9, wspace=0.35, hspace=0.4)
        fig.add_subplot(111, frameon=False)
        # hide tick and tick label of the big axis

        for EI in range(number_of_EI):
            result_MC_EI = pd.DataFrame(result_MC[:, :, EI])

            if nb_ite_MC > 1:
                var = np.arange(result_MC_EI.shape[0]) / step
                ax[row_fig, col_fig] = _decile(
                    result_MC_EI.T,
                    ax[row_fig, col_fig],
                    var,
                    display_decile=True,
                    display_median=True,
                    display_mean=True,
                    display_max=True,
                    display_legend=False,
                    xlabel=True,
                    ylabel=False,
                    title=False,
                )
                ax[row_fig, col_fig].ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
                ax[row_fig, col_fig].set_title(methods[EI])
                ax[row_fig, col_fig].grid(True)
            if nb_ite_MC == 1:
                ax[row_fig, col_fig].ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
                ax[row_fig, col_fig].set_title(methods[EI])
                ax[row_fig, col_fig].grid(True)
                # ax=result.plot(kind='line',legend=False)
                # plt.figure()
                var = np.arange(result.shape[0]) / step
                w = 0.1
                ax[row_fig, col_fig].bar(var, result_fab[:, 0, EI].T, color=["blue"], width=w)
                ax[row_fig, col_fig].bar(
                    var, result_use[:, 0, EI].T, bottom=result_fab[:, 0, EI].T, color=["pink"], width=w
                )
                ax[row_fig, col_fig].plot(var, result[:, 0, EI].T)
                # ax[row_fig,col_fig].legend(['Total','Manufacturing','Use'])
                if EI == 0:
                    ax[row_fig, col_fig].legend(
                        ["Total", "Manufacturing", "Use"], bbox_to_anchor=(2.5, 1.30), loc="center", ncol=3
                    )
            col_fig = col_fig + 1
            if col_fig == 4:
                col_fig = 0
                row_fig = row_fig + 1

        # Appel à adjust_fontsize pour ajuster dynamiquement la taille des polices
        # adjust_fontsize(fig, ax)

        plt.tick_params(labelcolor="none", which="both", top=False, bottom=False, left=False, right=False)
        plt.xlabel("Time (years)", fontsize=14)

        screen_width, screen_height = get_screen_size()
        scaling_factor = get_dpi_scaling()

        # Ajustement des dimensions de la figure
        fig_width = (screen_width / 210) / scaling_factor  # Ajustez ces valeurs pour une taille plus adaptée
        fig_height = (screen_height / 150) / scaling_factor
        fig.set_size_inches(fig_width, fig_height)
        return fig
    




    def plot_allEI_plotly(self, dic, EI, EI_manu, EI_use, usage_time, nb_RU, nb_ite_MC, step):
        methods = dic["EI_name"]
        number_of_EI = len(methods)

        # Préparer les données pour les graphiques
        result_MC = EI[:, :, :]
        result_fab = EI_manu[:, :, :]
        result_use = EI_use[:, :, :]

        # Créer une figure avec des sous-graphiques
        num_cols = 4  # Nombre de colonnes dans la grille
        num_rows = math.ceil(number_of_EI / num_cols)  # Nombre de lignes dans la grille
        fig = sp.make_subplots(rows=num_rows, cols=num_cols, subplot_titles=methods)

        for EI_index in range(number_of_EI):
            row = (EI_index // num_cols) + 1
            col = (EI_index % num_cols) + 1

            result_MC_EI = pd.DataFrame(result_MC[:, :, EI_index])
            var = np.arange(result_MC_EI.shape[0]) / step

            if nb_ite_MC > 1:
                # Calcul des statistiques (médiane, déciles, etc.)
                mean_vals = result_MC_EI.mean(axis=1)
                median_vals = result_MC_EI.median(axis=1)
                min_vals = result_MC_EI.min(axis=1)
                max_vals = result_MC_EI.max(axis=1)

                # Ajouter les graphiques pour Mean, Min, Max, et Median
                fig.add_trace(
                    go.Scatter(
                        x=var, y=mean_vals, mode="lines", name="Mean",
                        line=dict(color="blue"),
                        hovertemplate="<b>Mean</b>: %{y:.2e}<br><b>Time</b>: %{x} years<extra></extra>",
                        showlegend=(EI_index == 0),  # Montrer la légende une seule fois
                        legendgroup="mean"  # Groupe "mean"
                    ),
                    row=row, col=col
                )

                fig.add_trace(
                    go.Scatter(
                        x=var, y=min_vals, mode="lines", name="Min",
                        line=dict(dash="dot", color="lightblue"),
                        hovertemplate="<b>Min</b>: %{y:.2e}<br><b>Time</b>: %{x} years<extra></extra>",
                        showlegend=(EI_index == 0),  # Montrer la légende une seule fois
                        legendgroup="min"  # Groupe "min"
                    ),
                    row=row, col=col
                )

                fig.add_trace(
                    go.Scatter(
                        x=var, y=max_vals, mode="lines", name="Max",
                        line=dict(dash="dot", color="lightblue"),
                        hovertemplate="<b>Max</b>: %{y:.2e}<br><b>Time</b>: %{x} years<extra></extra>",
                        showlegend=(EI_index == 0),  # Montrer la légende une seule fois
                        legendgroup="max"  # Groupe "max"
                    ),
                    row=row, col=col
                )

                fig.add_trace(
                    go.Scatter(
                        x=var, y=median_vals, mode="lines", name="Median",
                        line=dict(color="green"),
                        hovertemplate="<b>Median</b>: %{y:.2e}<br><b>Time</b>: %{x} years<extra></extra>",
                        showlegend=(EI_index == 0),  # Montrer la légende une seule fois
                        legendgroup="median"  # Groupe "median"
                    ),
                    row=row, col=col
                )

            if nb_ite_MC == 1:
                # Empilage Manufacturing et Use
                fig.add_trace(
                    go.Bar(
                        x=var, y=result_fab[:, 0, EI_index], name=f"Manufacturing ({methods[EI_index]})",
                        marker_color="blue",
                        hovertemplate="<b>Manufacturing</b>: %{y:.2e}<br><b>Time</b>: %{x} years<extra></extra>"
                    ),
                    row=row, col=col
                )

                fig.add_trace(
                    go.Bar(
                        x=var, y=result_use[:, 0, EI_index], name=f"Use ({methods[EI_index]})",
                        marker_color="pink",
                        base=result_fab[:, 0, EI_index],
                        hovertemplate="<b>Use</b>: %{y:.2e}<br><b>Time</b>: %{x} years<extra></extra>"
                    ),
                    row=row, col=col
                )

                fig.add_trace(
                    go.Scatter(
                        x=var, y=result_MC[:, 0, EI_index], mode="lines", name=f"Total ({methods[EI_index]})",
                        line=dict(color="black", width=2),
                        hovertemplate="<b>Total</b>: %{y:.2e}<br><b>Time</b>: %{x} years<extra></extra>"
                    ),
                    row=row, col=col
                )

        # Configuration générale des axes et du titre
        fig.update_layout(
            title="Environmental Impact Over Time",
            xaxis_title="Time (years)",
            yaxis_title="Environmental Impact",
            barmode="stack",
            legend=dict(x=1.05, y=1),
            template="plotly_white",
            autosize=True
        )

        for i in range(1, num_rows + 1):
            for j in range(1, num_cols + 1):
                fig.update_xaxes(title_text="Time (years)", row=i, col=j)
                # fig.update_yaxes(title_text="Environmental Impact", row=i, col=j)
        return fig



    def fault_repartition(self, dic, fault_cause):
        if dic["Wearout_failure"] == "False" and dic["Random_failure"] == "False" and dic["Early_failure"] == "False":
            # Afficher un message "no fault selected" si toutes les défaillances sont False
            fig, ax = plt.subplots()
            ax.pie([1], colors=["lightgrey"])
            ax.text(0.5, 0.5, "No fault selected", fontsize=24, ha="center", va="center")
            ax.axis("off")  # Masquer les axes pour un affichage plus propre

        else:
            # Données
            tableau_1d = fault_cause.flatten()
            count_early = np.sum(tableau_1d == "Early")
            count_random = np.sum(tableau_1d == "Random")
            count_wearout = np.sum(tableau_1d == "Wearout")
            nombres = [count_early, count_random, count_wearout]
            etiquettes = ["Early fault", "Random fault", "Wearout fault"]

            # Couleurs correspondantes
            couleurs = plt.cm.tab20c(range(3))

            # Filter out zero values
            filtered_nombres = [n for n in nombres if n > 0]
            filtered_etiquettes = [label for n, label in zip(nombres, etiquettes) if n > 0]

            # Corresponding colors
            couleurs = plt.cm.tab20c(range(3))

            # Filter colors based on filtered_nombres
            filtered_couleurs = [color for n, color in zip(nombres, couleurs) if n > 0]

            # Création du diagramme en camembert
            fig, ax = plt.subplots()
            ax.pie(
                filtered_nombres,
                labels=filtered_etiquettes,
                autopct="%1.1f%%",
                startangle=140,
                colors=filtered_couleurs,
                labeldistance=1.05,
                pctdistance=0.85,
            )

            # Ajout d'un titre avec une taille de police plus grande
            ax.set_title("Distribution of defects", weight="bold")

            # Appel à adjust_fontsize pour ajuster dynamiquement la taille des polices
            # adjust_fontsize(fig, ax)

            adjust_figure_size(fig, ax)
            adjust_fontsize(fig, ax)
        return fig
    
    def plot_allEIatServicelife(self, dic, EI, EI_manu, EI_use, EI_maintenance, nb_RU, nb_ite_MC, step):
        # Charger les données à partir du fichier Excel
        excel = pd.ExcelFile(os.path.join(dic["LCA_path"], dic["filename_result_EI"]))

        # Lire les données de la feuille Manufacturing
        self.EI_manufacturing = pd.read_excel(excel, sheet_name="Manufacturing", index_col=0)
        self.EI_manufacturing = self.EI_manufacturing.drop(columns=["Unit"])
        self.EI_manufacturing = self.EI_manufacturing.to_numpy()
        self.EI_manufacturing = np.sum(self.EI_manufacturing, axis=1)

        # Calculer la moyenne des EI pour les autres catégories
        self.EI_use = np.mean(EI_use[dic["service_life"] - 1, :, :], axis=0)
        self.EI_maintenance = np.mean(EI_maintenance[dic["service_life"] - 1, :, :], axis=0)
        self.EI_replacement = (
            np.mean(EI_manu[dic["service_life"] - 1, :, :], axis=0) - self.EI_manufacturing - self.EI_maintenance
        )

        # Calculer le total des EI
        self.EI_total = np.mean(EI[dic["service_life"] - 1, :, :], axis=0)

        # Normaliser les valeurs
        normalized_EI_manu = self.EI_manufacturing * 100 / self.EI_total
        normalized_EI_use = self.EI_use * 100 / self.EI_total
        normalized_EI_replacement = self.EI_replacement * 100 / self.EI_total
        normalized_EI_maintenance = self.EI_maintenance * 100 / self.EI_total

        # Empiler les valeurs
        combined_EI = np.column_stack((self.EI_manufacturing, self.EI_use, self.EI_replacement, self.EI_maintenance))
        combined_normalized_EI = np.column_stack(
            (normalized_EI_manu, normalized_EI_use, normalized_EI_replacement, normalized_EI_maintenance)
        )

        # Création du graphique en barres empilées
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Nombre de lignes et colonnes pour les barres empilées
        num_rows = normalized_EI_manu.shape[0]
        num_columns = 4

        # Récupérer les noms des lignes
        line_names = dic["EI_name"]

        # Créer des étiquettes combinées
        combined_labels = [f"{name} ({unit})" for name, unit in zip(line_names, dic["LCIA_unit"])]

        # Utilisation d'une colormap pour les couleurs
        cmap = matplotlib.cm.get_cmap("tab20b")
        colors = [cmap(i) for i in np.linspace(0, 1, num_columns)]

        # Ajuster la taille des polices
        fig_width, fig_height = fig.get_size_inches()
        font_size = min(fig_width, fig_height) * 1.3

        # Tracer les barres empilées
        for i in range(num_rows):
            bottom = 0
            for j in range(num_columns):
                bar_color = colors[j % len(colors)]  # Utiliser les couleurs cycliquement
                ax.bar(i, combined_normalized_EI[i, j], color=bar_color, bottom=bottom)

                # Annotation pour chaque barre
                height = combined_normalized_EI[i, j]
                val = combined_EI[i, j]
                ax.text(
                    i,
                    bottom + height / 2,
                    f"{val:.1e}",
                    ha="center",
                    va="center",
                    fontsize=font_size,
                    color="black",
                    rotation=45,
                    bbox=dict(facecolor="white", alpha=0.5, edgecolor="none", boxstyle="round,pad=0.2"),
                )

                bottom += height

        # Configuration des axes
        ax.set_ylabel("Normalized Value (%)")
        ax.set_title(f'Total environmental impact at {dic["service_life"]} years (Mean)', weight="bold")
        ax.set_xticks(range(num_rows))
        ax.set_xticklabels(combined_labels, rotation=45, ha="right")
        ax.set_ylim(0, 100)
        ax.set_yticks(np.arange(0, 101, 10))
        ax.grid(True, axis="y", alpha=0.7)

        # Ajouter une légende
        index_labels = ["Manufacture", "Use", "Replacement", "Maintenance"]
        ax.legend(index_labels, loc="center left", bbox_to_anchor=(1, 0.5))

        return fig
    

    def plot_allEIatServicelife_plotly(self, dic, EI, EI_manu, EI_use, EI_maintenance, nb_RU, nb_ite_MC, step):
        # Charger les données à partir du fichier Excel
        excel = pd.ExcelFile(os.path.join(dic["LCA_path"], dic["filename_result_EI"]))

        # Lire les données de la feuille Manufacturing
        self.EI_manufacturing = pd.read_excel(excel, sheet_name="Manufacturing", index_col=0)
        self.EI_manufacturing = self.EI_manufacturing.drop(columns=["Unit"])
        self.EI_manufacturing = self.EI_manufacturing.to_numpy()
        self.EI_manufacturing = np.sum(self.EI_manufacturing, axis=1)

        # Calculer la moyenne des EI pour les autres catégories
        self.EI_use = np.mean(EI_use[dic["service_life"] - 1, :, :], axis=0)
        self.EI_maintenance = np.mean(EI_maintenance[dic["service_life"] - 1, :, :], axis=0)
        self.EI_replacement = (
            np.mean(EI_manu[dic["service_life"] - 1, :, :], axis=0) - self.EI_manufacturing - self.EI_maintenance
        )

        # Calculer le total des EI
        self.EI_total = np.mean(EI[dic["service_life"] - 1, :, :], axis=0)

        # Normaliser les valeurs
        normalized_EI_manu = self.EI_manufacturing * 100 / self.EI_total
        normalized_EI_use = self.EI_use * 100 / self.EI_total
        normalized_EI_replacement = self.EI_replacement * 100 / self.EI_total
        normalized_EI_maintenance = self.EI_maintenance * 100 / self.EI_total

        # Empiler les valeurs
        combined_EI = np.column_stack((self.EI_manufacturing, self.EI_use, self.EI_replacement, self.EI_maintenance))
        combined_normalized_EI = np.column_stack(
            (normalized_EI_manu, normalized_EI_use, normalized_EI_replacement, normalized_EI_maintenance)
        )

        # Récupérer les noms des lignes
        line_names = dic["EI_name"]
        combined_labels = [f"{name} ({unit})" for name, unit in zip(line_names, dic["LCIA_unit"])]

        # Couleurs personnalisées
        colors = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA"]  # Plotly "standard" palette
        index_labels = ["Manufacture", "Use", "Replacement", "Maintenance"]

        # Initialisation de la figure Plotly
        fig = go.Figure()

        # Ajouter les traces pour chaque catégorie
        for idx, label in enumerate(index_labels):
            fig.add_trace(
                go.Bar(
                    name=label,
                    x=combined_labels,
                    y=combined_normalized_EI[:, idx],
                    text=[f"{val:.1e}" for val in combined_EI[:, idx]],
                    textposition="inside",
                    marker=dict(color=colors[idx]),
                    hoverinfo="x+y+text",
                )
            )

        # Mise en page
        fig.update_layout(
            barmode="stack",
            title=f"Total environmental impact at {dic['service_life']} years (Mean)",
            xaxis=dict(title="Environmental Indicators", tickangle=45),
            yaxis=dict(title="Normalized Value (%)", range=[0, 100]),
            legend=dict(title="Categories"),
            template="plotly_white",
        )

        return fig

