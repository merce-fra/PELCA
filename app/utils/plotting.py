"""PELCA (Power Electronics Life Cycle Assessment) is an open-source project aimed at assessing the environmental impact over the life cycle of modular and diagnosable power electronics systems. The integration of modularity and diagnosability aligns with circular economy principles, promoting practices such as repair and reuse. This project provides a tool to calculate the environmental impacts associated with the manufacturing, usage, and replacement of power electronics products.
Copyright (C) Mitsubishi Electric R&D Centre Europe and SATIE 2024, author Briac Baudais baudaisbriac@gmail.com

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this program.  If not, see https://www.gnu.org/licenses/lgpl-3.0.html"""

"""
Created on 2024

@author: baudais
"""
import math
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp

class PLOT:
    def __init__(self, dic, EI, EI_manu, EI_use, usage_time, fault_cause, nb_RU, nb_ite_MC, step, wcdf, wcdf_per_RU, EI_maintenance, impact_eco): #added wcdf_per_RU
        
        self.allEI_manufacturing = self.plot_allEI_manufacturing_plotly(dic, EI, EI_manu, EI_use, usage_time, nb_RU, nb_ite_MC, step)
        self.fig8 = self.plotCDF_plotly(dic, wcdf, wcdf_per_RU, usage_time,step)
        self.fig9 = self.fault_repartition_plotly(dic, fault_cause)
        self.fig10 = self.plot_selectEI_plotly(dic, EI, EI_manu, EI_use, usage_time, nb_RU, nb_ite_MC, step)
        self.fig11 = self.plot_allEI_plotly(dic, EI, EI_manu, EI_use, usage_time, nb_RU, nb_ite_MC, step)
        self.fig12 = self.plot_allEIatServicelife_plotly(dic, EI, EI_manu, EI_use, EI_maintenance, nb_RU, nb_ite_MC, step)
        self.eco_plotly = self.plot_selectEI_eco_plotly(dic, impact_eco['Total'], impact_eco['Manufacturing'], impact_eco['Use'], usage_time, nb_RU, nb_ite_MC, step)

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
            {
                "title" : "Select EI", 
                "plot": self.fig10,
                "type": "plotly"
            },
            {
                "title" : "All EI",
                "plot": self.fig11,
                "type": "plotly"
            },
            {
                "title" : "All EI at Service Life",
                "plot": self.fig12,
                "type": "plotly"
            },
            {
                "title" : "Economic Impact",
                "plot": self.eco_plotly,
                "type": "plotly"
            },
        ]


    def plot_selectEI_eco_plotly(self, dic, EI, EI_manu, EI_use, usage_time, nb_RU, nb_ite_MC, step):
        t = np.arange(0, usage_time, 1)
        result_MC = EI[:, :]
        result = EI[:, :]
        result_fab = EI_manu[:, :]
        result_use = EI_use[:, :]

        fig = go.Figure()

        if nb_ite_MC > 1:
            # Calcul des déciles, min, max, médiane et moyenne
            percentiles = np.percentile(result_MC, [10, 20, 30, 40, 50, 60, 70, 80, 90], axis=1)
            median = np.percentile(result_MC, 50, axis=1)
            mean = np.mean(result_MC, axis=1)
            min_values = np.min(result_MC, axis=1)
            max_values = np.max(result_MC, axis=1)

            # Edit(AEP): np.arange(result_MC.shape[0]) equals the total number of steps
            # np.arange(result_MC.shape[0]) / step is a list of years (can contain fractions of years e.g. 3.4years)
            var = np.arange(result_MC.shape[0]) / step

            # Ajouter les bandes des déciles
            fig.add_trace(go.Scatter(
                x=var,
                y=percentiles[0],
                mode='lines',
                line=dict(width=0),
                fillcolor="rgba(0, 0, 255, 0.1)",
                showlegend=False
            ))
            for i in range(0,len(percentiles) // 2):
                fig.add_trace(go.Scatter(
                    x=var,
                    y=percentiles[i],
                    mode='lines',
                    fill='tonextx',
                    line=dict(width=0),
                    fillcolor="rgba(0, 0, 255, 0.1)",
                    showlegend=False
                ))
                fig.add_trace(go.Scatter(
                    x=var,
                    y=percentiles[-(i+1)],
                    mode='lines',
                    fill='tonextx',
                    line=dict(width=0),
                    fillcolor="rgba(0, 0, 255, 0.1)",
                    showlegend=False
                ))

            # Ajouter la médiane
            fig.add_trace(go.Scatter(
                x=var,
                y=median,
                mode='lines',
                line=dict(color='blue', width=2),
                name="Median"
            ))

            # Ajouter la moyenne
            fig.add_trace(go.Scatter(
                x=var,
                y=mean,
                mode='lines',
                line=dict(color='red', width=2),
                name="Mean"
            ))

            # Ajouter les min et max
            fig.add_trace(go.Scatter(
                x=var,
                y=min_values,
                mode='lines',
                line=dict(color='blue', dash='dash'),
                name="Min"
            ))
            fig.add_trace(go.Scatter(
                x=var,
                y=max_values,
                mode='lines',
                line=dict(color='blue', dash='dash'),
                name="Max"
            ))

        else:
            # Affichage des barres empilées
            var = np.arange(result_fab.shape[0]) / step

            fig.add_trace(go.Bar(
                x=var,
                y=EI_manu[:, 0],
                name="Manufacturing",
                marker_color='blue',
                hovertemplate="<b>Manufacturing</b>: %{y:.2e}<br><b>Time</b>: %{x} years<extra></extra>"
            ))

            fig.add_trace(go.Bar(
                x=var,
                y=EI_use[:, 0],
                name="Use",
                marker_color='pink',
                base=EI_manu[:, 0],
                hovertemplate="<b>Use</b>: %{y:.2e}<br><b>Time</b>: %{x} years<extra></extra>"
            ))

            # Ajout de la ligne "Total"
            total = np.sum(result_fab, axis=1) + np.sum(result_use, axis=1)
            fig.add_trace(go.Scatter(
                x=var,
                y=EI[:, 0],
                mode='lines',
                line=dict(color='black', width=2),
                name="Total",
                hovertemplate="<b>Total</b>: %{y:.2e}<br><b>Time</b>: %{x} years<extra></extra>"
            ))

        # Mise en page finale
        fig.update_layout(
            title="Economic Impact",
            xaxis_title="Time (years)",
            yaxis_title="Cost/Price (€)",
            template="plotly_white"
        )

        return fig

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
        base_colors = px.colors.qualitative.Plotly
        n_traces = len(index_labels)

        if n_traces <= len(base_colors):
            colors = base_colors
        else:
            n_extra = n_traces - len(base_colors)
            extra_colors = px.colors.qualitative.Safe[:n_extra]
            colors = base_colors + extra_colors

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
    
    
    def plot_selectEI_plotly(self, dic, EI, EI_manu, EI_use, usage_time, nb_RU, nb_ite_MC, step):
        t = np.arange(0, usage_time, 1)
        result_MC = EI[:, :, dic["selected_EI"]]
        result_fab = EI_manu[:, :, dic["selected_EI"]]
        result_use = EI_use[:, :, dic["selected_EI"]]
        
        # Trier les données si Monte Carlo > 1
        if nb_ite_MC > 1:
            result_MC = result_MC[:, result_MC[0, :].argsort()]
            result_MC = pd.DataFrame(result_MC)

        var = np.arange(result_MC.shape[0]) / step
        
        fig = go.Figure()

        if nb_ite_MC > 1:
            # Calcul des déciles
            percentiles = np.percentile(result_MC, [10, 20, 30, 40, 50, 60, 70, 80, 90], axis=1)
            
            # Ajouter les bandes de déciles (tous les déciles)
            fig.add_trace(go.Scatter(
                x=var,
                y=percentiles[0],
                mode='lines',
                line=dict(width=0),
                fillcolor="rgba(0, 0, 255, 0.1)",
                showlegend=False
            ))
            for i in range(0, 4):  # Inclut tous les déciles
                fig.add_trace(go.Scatter(
                    x=var,
                    y=percentiles[i],
                    mode='lines',
                    fill='tonextx',
                    line=dict(width=0),
                    fillcolor="rgba(0, 0, 255, 0.1)",
                    #name=f"Décile {i * 10}-{(i + 1) * 10}%",  # Légende pour chaque décile
                    showlegend=False
                ))
                fig.add_trace(go.Scatter(
                    x=var,
                    y=percentiles[-(i+1)],
                    mode='lines',
                    fill='tonextx',
                    line=dict(width=0),
                    fillcolor="rgba(0, 0, 255, 0.1)",
                    #name=f" Décile {100 - (i + 1) * 10}-{100 - i * 10}%",  # Légende pour chaque décile
                    showlegend=False
                ))

            # Tracer la médiane (50%)
            fig.add_trace(go.Scatter(
                x=var,
                y=percentiles[4],
                mode='lines',
                line=dict(color='blue', width=2),
                name="Median"
            ))

            # Tracer la moyenne
            mean_values = np.mean(result_MC, axis=1)
            fig.add_trace(go.Scatter(
                x=var,
                y=mean_values,
                mode='lines',
                line=dict(color='red', width=2),
                name="Mean"
            ))

            # Tracer les min et max
            fig.add_trace(go.Scatter(
                x=var,
                y=np.min(result_MC, axis=1),
                mode='lines',
                line=dict(color='blue', dash='dash'),
                name="Min"
            ))

            fig.add_trace(go.Scatter(
                x=var,
                y=np.max(result_MC, axis=1),
                mode='lines',
                line=dict(color='blue', dash='dash'),
                name="Max"
            ))
        else:
            # Affichage des barres empilées
            fig.add_trace(go.Bar(
                x=var,
                y=EI_manu[:, 0, dic["selected_EI"]],
                name="Manufacturing",
                marker_color='blue',
                hovertemplate="<b>Manufacturing</b>: %{y:.2e}<br><b>Time</b>: %{x} years<extra></extra>"
            ))

            fig.add_trace(go.Bar(
                x=var,
                y=EI_use[:, 0, dic["selected_EI"]],
                name="Use",
                marker_color='pink',
                base=EI_manu[:, 0, dic["selected_EI"]],
                hovertemplate="<b>Use</b>: %{y:.2e}<br><b>Time</b>: %{x} years<extra></extra>"
            ))

            fig.add_trace(go.Scatter(
                x=var,
                y=EI[:, 0, dic["selected_EI"]],
                mode="lines",
                name="Total",
                line=dict(color="black", width=2),
                hovertemplate="<b>Total</b>: %{y:.2e}<br><b>Time</b>: %{x} years<extra></extra>"
            ))



        # Mise en page finale
        fig.update_layout(
            title=f"Selected EI: {dic["EI_name"][dic["selected_EI"]]}",
            xaxis_title="Time (years)",
            yaxis_title=f"{dic["EI_name"][dic["selected_EI"]]} ({dic["LCIA_unit"][dic["selected_EI"]]})", #Unit to be added dic["LCIA_unit"]
            template="plotly_white"
        )

        return fig


    def plotCDF_plotly(self, dic, wcdf, wcdf_per_RU, usage_time,step): #add dic, wcdf_per_RU
        import plotly.graph_objects as go
        # Import the result excel to get the RUs names
        excel = pd.ExcelFile(os.path.join(dic["LCA_path"], dic["filename_result_EI"]))
        self.EI_manufacturing = pd.read_excel(excel, sheet_name="Manufacturing", index_col=0)
        self.EI_manufacturing = self.EI_manufacturing.drop(columns=["Unit"])
        # Get the RUs names
        index_labels = self.EI_manufacturing.columns.to_numpy()

        t = np.arange(0, usage_time, 1)
        var = np.arange(0, usage_time, 1) / step

        # Create a figure with the trace
        fig = go.Figure()

        # Add the CDF trace (line plot)
        # CDF of each RU
        for i in range(len(index_labels)):
            fig.add_trace(go.Scatter(
                x=var,
                y = wcdf_per_RU[:,i],
                mode="lines",
                line=dict(dash='dash', width=2),
                name=index_labels[i],
                showlegend=True
            ))
        # Total CDF plot
        fig.add_trace(go.Scatter(x=var, y=wcdf, mode="lines", line=dict(color="mediumvioletred", width=2), name=f" Total", showlegend=True))

        # Update the layout (title, labels, etc.)
        fig.update_layout(
            title="Cumulative Distribution Function",
            xaxis_title="Time (years)",
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

    def plot_allEIatServicelife_plotly(self, dic, EI, EI_manu, EI_use, EI_maintenance, nb_RU, nb_ite_MC, step):
        # Charger les données à partir du fichier Excel
        excel = pd.ExcelFile(os.path.join(dic["LCA_path"], dic["filename_result_EI"]))

        # Lire les données de la feuille Manufacturing
        self.EI_manufacturing = pd.read_excel(excel, sheet_name="Manufacturing", index_col=0)
        self.EI_manufacturing = self.EI_manufacturing.drop(columns=["Unit"])
        self.EI_manufacturing = self.EI_manufacturing.to_numpy()
        self.EI_manufacturing = np.sum(self.EI_manufacturing, axis=1)

        # Calculer la moyenne des EI pour les autres catégories
        # Edit(AEP): In the following lines, mean values of EIs and costs are calculated at the last time step.
        # Therefore, dic["service_life"] is replaced with dic["service_life"]*dic["step"]
        self.EI_use = np.mean(EI_use[dic["service_life"]*dic["step"] - 1, :, :], axis=0)
        self.EI_maintenance = np.mean(EI_maintenance[dic["service_life"]*dic["step"] - 1, :, :], axis=0)
        self.EI_replacement = (
            np.mean(EI_manu[dic["service_life"]*dic["step"] - 1, :, :], axis=0) - self.EI_manufacturing - self.EI_maintenance
        )

        # Calculer le total des EI
        self.EI_total = np.mean(EI[dic["service_life"]*dic["step"] - 1, :, :], axis=0)

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
        index_labels = ["Manufacture", "Use", "Cur. Maint.", "Prev. Maint."] # modified labels of bar graph legend

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

        # Retourne la figure Plotly
        return fig

