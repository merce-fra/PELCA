from matplotlib.patches import Circle, RegularPolygon
from matplotlib.path import Path
from matplotlib.projections import register_projection
from matplotlib.projections.polar import PolarAxes
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os


class PLOT_MC:
    def __init__(self, dic):
        # Graphiques Matplotlib
        self.fig1_matplotlib = self.radar_montecarlo(dic)

        # Graphiques Plotly
        self.fig1_plotly = self.radar_montecarlo_plotly(dic)
        self.fig2_plotly = self.bar_with_uncertainty_plotly(dic)

        # Liste des graphiques
        self.figs = [
            {
                "title": "Uncertainty Analysis - Monte Carlo (Radar Chart)",
                "plot": self.fig1_matplotlib,
                "type": "matplotlib",
            },
            # {
            #     "title": "Uncertainty Analysis - Monte Carlo (Radar Chart)",
            #     "plot": self.fig1_plotly,
            #     "type": "plotly",
            # },
            {
                "title": "Uncertainty Analysis - Monte Carlo (Bar Chart)",
                "plot": self.fig2_plotly,
                "type": "plotly",
            },
        ]

    def radar_montecarlo(self, dic):
        N = len(dic["EI_name"])
        theta = self.radar_factory(N, frame="polygon")

        excel_LCA = pd.ExcelFile(os.path.join(dic["LCA_path"], dic["filename_result_EI_MC"]))
        df_LCA = pd.read_excel(excel_LCA, 0)
        excel_LCA.close()

        mean = df_LCA.loc[:, "Mean"].to_numpy()
        sd = df_LCA.loc[:, "SD"].to_numpy()

        mean_sum_norm = 100 * mean / mean
        min_sum_norm = 100 * (mean - 2 * sd) / mean
        max_sum_norm = 100 * (mean + 2 * sd) / mean

        categories = [f"{name} ({unit})" for name, unit in zip(dic["EI_name"], dic["LCIA_unit"])]

        fig, ax = plt.subplots(subplot_kw=dict(projection="radar"), figsize=(7, 5))
        ax.set_title("Uncertainty Analysis - Monte Carlo", fontsize=20, weight="bold")

        for data, color, alpha in zip(
            [max_sum_norm, mean_sum_norm, min_sum_norm], ["m", "b", "g"], [0.3, 0.6, 0.3]
        ):
            ax.plot(theta, data, color=color)
            ax.fill(theta, data, color=color, alpha=alpha)

        ax.set_varlabels(categories)
        ax.legend(["μ+2σ", "Mean (μ)", "μ-2σ"], loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3)

        return fig


    def radar_montecarlo_plotly(self, dic):
        excel_LCA = pd.ExcelFile(os.path.join(dic["LCA_path"], dic["filename_result_EI_MC"]))
        df_LCA = pd.read_excel(excel_LCA, 0)
        excel_LCA.close()

        mean = df_LCA.loc[:, "Mean"].to_numpy()
        sd = df_LCA.loc[:, "SD"].to_numpy()

        mean_sum_norm = 100 * mean / mean
        min_sum_norm = 100 * (mean - 2 * sd) / mean
        max_sum_norm = 100 * (mean + 2 * sd) / mean

        categories = [f"{name} ({unit})" for name, unit in zip(dic["EI_name"], dic["LCIA_unit"])]
        categories.append(categories[0])

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=max_sum_norm, theta=categories, fill="toself", name="μ+2σ"))
        fig.add_trace(go.Scatterpolar(r=mean_sum_norm, theta=categories, fill="toself", name="Mean (μ)"))
        fig.add_trace(go.Scatterpolar(r=min_sum_norm, theta=categories, fill="toself", name="μ-2σ"))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), title="Radar Chart")

        return fig

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

    def radar_factory(self, num_vars, frame="circle"):
        theta = np.linspace(0, 2 * np.pi, num_vars, endpoint=False)

        class RadarAxes(PolarAxes):
            name = "radar"
            RESOLUTION = 1

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.set_theta_zero_location("N")

            def fill(self, *args, closed=True, **kwargs):
                return super().fill(closed=closed, *args, **kwargs)

            def plot(self, *args, **kwargs):
                lines = super().plot(*args, **kwargs)
                for line in lines:
                    self._close_line(line)

            def _close_line(self, line):
                x, y = line.get_data()
                if x[0] != x[-1]:
                    x = np.append(x, x[0])
                    y = np.append(y, y[0])
                    line.set_data(x, y)

            def set_varlabels(self, labels):
                self.set_thetagrids(np.degrees(theta), labels)

        register_projection(RadarAxes)
        return theta
