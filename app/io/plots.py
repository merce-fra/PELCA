"""Plotly figure builder for PELCA simulation results.

Accepts :class:`~app.core.simulation.EnvironmentalResult`,
:class:`~app.core.simulation.EconomicResult`,
:class:`~app.core.lca.LcaResult`, and :class:`~app.core.config.PelcaConfig`
and produces a set of interactive Plotly figures covering manufacturing impacts,
end-of-life impacts, CDF, fault repartition, and economic costs.

Entry point: :class:`PlotBuilder`.
"""

from __future__ import annotations

import logging
import math
import sys
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp

from app.core.config import PelcaConfig
from app.core.lca import LcaResult
from app.core.simulation import SimulationResult
from app.utils.utils import build_phase_totals

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

_EPSILON: float = 1e-5
_EOL_ZONE_COLOR: str = "rgba(180, 180, 180, 0.18)"
_EOL_MARKER_SIZE: int = 8
_EOL_EXTENSION_YEARS: float = 1.0


# ── Module-level helpers ───────────────────────────────────────────────────────


def _normalize_array_costs(array_input: np.ndarray) -> np.ndarray:
    """L1-normalise *array_input* so the sum of absolute values equals 100.

    Args:
        array_input: 1-D or N-D numerical array.

    Returns:
        Normalised array with values in ``[-100, 100]``, or an array of zeros
        if the sum of absolute values is effectively zero.
    """
    sum_abs = float(np.sum(np.abs(array_input)))
    if math.isclose(sum_abs, 0.0, abs_tol=sys.float_info.epsilon):
        logger.warning("Sum of absolute values is zero; returning zeros.")
        return np.zeros_like(array_input, dtype=float)
    return (array_input / sum_abs) * 100.0


def _extract_color(trace: Any) -> str:
    """Return a best-effort representative colour string from a Plotly trace.

    Args:
        trace: Any Plotly trace object.

    Returns:
        A CSS colour string.
    """
    if hasattr(trace, "line") and trace.line and trace.line.color:
        return trace.line.color
    if hasattr(trace, "marker") and trace.marker:
        c = trace.marker.color
        if isinstance(c, str):
            return c
    return "rgba(100,100,100,0.8)"


def _add_end_of_life_extension(
    fig: go.Figure,
    eol_x: float = 0.0,
    extension_duration: float = _EOL_EXTENSION_YEARS,
    zone_label: str = "EoL",
    x_max: float | None = None,
) -> go.Figure:
    """Extend all traces on *fig* with a plateau after the end-of-life marker.

    Adds a shaded rectangle, horizontal plateau segments, and end-of-life
    marker dots to every line trace already on the figure.

    Args:
        fig: The Plotly figure to modify in place.
        eol_x: The x-coordinate at which the end-of-life zone begins.
        extension_duration: Width of the EoL zone in the same x-units.
        zone_label: Annotation text for the shaded region.
        x_max: Override the right x-axis bound; defaults to ``eol_x + extension_duration + 0.3``.

    Returns:
        The modified figure (same object).
    """
    eol_end = eol_x + extension_duration

    fig.add_vrect(
        x0=eol_x,
        x1=eol_end,
        fillcolor=_EOL_ZONE_COLOR,
        layer="below",
        line_width=0,
        annotation_text=zone_label,
        annotation_position="top left",
        annotation=dict(
            font=dict(size=11, color="rgba(120,120,120,0.85)"),
            showarrow=False,
        ),
    )

    snapshot: list[Any] = list(fig.data)
    traces_to_add: list[Any] = []

    fill_traces = [
        t
        for t in snapshot
        if hasattr(t, "x")
        and t.x is not None
        and hasattr(t, "y")
        and t.y is not None
        and len(t.x) > 0
        and len(t.y) > 0
        and hasattr(t, "fill")
        and t.fill in ("tonextx", "tonexty", "toself", "tonext")
    ]
    line_traces = [
        t
        for t in snapshot
        if hasattr(t, "x")
        and t.x is not None
        and hasattr(t, "y")
        and t.y is not None
        and len(t.x) > 0
        and len(t.y) > 0
        and not (hasattr(t, "fill") and t.fill in ("tonextx", "tonexty", "toself", "tonext"))
    ]

    n = len(fill_traces)
    if n >= 2:
        n_pairs = n // 2
        for i in range(n_pairs):
            lower_trace = fill_traces[i]
            upper_trace = fill_traces[n - 1 - i]
            lower_y = float(np.asarray(lower_trace.y, dtype=float)[-1])
            upper_y = float(np.asarray(upper_trace.y, dtype=float)[-1])
            fill_color = lower_trace.fillcolor or "rgba(0,0,255,0.1)"
            traces_to_add.append(
                go.Scatter(
                    x=[eol_x, eol_end, eol_end, eol_x, eol_x],
                    y=[lower_y, lower_y, upper_y, upper_y, lower_y],
                    mode="lines",
                    fill="toself",
                    fillcolor=fill_color,
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    for trace in line_traces:
        y_arr = np.asarray(trace.y, dtype=float)
        last_y = float(y_arr[-1])
        line_color = _extract_color(trace)
        tline = trace.line if hasattr(trace, "line") and trace.line else None
        orig_width: int | float = (
            tline.width if tline is not None and tline.width is not None else 2
        )
        orig_dash: str = tline.dash if tline is not None and tline.dash is not None else "solid"
        traces_to_add.append(
            go.Scatter(
                x=[eol_x, eol_end],
                y=[last_y, last_y],
                mode="lines",
                line=dict(color=line_color, width=orig_width, dash=orig_dash),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        traces_to_add.append(
            go.Scatter(
                x=[eol_end],
                y=[last_y],
                mode="markers",
                marker=dict(
                    color=line_color,
                    size=_EOL_MARKER_SIZE,
                    symbol="circle",
                    line=dict(color="white", width=1.5),
                ),
                showlegend=False,
                hovertemplate="<b>End of Life</b><br>Value: %{y:.2e}<extra></extra>",
            )
        )

    for t in traces_to_add:
        fig.add_trace(t)

    current_range = fig.layout.xaxis.range
    right_bound = eol_end + 0.3 if x_max is None else x_max
    if current_range:
        right_bound = max(float(current_range[1]), right_bound)
        fig.update_xaxes(range=[float(current_range[0]), right_bound])
    else:
        fig.update_xaxes(range=[-0.5, right_bound])

    return fig


def _time_axis(usage_time: int, time_step: int) -> np.ndarray:
    """Build the standard x-axis starting at ``-_EPSILON`` and ending after EoL.

    Args:
        usage_time: Number of simulation time steps.
        time_step: Number of time steps per year.

    Returns:
        1-D array of shape ``(usage_time + 2,)`` with a leading ``-_EPSILON``
        and a trailing point one step beyond the last value.
    """
    base = np.arange(usage_time) / time_step
    axis = np.insert(base, 0, -_EPSILON)
    axis = np.append(axis, base[-1] + _EPSILON)
    return axis


# ── Main class ────────────────────────────────────────────────────────────────


class PlotBuilder:
    """Build and display Plotly figures from a completed PELCA simulation run.

    Args:
        config: Full PELCA run configuration.
        lca_result: Per-RU environmental impact arrays from the LCA phase.
        env_result: Time-series environmental impact arrays from the staircase
            simulation.
        eco_result: Time-series economic cost arrays from the staircase
            simulation.
    """

    def __init__(
        self,
        config: PelcaConfig,
        lca_result: LcaResult,
        simulation_result: SimulationResult,
    ) -> None:
        self._config = config
        self._lca = lca_result
        self._simulation_result = simulation_result

        # Aliases
        self._env = simulation_result.environmental
        self._eco = simulation_result.economic
        self._downtime = simulation_result.downtime

    # ── Public API ────────────────────────────────────────────────────────────

    def run(self, show: bool = True) -> list[dict[str, Any]]:
        """Build all figures and optionally open them in a browser.

        Args:
            show: If ``True``, call ``fig.show()`` on every figure so it opens
                in the default browser.  Set to ``False`` to suppress display
                and only receive the return value.

        Returns:
            A list of dicts, each with ``"title"`` (str) and ``"plot"``
            (:class:`plotly.graph_objects.Figure`) keys.
        """
        # Build the ordered list; planned maintenance is included only when enabled.
        builders = [
            self._plot_manufacturing,
            self._plot_use,
            self._plot_preventive_maintenance
            if self._config.simulation.maintenance.prev_enabled
            else None,
            self._plot_modernization
            if self._config.simulation.maintenance.modernization_enabled
            else None,
            self._plot_curative_maintenance,
            self._plot_end_of_life,
            self._plot_cdf,
            self._plot_fault_repartition,
            self._plot_selected_ei,
            self._plot_all_ei,
            self._plot_all_ei_at_service_life,
            self._plot_economic,
            self._plot_downtime_staircase,
        ]
        # Filter out disabled entries.
        active_builders = [builder for builder in builders if builder is not None]

        figs: list[dict[str, Any]] = []
        for builder in active_builders:
            fig = builder()
            # Use the title declared on the figure itself; fall back to a readable builder name.
            fig_title = fig.layout.title.text
            title = (
                str(fig_title)
                if fig_title
                else builder.__name__.removeprefix("_plot_").replace("_", " ").title()
            )
            figs.append({"title": title, "plot": fig, "type": "plotly"})
            if show:
                fig.show()

        return figs

    def save_all(self) -> None:
        """Save all figures as HTML files in the specified directory.

        Args:
            directory: Path to an existing directory where the files will be saved.
        """
        figs = self.run(show=False)
        for fig_info in figs:
            title = fig_info["title"]
            fig = fig_info["plot"]
            filename_html = f"{title.replace(' ', '_')}.html"
            filename_png = f"{title.replace(' ', '_')}.png"
            filepath_html = self._config.output.plot_dir / filename_html
            filepath_png = self._config.output.plot_dir / filename_png
            filepath_html.parent.mkdir(parents=True, exist_ok=True)
            fig.write_html(filepath_html)
            fig.write_image(filepath_png)

    # ── Private plot methods ──────────────────────────────────────────────────

    def _plot_downtime_staircase(self) -> go.Figure:
        """Time-series of cumulative total downtime (hours)
        with statistical bands across MC iterations."""
        sim = self._config.simulation
        nb_ite_mc = sim.mc_iterations
        usage_time = self._downtime.per_maintenance.shape[0]

        # Build time axis in years.
        var = np.arange(usage_time) / sim.time_step

        # Total system downtime per MC iteration: sum over RUs → (usage_time, nb_ite_mc).
        result_mc = self._downtime.per_maintenance.sum(axis=-1)

        fig = go.Figure()

        if nb_ite_mc > 1:
            # Compute percentile bands.
            percentiles = np.percentile(result_mc, [10, 20, 30, 40, 50, 60, 70, 80, 90], axis=1)
            pct_ext = np.insert(percentiles, 0, 0.0, axis=1)
            median_ext = np.insert(np.percentile(result_mc, 50, axis=1), 0, 0.0)
            mean_ext = np.insert(result_mc.mean(axis=1), 0, 0.0)
            min_ext = np.insert(result_mc.min(axis=1), 0, 0.0)
            max_ext = np.insert(result_mc.max(axis=1), 0, 0.0)
            var_ext = np.insert(var, 0, -_EPSILON)

            # Bottom boundary for the first fill band.
            fig.add_trace(
                go.Scatter(
                    x=var_ext,
                    y=pct_ext[0],
                    mode="lines",
                    line=dict(width=0),
                    fillcolor="rgba(0,0,255,0.1)",
                    showlegend=False,
                )
            )
            # Nested percentile fill bands (10–90, 20–80, 30–70, 40–60).
            for i in range(4):
                fig.add_trace(
                    go.Scatter(
                        x=var_ext,
                        y=pct_ext[i],
                        mode="lines",
                        fill="tonextx",
                        line=dict(width=0),
                        fillcolor="rgba(0,0,255,0.1)",
                        showlegend=False,
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=var_ext,
                        y=pct_ext[-(i + 1)],
                        mode="lines",
                        fill="tonextx",
                        line=dict(width=0),
                        fillcolor="rgba(0,0,255,0.1)",
                        showlegend=False,
                    )
                )
            # Median, mean, min, max lines.
            fig.add_trace(
                go.Scatter(
                    x=var_ext,
                    y=median_ext,
                    mode="lines",
                    line=dict(color="blue", width=2),
                    name="Median",
                    hovertemplate="<b>Median</b>: %{y:.2f} h<br>%{x:.2f} yr<extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=var_ext,
                    y=mean_ext,
                    mode="lines",
                    line=dict(color="red", width=2),
                    name="Mean",
                    hovertemplate="<b>Mean</b>: %{y:.2f} h<br>%{x:.2f} yr<extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=var_ext,
                    y=min_ext,
                    mode="lines",
                    line=dict(color="blue", dash="dash"),
                    name="Min",
                    hovertemplate="<b>Min</b>: %{y:.2f} h<br>%{x:.2f} yr<extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=var_ext,
                    y=max_ext,
                    mode="lines",
                    line=dict(color="blue", dash="dash"),
                    name="Max",
                    hovertemplate="<b>Max</b>: %{y:.2f} h<br>%{x:.2f} yr<extra></extra>",
                )
            )
        else:
            # Single iteration: squeeze MC axis and plot the total directly.
            total_vals = result_mc[:, 0]  # (usage_time,)
            fig.add_trace(
                go.Scatter(
                    x=var,
                    y=total_vals,
                    mode="lines",
                    line=dict(color="mediumvioletred", width=2),
                    name="Total",
                    hovertemplate="<b>Total</b>: %{y:.2f} h<br>%{x:.2f} yr<extra></extra>",
                )
            )

        fig.update_layout(
            title="Downtime Impact",
            xaxis_title="Time (years)",
            yaxis_title="DWT (hours)",
            xaxis=dict(showgrid=True, gridcolor="lightgray"),
            yaxis=dict(showgrid=True, gridcolor="lightgray"),
            plot_bgcolor="white",
        )

        _add_end_of_life_extension(fig, zone_label="", eol_x=float(var.max()))
        return fig

    def _plot_use(self) -> go.Figure:
        """Normalised stacked bar chart of use-phase EI per RU."""
        use_np = self._env.use[-1, :, :]
        use_cost = self._eco.use[-1]  # (nb_activity_use,)

        total_impact = np.vstack([use_np, use_cost])
        total_norm = np.apply_along_axis(_normalize_array_costs, axis=1, arr=total_impact)

        ru_names = list(self._config.lca.activity_names.use)
        ei_names = self._config.lcia.names
        units = self._config.lcia.units
        x_labels = [f"{n} ({u})" for n, u in zip(ei_names, units, strict=False)] + ["ECO (€)"]

        base_colors = px.colors.qualitative.Plotly
        n_traces = len(ru_names)
        if n_traces > len(base_colors):
            extra = px.colors.qualitative.Safe[: n_traces - len(base_colors)]
            colors = base_colors + extra
        else:
            colors = base_colors

        fig = go.Figure()
        for j, name in enumerate(ru_names):
            fig.add_trace(
                go.Bar(
                    x=x_labels,
                    y=total_norm[:, j],
                    name=name,
                    marker_color=colors[j % len(colors)],
                    text=[f"{v:.1e}" for v in total_impact[:, j]],
                    textposition="inside",
                )
            )

        fig.update_layout(
            barmode="relative",
            title="Use Impacts",
            xaxis_title="",
            yaxis_title="Normalised value (%)",
            yaxis=dict(showgrid=True, gridcolor="lightgray"),
            legend_title="",
            yaxis_autorange=True,
            plot_bgcolor="white",
        )
        return fig

    def _plot_preventive_maintenance(self) -> go.Figure:
        """Normalised stacked bar chart of preventive maintenance EI per RU."""
        return self._plot_planned_subtype(
            maint_np=self._env.preventive_maintenance_mean,
            cost_np=np.mean(self._eco.preventive_maintenance[-1, :, :], axis=0),
            downtime_np=np.mean(self._downtime.preventive[-1, :, :], axis=0),
            title="Preventive Maintenance Impacts",
        )

    def _plot_modernization(self) -> go.Figure:
        """Normalised stacked bar chart of modernization EI per RU."""
        return self._plot_planned_subtype(
            maint_np=self._env.modernization_mean,
            cost_np=np.mean(self._eco.modernization[-1, :, :], axis=0),
            downtime_np=np.mean(self._downtime.modernization[-1, :, :], axis=0),
            title="Modernization Impacts",
        )

    def _plot_planned_subtype(
        self,
        maint_np: np.ndarray,
        cost_np: np.ndarray,
        downtime_np: np.ndarray,
        title: str,
    ) -> go.Figure:
        """Build a normalised stacked bar chart for one planned-maintenance subtype.

        Args:
            maint_np: MC-averaged per-RU environmental impact array. Shape
                ``(nb_ei, nb_ru_maint)``.
            cost_np: MC-averaged per-RU cumulative cost. Shape ``(nb_ru,)``.
            downtime_np: MC-averaged per-RU cumulative downtime hours. Shape ``(nb_ru,)``.
            title: Figure title.

        Returns:
            A ``plotly.graph_objects.Figure`` with one stacked bar per RU.
        """
        # Stack EI rows, the downtime row, and the cost row to form the full per-RU impact matrix.
        total_impact = np.vstack([maint_np, downtime_np, cost_np])
        # Normalise each row (EI method, downtime, or cost) to a 0-100 % distribution.
        total_norm = np.apply_along_axis(_normalize_array_costs, axis=1, arr=total_impact)

        # Activity (RU) labels are shared between preventive and modernization.
        ru_names = list(self._config.lca.activity_names.planned_maintenance)
        ei_names = self._config.lcia.names
        units = self._config.lcia.units
        x_labels = [f"{n} ({u})" for n, u in zip(ei_names, units, strict=False)] + [
            "DWT (h)",
            "ECO (€)",
        ]

        # Extend the qualitative palette if there are more RUs than base colours.
        base_colors = px.colors.qualitative.Plotly
        n_traces = len(ru_names)
        if n_traces > len(base_colors):
            extra = px.colors.qualitative.Safe[: n_traces - len(base_colors)]
            colors = base_colors + extra
        else:
            colors = base_colors

        # One stacked bar trace per RU.
        fig = go.Figure()
        for j, name in enumerate(ru_names):
            fig.add_trace(
                go.Bar(
                    x=x_labels,
                    y=total_norm[:, j],
                    name=name,
                    marker_color=colors[j % len(colors)],
                    text=[f"{v:.1e}" for v in total_impact[:, j]],
                    textposition="inside",
                )
            )

        fig.update_layout(
            barmode="relative",
            title=title,
            xaxis_title="",
            yaxis=dict(title="Normalised value (%)", showgrid=True, gridcolor="lightgray"),
            legend_title="",
            yaxis_autorange=True,
            plot_bgcolor="white",
        )
        return fig

    def _plot_curative_maintenance(self) -> go.Figure:
        """Normalised stacked bar chart of curative maintenance EI per RU."""
        maint_np = self._env.curative_maintenance_mean  # (nb_ei, nb_ru_maint)
        curative_maint_cost = np.mean(self._eco.curative_maintenance[-1, :, :], axis=0)  # (nb_ru,)
        curative_downtime = np.mean(self._downtime.curative[-1, :, :], axis=0)  # (nb_ru,)

        # Stack EI rows, the downtime row, and the cost row.
        total_impact = np.vstack([maint_np, curative_downtime, curative_maint_cost])
        total_norm = np.apply_along_axis(_normalize_array_costs, axis=1, arr=total_impact)

        ru_names = list(self._config.lca.activity_names.curative_maintenance)
        ei_names = self._config.lcia.names
        units = self._config.lcia.units
        x_labels = [f"{n} ({u})" for n, u in zip(ei_names, units, strict=False)] + [
            "DWT (h)",
            "ECO (€)",
        ]

        base_colors = px.colors.qualitative.Plotly
        n_traces = len(ru_names)
        if n_traces > len(base_colors):
            extra = px.colors.qualitative.Safe[: n_traces - len(base_colors)]
            colors = base_colors + extra
        else:
            colors = base_colors

        fig = go.Figure()
        for j, name in enumerate(ru_names):
            fig.add_trace(
                go.Bar(
                    x=x_labels,
                    y=total_norm[:, j],
                    name=name,
                    marker_color=colors[j % len(colors)],
                    text=[f"{v:.1e}" for v in total_impact[:, j]],
                    textposition="inside",
                )
            )

        fig.update_layout(
            barmode="relative",
            title="Curative Maintenance Impacts",
            xaxis_title="",
            yaxis=dict(title="Normalised value (%)", showgrid=True, gridcolor="lightgray"),
            legend_title="",
            yaxis_autorange=True,
            plot_bgcolor="white",
        )
        return fig

    def _plot_manufacturing(self) -> go.Figure:
        """Normalised stacked bar chart of manufacturing EI and cost per RU."""
        manu_np = self._lca.manufacturing  # (nb_ei, nb_ru_manu)
        # raw_cost is already phase-specific (manufacturing only) as read from the Excel.
        raw_costs = self._config.simulation.cost.manufacturing[:]

        total_impact = np.vstack([manu_np, raw_costs])
        total_norm = np.apply_along_axis(_normalize_array_costs, axis=1, arr=total_impact)

        ru_names = list(self._config.lca.activity_names.manufacturing)
        ei_names = self._config.lcia.names
        units = self._config.lcia.units
        x_labels = [f"{n} ({u})" for n, u in zip(ei_names, units, strict=False)] + ["ECO (€)"]

        base_colors = px.colors.qualitative.Plotly
        n_traces = len(ru_names)
        if n_traces > len(base_colors):
            extra = px.colors.qualitative.Safe[: n_traces - len(base_colors)]
            colors = base_colors + extra
        else:
            colors = base_colors

        fig = go.Figure()
        for j, name in enumerate(ru_names):
            fig.add_trace(
                go.Bar(
                    x=x_labels,
                    y=total_norm[:, j],
                    name=name,
                    marker_color=colors[j % len(colors)],
                    text=[f"{v:.1e}" for v in total_impact[:, j]],
                    textposition="inside",
                )
            )

        fig.update_layout(
            barmode="relative",
            title="Manufacturing Impacts",
            xaxis_title="",
            yaxis=dict(title="Normalised value (%)", showgrid=True, gridcolor="lightgray"),
            legend_title="",
            yaxis_autorange=True,
            plot_bgcolor="white",
        )
        return fig

    def _plot_end_of_life(self) -> go.Figure:
        """Normalised stacked bar chart of End-of-Life EI and cost per RU."""
        eol_np = self._lca.eol  # (nb_ei, nb_ru_eol)
        # eol_cost is already phase-specific (EoL only) as read from the Excel.
        eol_costs = self._config.simulation.cost.end_of_life[:]

        total_impact = np.vstack([eol_np, eol_costs])
        total_norm = np.apply_along_axis(_normalize_array_costs, axis=1, arr=total_impact)

        ru_names = list(self._config.lca.activity_names.eol)
        ei_names = self._config.lcia.names
        units = self._config.lcia.units
        x_labels = [f"{n} ({u})" for n, u in zip(ei_names, units, strict=False)] + ["ECO (€)"]

        base_colors = px.colors.qualitative.Plotly
        n_traces = len(ru_names)
        if n_traces > len(base_colors):
            extra = px.colors.qualitative.Safe[: n_traces - len(base_colors)]
            colors = base_colors + extra
        else:
            colors = base_colors

        fig = go.Figure()
        for j, name in enumerate(ru_names):
            fig.add_trace(
                go.Bar(
                    x=x_labels,
                    y=total_norm[:, j],
                    name=name,
                    marker_color=colors[j % len(colors)],
                    text=[f"{v:.1e}" for v in total_impact[:, j]],
                    textposition="inside",
                )
            )

        fig.update_layout(
            barmode="relative",
            title="End-of-Life Impacts",
            xaxis_title="",
            yaxis=dict(title="Normalised value (%)", showgrid=True, gridcolor="lightgray"),
            legend_title="",
            yaxis_autorange=True,
            plot_bgcolor="white",
        )
        return fig

    def _plot_cdf(self) -> go.Figure:
        """Cumulative distribution function for each RU and the total system."""
        sim = self._config.simulation
        usage_time = self._env.wcdf_total.shape[0]
        var = np.arange(usage_time) / sim.time_step

        curative_ru = self._config.simulation.cost.names.curative_maintenance
        nb_ru = self._lca.nb_ru

        # Cycle through distinct colors and dash styles so overlapping RU curves remain visible.
        ru_colors = px.colors.qualitative.Plotly
        dash_styles = ["longdashdot", "longdash", "dashdot", "dash", "dot"]

        fig = go.Figure()
        for i in range(nb_ru):
            label = curative_ru[i] if i < len(curative_ru) else f"RU {i}"
            color = ru_colors[i % len(ru_colors)]
            dash = dash_styles[i % len(dash_styles)]
            fig.add_trace(
                go.Scatter(
                    x=var,
                    y=self._env.wcdf_per_ru[:, i],
                    mode="lines",
                    line=dict(color=color, dash=dash, width=2),
                    name=label,
                )
            )
        fig.add_trace(
            go.Scatter(
                x=var,
                y=self._env.wcdf_total,
                mode="lines",
                line=dict(color="mediumvioletred", width=2),
                name="Total",
            )
        )

        fig.update_layout(
            title="Cumulative Distribution Function",
            xaxis_title="Time (years)",
            yaxis_title="CDF",
            xaxis=dict(showgrid=True, gridcolor="lightgray"),
            yaxis=dict(showgrid=True, gridcolor="lightgray"),
            plot_bgcolor="white",
        )
        return fig

    def _plot_fault_repartition(self) -> go.Figure:
        """Pie chart showing the distribution of fault causes."""
        failure = self._config.simulation.failure
        if not (failure.wearout_enabled or failure.random_enabled or failure.early_enabled):
            fig = go.Figure()
            fig.add_trace(
                go.Pie(
                    labels=["No fault selected"],
                    values=[1],
                    marker=dict(colors=["lightgrey"]),
                    textinfo="label",
                    showlegend=False,
                )
            )
            fig.update_layout(
                title="No Fault Selected",
                title_x=0.5,
                title_font=dict(size=24),
            )
            return fig

        flat = self._env.fault_cause.flatten()
        counts = [
            int(np.sum(flat == "Early")),
            int(np.sum(flat == "Random")),
            int(np.sum(flat == "Wearout")),
        ]
        labels = ["Early fault", "Random fault", "Wearout fault"]
        filtered_counts = [c for c in counts if c > 0]
        filtered_labels = [label for c, label in zip(counts, labels, strict=False) if c > 0]

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=filtered_labels,
                    values=filtered_counts,
                    marker=dict(colors=px.colors.qualitative.Plotly[: len(filtered_labels)]),
                    textinfo="label+percent",
                    pull=[0.1] * len(filtered_labels),
                )
            ]
        )
        fig.update_layout(
            title="Distribution of Defects",
            title_x=0.5,
            title_font=dict(size=24),
            showlegend=False,
        )
        return fig

    def _plot_selected_ei(self) -> go.Figure:
        """Time-series for the selected environmental impact indicator."""
        sim = self._config.simulation
        ei_name = sim.selected_ei_name
        ei_idx = self._config.lcia.names.index(ei_name)
        nb_ite_mc = sim.mc_iterations
        step = sim.time_step

        ei_unit = self._config.lcia.units[ei_idx]
        eol_impact = float(np.sum(self._lca.eol, axis=1)[ei_idx])

        # Strip the extra EoL step from total; EoL is appended manually below.
        result_mc = pd.DataFrame(self._env.total[:-1, :, ei_idx].copy())
        usage_time = result_mc.shape[0]

        if nb_ite_mc > 1:
            result_mc = result_mc.iloc[:, result_mc.iloc[0].argsort().tolist()]

        var = _time_axis(usage_time, step)

        # Append end-of-life row.
        eol_row = result_mc.iloc[-1] + eol_impact
        result_mc = pd.concat([result_mc, eol_row.to_frame().T], ignore_index=True)

        fig = go.Figure()

        if nb_ite_mc > 1:
            percentiles = np.percentile(
                result_mc.values, [10, 20, 30, 40, 50, 60, 70, 80, 90], axis=1
            )
            pct_ext = np.insert(percentiles, 0, 0.0, axis=1)
            median_ext = np.insert(np.percentile(result_mc.values, 50, axis=1), 0, 0.0)
            mean_ext = np.insert(np.asarray(result_mc.mean(axis=1)), 0, 0.0)
            min_ext = np.insert(np.asarray(result_mc.min(axis=1)), 0, 0.0)
            max_ext = np.insert(np.asarray(result_mc.max(axis=1)), 0, 0.0)

            fig.add_trace(
                go.Scatter(
                    x=var,
                    y=pct_ext[0],
                    mode="lines",
                    line=dict(width=0),
                    fillcolor="rgba(0,0,255,0.1)",
                    showlegend=False,
                )
            )
            for i in range(4):
                fig.add_trace(
                    go.Scatter(
                        x=var,
                        y=pct_ext[i],
                        mode="lines",
                        fill="tonextx",
                        line=dict(width=0),
                        fillcolor="rgba(0,0,255,0.1)",
                        showlegend=False,
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=var,
                        y=pct_ext[-(i + 1)],
                        mode="lines",
                        fill="tonextx",
                        line=dict(width=0),
                        fillcolor="rgba(0,0,255,0.1)",
                        showlegend=False,
                    )
                )
            fig.add_trace(
                go.Scatter(
                    x=var,
                    y=median_ext,
                    mode="lines",
                    line=dict(color="blue", width=2),
                    name="Median",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=var, y=mean_ext, mode="lines", line=dict(color="red", width=2), name="Mean"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=var, y=min_ext, mode="lines", line=dict(color="blue", dash="dash"), name="Min"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=var, y=max_ext, mode="lines", line=dict(color="blue", dash="dash"), name="Max"
                )
            )
        else:
            # Non-use cumulative EI (manufacturing constant + cumulative maintenance).
            manu_vals = np.insert(
                self._env.manufacturing_total[ei_idx]
                + self._env.planned_maintenance_total[:, 0, ei_idx]
                + self._env.curative_maintenance_total[:, 0, ei_idx],
                0,
                0.0,
            )
            use_vals = np.insert(self._env.use_total[:, ei_idx], 0, 0.0)
            # Strip EoL step from total; EoL is appended as the trailing point.
            total_vals = np.insert(self._env.total[:-1, 0, ei_idx], 0, 0.0)
            total_vals = np.append(total_vals, total_vals[-1] + eol_impact)

            fig.add_trace(
                go.Bar(
                    x=var,
                    y=manu_vals,
                    name="Manufacturing",
                    marker_color="blue",
                    hovertemplate=(
                        "<b>Manufacturing</b>: %{y:.2e}<br><b>Time</b>: %{x} yr<extra></extra>"
                    ),
                )
            )
            fig.add_trace(
                go.Bar(
                    x=var,
                    y=use_vals,
                    name="Use",
                    marker_color="pink",
                    base=manu_vals,
                    hovertemplate=("<b>Use</b>: %{y:.2e}<br><b>Time</b>: %{x} yr<extra></extra>"),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=var,
                    y=total_vals,
                    mode="lines",
                    line=dict(color="black", width=2),
                    name="Total",
                    hovertemplate="<b>Total</b>: %{y:.2e}<br><b>Time</b>: %{x} yr<extra></extra>",
                )
            )

        fig.update_layout(
            title=f"Selected EI: {ei_name}",
            xaxis=dict(title="Time (years)", showgrid=True, gridcolor="lightgray"),
            yaxis=dict(title=f"{ei_name} ({ei_unit})", showgrid=True, gridcolor="lightgray"),
            template="plotly_white",
        )
        _add_end_of_life_extension(fig, eol_x=float(var.max()))
        return fig

    def _plot_all_ei(self) -> go.Figure:
        """Grid of time-series subplots — one panel per LCIA indicator."""
        sim = self._config.simulation
        nb_ite_mc = sim.mc_iterations
        step = sim.time_step
        methods = self._config.lcia.names
        nb_ei = len(methods)
        eol_per_ei = np.sum(self._lca.eol, axis=1)  # (nb_ei,)

        # Strip the extra EoL step; it is appended manually per subplot below.
        usage_time = self._env.total.shape[0] - 1
        num_cols = 4
        num_rows = math.ceil(nb_ei / num_cols)

        fig = sp.make_subplots(rows=num_rows, cols=num_cols, subplot_titles=methods)

        for ei_index in range(nb_ei):
            row = (ei_index // num_cols) + 1
            col = (ei_index % num_cols) + 1

            df = pd.DataFrame(self._env.total[:-1, :, ei_index])
            base_x = np.arange(usage_time) / step
            var = np.insert(base_x, 0, -_EPSILON)
            var = np.append(var, base_x[-1] + _EPSILON)

            eol_row = df.iloc[-1] + eol_per_ei[ei_index]
            df = pd.concat([df, eol_row.to_frame().T], ignore_index=True)

            if nb_ite_mc > 1:
                mean_vals = np.insert(np.asarray(df.mean(axis=1)), 0, 0.0)
                median_vals = np.insert(np.asarray(df.median(axis=1)), 0, 0.0)
                min_vals = np.insert(np.asarray(df.min(axis=1)), 0, 0.0)
                max_vals = np.insert(np.asarray(df.max(axis=1)), 0, 0.0)

                first = ei_index == 0
                fig.add_trace(
                    go.Scatter(
                        x=var,
                        y=mean_vals,
                        mode="lines",
                        name="Mean",
                        line=dict(color="blue"),
                        showlegend=first,
                        legendgroup="mean",
                        hovertemplate="<b>Mean</b>: %{y:.2e}<br>%{x} yr<extra></extra>",
                    ),
                    row=row,
                    col=col,
                )
                fig.add_trace(
                    go.Scatter(
                        x=var,
                        y=min_vals,
                        mode="lines",
                        name="Min",
                        line=dict(dash="dot", color="lightblue"),
                        showlegend=first,
                        legendgroup="min",
                        hovertemplate="<b>Min</b>: %{y:.2e}<br>%{x} yr<extra></extra>",
                    ),
                    row=row,
                    col=col,
                )
                fig.add_trace(
                    go.Scatter(
                        x=var,
                        y=max_vals,
                        mode="lines",
                        name="Max",
                        line=dict(dash="dot", color="lightblue"),
                        showlegend=first,
                        legendgroup="max",
                        hovertemplate="<b>Max</b>: %{y:.2e}<br>%{x} yr<extra></extra>",
                    ),
                    row=row,
                    col=col,
                )
                fig.add_trace(
                    go.Scatter(
                        x=var,
                        y=median_vals,
                        mode="lines",
                        name="Median",
                        line=dict(color="green"),
                        showlegend=first,
                        legendgroup="median",
                        hovertemplate="<b>Median</b>: %{y:.2e}<br>%{x} yr<extra></extra>",
                    ),
                    row=row,
                    col=col,
                )
            else:
                # Non-use component: constant manu + cumulative maintenance.
                manu = (
                    self._env.manufacturing_total[ei_index]
                    + self._env.planned_maintenance_total[:, 0, ei_index]
                    + self._env.curative_maintenance_total[:, 0, ei_index]
                )
                use = self._env.use_total[:, ei_index]
                # Strip EoL step; EoL is already appended via eol_row above.
                total = self._env.total[:-1, 0, ei_index]
                fig.add_trace(
                    go.Bar(
                        x=var,
                        y=manu,
                        name=f"Manufacturing ({methods[ei_index]})",
                        marker_color="blue",
                        hovertemplate="<b>Manufacturing</b>: %{y:.2e}<extra></extra>",
                    ),
                    row=row,
                    col=col,
                )
                fig.add_trace(
                    go.Bar(
                        x=var,
                        y=use,
                        name=f"Use ({methods[ei_index]})",
                        marker_color="pink",
                        base=manu,
                        hovertemplate="<b>Use</b>: %{y:.2e}<extra></extra>",
                    ),
                    row=row,
                    col=col,
                )
                fig.add_trace(
                    go.Scatter(
                        x=var,
                        y=total,
                        mode="lines",
                        name=f"Total ({methods[ei_index]})",
                        line=dict(color="black", width=2),
                        hovertemplate="<b>Total</b>: %{y:.2e}<extra></extra>",
                    ),
                    row=row,
                    col=col,
                )

        fig.update_layout(
            title="Environmental Impact Over Time",
            barmode="relative",
            legend=dict(x=1.05, y=1),
            autosize=True,
            plot_bgcolor="white",
        )
        for i in range(1, num_rows + 1):
            for j in range(1, num_cols + 1):
                fig.update_xaxes(
                    title_text="Time (years)", showgrid=True, gridcolor="lightgray", row=i, col=j
                )
                fig.update_yaxes(showgrid=True, gridcolor="lightgray", row=i, col=j)

        return fig

    def _plot_all_ei_at_service_life(self) -> go.Figure:
        """Normalised stacked bar chart of all LCIA indicators at service life."""
        # Aggregate env impacts, downtime, and economic costs per phase.
        manu_total, use_total, cur_maint_total, prev_maint_total, eol_total, x_labels = (
            build_phase_totals(
                simulation_result=self._simulation_result,
                lca=self._lca,
                config=self._config,
                downtime=self._downtime,
            )
        )

        stacked = np.column_stack(
            (manu_total, use_total, cur_maint_total, prev_maint_total, eol_total)
        )
        stacked_norm = np.apply_along_axis(_normalize_array_costs, axis=1, arr=stacked)

        colors = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"]
        bar_labels = ["Manufacture", "Use", "Cur. Maint.", "Planned Maint.", "End of Life"]

        fig = go.Figure()
        for idx, label in enumerate(bar_labels):
            fig.add_trace(
                go.Bar(
                    name=label,
                    x=x_labels,
                    y=stacked_norm[:, idx],
                    text=[f"{v:.1e}" for v in stacked[:, idx]],
                    textposition="inside",
                    marker=dict(color=colors[idx]),
                )
            )

        fig.update_layout(
            barmode="relative",
            title="Total impacts at service life (mean)",
            xaxis=dict(title="Indicators", tickangle=45),
            yaxis=dict(title="Normalised value (%)", showgrid=True, gridcolor="lightgray"),
            yaxis_autorange=True,
            legend=dict(title="Categories"),
            plot_bgcolor="white",
        )
        return fig

    def _plot_economic(self) -> go.Figure:
        """Time-series of economic cost, broken down by life-cycle stage."""
        sim = self._config.simulation
        nb_ite_mc = sim.mc_iterations
        step = sim.time_step

        # total has shape (usage_time + 1, nb_ite_mc): EoL already at last index.
        result_mc = self._eco.total.copy()
        usage_time = result_mc.shape[0] - 1

        base_x = np.arange(usage_time) / step
        var = np.insert(base_x, 0, -_EPSILON)
        var = np.append(var, base_x[-1] + _EPSILON)

        fig = go.Figure()

        if nb_ite_mc > 1:
            percentiles = np.percentile(result_mc, [10, 20, 30, 40, 50, 60, 70, 80, 90], axis=1)
            pct_ext = np.insert(percentiles, 0, 0.0, axis=1)
            median_ext = np.insert(np.percentile(result_mc, 50, axis=1), 0, 0.0)
            mean_ext = np.insert(result_mc.mean(axis=1), 0, 0.0)
            min_ext = np.insert(result_mc.min(axis=1), 0, 0.0)
            max_ext = np.insert(result_mc.max(axis=1), 0, 0.0)

            fig.add_trace(
                go.Scatter(
                    x=var,
                    y=pct_ext[0],
                    mode="lines",
                    line=dict(width=0),
                    fillcolor="rgba(0,0,255,0.1)",
                    showlegend=False,
                )
            )
            for i in range(len(pct_ext) // 2):
                fig.add_trace(
                    go.Scatter(
                        x=var,
                        y=pct_ext[i],
                        mode="lines",
                        fill="tonextx",
                        line=dict(width=0),
                        fillcolor="rgba(0,0,255,0.1)",
                        showlegend=False,
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=var,
                        y=pct_ext[-(i + 1)],
                        mode="lines",
                        fill="tonextx",
                        line=dict(width=0),
                        fillcolor="rgba(0,0,255,0.1)",
                        showlegend=False,
                    )
                )
            fig.add_trace(
                go.Scatter(
                    x=var,
                    y=median_ext,
                    mode="lines",
                    line=dict(color="blue", width=2),
                    name="Median",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=var, y=mean_ext, mode="lines", line=dict(color="red", width=2), name="Mean"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=var, y=min_ext, mode="lines", line=dict(color="blue", dash="dash"), name="Min"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=var, y=max_ext, mode="lines", line=dict(color="blue", dash="dash"), name="Max"
                )
            )
        else:
            # Manufacturing is constant (punctual); use grows cumulatively.
            manu_val = float(self._eco.manufacturing.sum())
            manu_vals = np.insert(np.full(usage_time + 1, manu_val), 0, 0.0)
            use_base = self._eco.use.sum(axis=-1)  # (usage_time,) cumulative use summed over RUs
            use_at_eol = float(use_base[-1])
            use_vals = np.insert(np.append(use_base, use_at_eol), 0, 0.0)
            total_vals = np.insert(self._eco.total[:, 0], 0, 0.0)

            fig.add_trace(
                go.Bar(
                    x=var,
                    y=manu_vals,
                    name="Manufacturing",
                    marker_color="blue",
                    hovertemplate="<b>Manufacturing</b>: %{y:.2e}<br>%{x} yr<extra></extra>",
                )
            )
            fig.add_trace(
                go.Bar(
                    x=var,
                    y=use_vals,
                    name="Use",
                    marker_color="pink",
                    base=manu_vals,
                    hovertemplate="<b>Use</b>: %{y:.2e}<br>%{x} yr<extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=var,
                    y=total_vals,
                    mode="lines",
                    line=dict(color="black", width=2),
                    name="Total",
                    hovertemplate="<b>Total</b>: %{y:.2e}<br>%{x} yr<extra></extra>",
                )
            )

        fig.update_layout(
            title="Economic Impact",
            xaxis_title="Time (years)",
            yaxis_title="ECO (€)",
            xaxis=dict(showgrid=True, gridcolor="lightgray"),
            yaxis=dict(showgrid=True, gridcolor="lightgray"),
            plot_bgcolor="white",
        )
        _add_end_of_life_extension(fig, eol_x=float(var.max()))
        return fig
