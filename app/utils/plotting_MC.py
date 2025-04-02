import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import os
from plotly.tools import mpl_to_plotly
import plotly.graph_objects as go
import numpy as np
from PIL import Image
import io

class PLOT_MC:
    def __init__(self, dic):
        # Graphiques Matplotlib
        self.fig1_matplotlib = self.radar_montecarlo(dic)

        # Graphiques Plotly
        self.fig3_plotly = self.radar_montecarlo_plotly(dic)
        self.fig2_plotly = self.bar_with_uncertainty_plotly(dic)

        # Liste des graphiques
        self.figs = [
            {
                "title": "Uncertainty Analysis - Monte Carlo (Radar Chart)",
                "plot": self.fig3_plotly,
                "type": "plotly",
            },
            {
                "title": "Uncertainty Analysis - Monte Carlo (Bar Chart)",
                "plot": self.fig2_plotly,
                "type": "plotly",
            },    
        ]

    
    
    #Ajout - radar plotly
    def radar_montecarlo_plotly(self, dic):
        #N = len(dic["EI_name"])
        #theta = self.radar_factory(N, frame="polygon")

        excel_LCA = pd.ExcelFile(os.path.join(dic["LCA_path"], dic["filename_result_EI_MC"]))
        df_LCA = pd.read_excel(excel_LCA, 0)
        excel_LCA.close()

        mean = df_LCA.loc[:, "Mean"].to_numpy()
        sd = df_LCA.loc[:, "SD"].to_numpy()

        mean_sum_norm = 100 * mean / mean
        min_sum_norm = 100 * (mean - 2 * sd) / mean
        max_sum_norm = 100 * (mean + 2 * sd) / mean
        #No change until there

        mean_sum_norm = [*mean_sum_norm, mean_sum_norm[0]]
        min_sum_norm = [*min_sum_norm, min_sum_norm[0]]
        max_sum_norm = [*max_sum_norm, max_sum_norm[0]]

        categories = [f"{name} ({unit})" for name, unit in zip(dic["EI_name"], dic["LCIA_unit"])]
        categories = [*categories, categories[0]]

        fig = go.Figure()

        # Plotting max
        fig.add_trace(go.Scatterpolar(
            r=max_sum_norm, #r to be changed with EI values
            theta=categories,
            fill='toself',
            marker=dict(
                color='magenta',  # Specify the color
                opacity=0.1   # Specify the transparency
            ),
            name="Max (μ+2σ)" #name -> mean / max / min
        ))
        # Plotting mean
        fig.add_trace(go.Scatterpolar(
            r=mean_sum_norm,
            theta=categories,
            fill='toself',
            marker=dict(
                color='blue',  # Specify the color
                opacity=0.2   # Specify the transparency
            ),
            name="Mean (μ)"
        ))
        # Plotting min
        fig.add_trace(go.Scatterpolar(
            r=min_sum_norm,
            theta=categories,
            fill='toself',
            marker=dict(
                color='green',  # Specify the color
                opacity=0.1   # Specify the transparency
            ),
            name="Min (μ-2σ)"
        ))

        fig.update_layout(
            title="Uncertainty Analysis - Monte Carlo\n",
            polar=dict(
                bgcolor='white',
                radialaxis=dict(
                    gridcolor='darkgrey',
                    linecolor='black',
                    showline=True,
                    layer='above traces',
                    tickfont=dict(
                        color='black'
                    ),
                    visible=True,
                ),
                angularaxis=dict(
                    gridcolor='darkgrey'
                )
            ),
            paper_bgcolor='white',
            plot_bgcolor='white',
            showlegend=True
        )

        return fig
    #End - plotly radar



    def bar_with_uncertainty_plotly(self, dic):
        excel_LCA = pd.ExcelFile(os.path.join(dic["LCA_path"], dic["filename_result_EI_MC"]))
        df_LCA = pd.read_excel(excel_LCA, 0)
        excel_LCA.close()

        mean = df_LCA["Mean"]
        sd = df_LCA["SD"]
        categories = [f"{name} ({unit})" for name, unit in zip(dic["EI_name"], dic["LCIA_unit"])]

        mean_sum_norm = 100 * mean / mean
        lower_error = np.clip(mean_sum_norm - (100 * (mean - 2 * sd) / mean), 0, None)
        upper_error = np.clip((100 * (mean + 2 * sd) / mean) - mean_sum_norm, 0, None)

        df_plot = pd.DataFrame({
            "Category": categories,
            "Mean": mean_sum_norm,
            "Lower Error": lower_error,
            "Upper Error": upper_error
        })

        fig = px.bar(
            df_plot,
            x="Category",
            y="Mean",
            error_y="Upper Error",
            error_y_minus="Lower Error",
            title="Uncertainty Analysis - Monte Carlo"
        )
        fig.update_layout(xaxis_title="Category", yaxis_title="Normalized Value (%)")

        return fig