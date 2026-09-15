"""Figure and array export utilities."""

from __future__ import annotations

import csv
import logging
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import openpyxl
import pandas as pd
import plotly.graph_objects as go
from openpyxl.utils import get_column_letter

from app.core.config import PelcaConfig
from app.core.lca import LcaResult
from app.core.simulation import (
    DowntimeResult,
    EconomicResult,
    EnvironmentalResult,
    SimulationResult,
)
from app.utils.utils import build_phase_totals

logger = logging.getLogger(__name__)


def _parse_label_units(labels: list[str]) -> tuple[list[str], list[str]]:
    """Split ``"Name (unit)"`` label strings into separate name and unit lists.

    Labels that do not contain a ``(`` are returned with an empty string as
    their unit.  Leading/trailing whitespace is stripped from both parts.

    Args:
        labels: List of strings in ``"Name (unit)"`` format, as produced by
            :func:`~app.utils.utils.build_phase_totals`.

    Returns:
        A pair ``(names, units)`` where each element corresponds to one input
        label.
    """
    names: list[str] = []
    units: list[str] = []
    for label in labels:
        # Split on the first opening parenthesis only.
        head, sep, tail = label.partition("(")
        names.append(head.strip())
        units.append(tail.rstrip(" )") if sep else "")
    return names, units


def _auto_adjust_column_width(path: Path) -> None:
    """Adjust column widths in *path* to fit their content, including headers."""
    if not path.exists():
        raise FileNotFoundError(f"File not found for column width adjustment: {path}")
    wb = openpyxl.load_workbook(path)
    for ws in wb.worksheets:
        for col in ws.columns:
            col_index = col[0].column
            if col_index is None:
                continue
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col_index)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 10)
    wb.save(path)


def _unique_path(directory: Path, stem: str, suffix: str) -> Path:
    """Return a path that does not yet exist in *directory*.

    If ``stem.suffix`` is free, returns it as-is. Otherwise appends ``_1``,
    ``_2``, … until a free name is found — matching the legacy GUI behaviour.
    """
    candidate = directory / f"{stem}.{suffix}"
    counter = 1
    while candidate.exists():
        candidate = directory / f"{stem}_{counter}.{suffix}"
        counter += 1
    return candidate


def export_html(fig: go.Figure, title: str, output_dir: Path) -> None:
    """Write *fig* as a standalone HTML file under ``output_dir/html/``.

    Args:
        fig: Plotly figure to export.
        title: Base filename (without extension). ``/`` and ``\\`` are replaced
            with ``-``.
        output_dir: Parent directory; the ``html/`` subfolder is created if
            absent.
    """
    safe = title.replace("/", "-").replace("\\", "-").replace(":", "")
    dest_dir = output_dir / "html"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = _unique_path(dest_dir, safe, "html")
    fig.write_html(str(dest))
    logger.info("html → %s", dest)


def export_png(fig: go.Figure, title: str, output_dir: Path) -> None:
    """Write *fig* as a PNG image under ``output_dir/png/`` (requires kaleido).

    Args:
        fig: Plotly figure to export.
        title: Base filename (without extension).
        output_dir: Parent directory; the ``png/`` subfolder is created if
            absent.
    """
    safe = title.replace("/", "-").replace("\\", "-").replace(":", "")
    dest_dir = output_dir / "png"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = _unique_path(dest_dir, safe, "png")
    fig.write_image(str(dest))
    logger.info("png  → %s", dest)


def export_svg(fig: go.Figure, title: str, output_dir: Path) -> None:
    """Write *fig* as an SVG image under ``output_dir/svg/`` (requires kaleido).

    Args:
        fig: Plotly figure to export.
        title: Base filename (without extension).
        output_dir: Parent directory; the ``svg/`` subfolder is created if
            absent.
    """
    safe = title.replace("/", "-").replace("\\", "-").replace(":", "")
    dest_dir = output_dir / "svg"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = _unique_path(dest_dir, safe, "svg")
    fig.write_image(str(dest), format="svg")
    logger.info("svg  → %s", dest)


def export_lcic_summary(
    simulation_result: SimulationResult,
    lca_result: LcaResult,
    config: PelcaConfig,
) -> None:
    """Write the end-of-life impact and cost summary to ``LCIC output.xlsx``.

    Produces a DataFrame with one row per LCIA method and an extra ``ECO`` row
    for economic costs, matching the legacy ``LCIC output.xlsx`` format.

    Args:
        simulation_result: Simulation result from :func:`~app.core.simulation.run_simulation`.
        lca_result: Static LCA impact arrays.
        config: Fully parsed PELCA configuration.
    """
    env_result = simulation_result.environmental
    eco_result = simulation_result.economic
    downtime_result = simulation_result.downtime

    # Aggregate per-phase env impacts and economic costs (no downtime here).
    manu_total, use_total, cur_maint_total, prev_maint_total, eol_total, method_labels = (
        build_phase_totals(
            simulation_result=simulation_result,
            lca=lca_result,
            config=config,
        )
    )
    method_names, method_units = _parse_label_units(method_labels)

    # Build summary DataFrame: env rows use the (nb_ei,) slice, eco row uses the last element.
    # Build summary columns; omit planned maintenance when it is disabled.
    summary_data: dict[str, Any] = {
        "Method": method_names,
        "LCIA Unit": method_units,
        "Manufacture": manu_total,
        "Use": use_total,
        "Cur. Maint.": cur_maint_total,
    }
    summary_data["Planned Maint."] = prev_maint_total
    summary_data["End Of Life"] = eol_total
    df = pd.DataFrame(summary_data)

    # -- Write to Excel -------------------------------------------------------
    dest = config.output.lca_dir / config.output.lcic_output_filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(str(dest), index=False, sheet_name="Summary")

    df_eol = export_end_of_life_summary(lca_result, config)
    df_use = export_use_summary(env_result, eco_result, config)
    df_cm = export_curative_maintenance_summary(env_result, eco_result, downtime_result, config)
    df_manufacturing = export_manufacturing_summary(lca_result, config)

    with pd.ExcelWriter(str(dest), engine="openpyxl", mode="a") as writer:
        df_manufacturing.to_excel(writer, index=False, sheet_name="Manufacturing Summary")
        df_use.to_excel(writer, index=False, sheet_name="Use Phase Summary")
        df_pm = export_planned_maintenance_summary(env_result, eco_result, downtime_result, config)
        df_pm.to_excel(writer, index=False, sheet_name="Planned Maint. Summary")
        df_cm.to_excel(writer, index=False, sheet_name="Curative Maint. Summary")
        df_eol.to_excel(writer, index=False, sheet_name="End of Life Summary")

    _auto_adjust_column_width(dest)
    logger.info("xlsx -> %s", dest)


def export_use_summary(
    env_result: EnvironmentalResult,
    eco_result: EconomicResult,
    config: PelcaConfig,
) -> pd.DataFrame:
    """Export use phase summary data as DataFrame.

    One row per LCIA method plus an extra ``ECO`` row for economic costs.
    Each replaceable unit (RU) gets its own column, containing the MC-averaged
    cumulative use phase impact at end of service life.

    Args:
        env_result: Environmental time-series from :func:`~app.core.simulation.run_simulation`.
        eco_result: Economic time-series from :func:`~app.core.simulation.run_simulation`.
        config: Fully parsed PELCA configuration.

    Returns:
        DataFrame with LCIA methods, units, one column per RU activity, and an
        ECO row for use phase costs.
    """
    # Build base DataFrame with method and unit columns
    df = pd.DataFrame(
        {
            "Method": config.lcia.names,
            "LCIA Unit": config.lcia.units,
        }
    )

    # use_mean shape: (nb_ei, nb_ru) — MC-averaged, end of service life
    use_mean = env_result.use[-1, :, :]

    # Add one column per RU activity with its per-method impact
    for idx_activity, activity in enumerate(config.lca.activity_names.use):
        df[activity] = use_mean[:, idx_activity]

    # Build economic row: MC-averaged cumulative cost per RU at last time step
    eco_use_mean = eco_result.use[-1]  # (nb_activity_use,)

    eco_row: dict[str, object] = {
        "Method": "ECO",
        "LCIA Unit": "Euros",
    }

    # Add use phase cost for each RU activity
    for idx_activity, activity in enumerate(config.lca.activity_names.use):
        eco_row[activity] = float(eco_use_mean[idx_activity])

    df = pd.concat([df, pd.DataFrame([eco_row])], ignore_index=True)

    return df


def export_planned_maintenance_summary(
    env_result: EnvironmentalResult,
    eco_result: EconomicResult,
    downtime_result: DowntimeResult,
    config: PelcaConfig,
) -> pd.DataFrame:
    """Export planned maintenance summary data as DataFrame.

    One row per LCIA method plus an extra ``ECO`` row for economic costs.
    Each replaceable unit (RU) gets its own column, containing the MC-averaged
    cumulative planned maintenance impact at end of service life.

    Args:
        env_result: Environmental time-series from :func:`~app.core.simulation.run_simulation`.
        eco_result: Economic time-series from :func:`~app.core.simulation.run_simulation`.
        downtime_result: Downtime time-series from :func:`~app.core.simulation.run_simulation`.
        config: Fully parsed PELCA configuration.

    Returns:
        DataFrame with LCIA methods, units, one column per RU activity, and an
        ECO row for planned maintenance costs.
    """
    # Build base DataFrame with method and unit columns
    df = pd.DataFrame(
        {
            "Method": config.lcia.names,
            "LCIA Unit": config.lcia.units,
        }
    )

    # planned_maintenance_mean shape: (nb_ei, nb_ru) — MC-averaged, end of service life
    pm_mean = env_result.planned_maintenance_mean

    # Add one column per RU activity with its per-method impact
    for idx_activity, activity in enumerate(config.lca.activity_names.planned_maintenance):
        df[activity] = pm_mean[:, idx_activity]

    # Build economic row: MC-averaged cumulative cost per RU at last time step
    eco_pm_mean = np.mean(eco_result.planned_maintenance[-1, :, :], axis=0)  # (nb_ru,)

    eco_row: dict[str, object] = {
        "Method": "ECO",
        "LCIA Unit": "€",
    }

    # Add planned maintenance cost for each RU activity
    for idx_activity, activity in enumerate(config.lca.activity_names.planned_maintenance):
        eco_row[activity] = float(eco_pm_mean[idx_activity])

    downtime_mean_per_ru = np.mean(downtime_result.planned[-1, :, :], axis=0)

    downtime_row: dict[str, object] = {
        "Method": "DWT",
        "LCIA Unit": "h",
    }

    for idx_activity, activity in enumerate(config.lca.activity_names.planned_maintenance):
        downtime_row[activity] = float(downtime_mean_per_ru[idx_activity])

    df = pd.concat([df, pd.DataFrame([downtime_row, eco_row])], ignore_index=True)

    return df


def export_curative_maintenance_summary(
    env_result: EnvironmentalResult,
    eco_result: EconomicResult,
    downtime_result: DowntimeResult,
    config: PelcaConfig,
) -> pd.DataFrame:
    """Export curative maintenance summary data as DataFrame.

    One row per LCIA method plus an extra ``ECO`` row for economic costs.
    Each replaceable unit (RU) gets its own column, containing the MC-averaged
    cumulative curative maintenance impact at end of service life.

    Args:
        env_result: Environmental time-series from :func:`~app.core.simulation.run_simulation`.
        eco_result: Economic time-series from :func:`~app.core.simulation.run_simulation`.
        config: Fully parsed PELCA configuration.

    Returns:
        DataFrame with LCIA methods, units, one column per RU activity, and an
        ECO row for curative maintenance costs.
    """
    # Build base DataFrame with method and unit columns
    df = pd.DataFrame(
        {
            "Method": config.lcia.names,
            "LCIA Unit": config.lcia.units,
        }
    )

    # curative_maintenance_mean shape: (nb_ei, nb_ru) — MC-averaged, end of service life
    cm_mean = env_result.curative_maintenance_mean

    # Add one column per RU activity with its per-method impact
    for idx_activity, activity in enumerate(config.lca.activity_names.curative_maintenance):
        df[activity] = cm_mean[:, idx_activity]

    # Build economic row: MC-averaged cumulative cost per RU at last time step
    eco_cm_mean = np.mean(eco_result.curative_maintenance[-1, :, :], axis=0)

    eco_row: dict[str, object] = {
        "Method": "ECO",
        "LCIA Unit": "€",
    }

    # Add curative maintenance cost for each RU activity
    for idx_activity, activity in enumerate(config.lca.activity_names.curative_maintenance):
        eco_row[activity] = float(eco_cm_mean[idx_activity])

    downtime_mean_per_ru = np.mean(downtime_result.curative[-1, :, :], axis=0)

    downtime_row: dict[str, object] = {
        "Method": "DWT",
        "LCIA Unit": "h",
    }

    # Add curative maintenance downtime for each RU activity
    for idx_activity, activity in enumerate(config.lca.activity_names.curative_maintenance):
        downtime_row[activity] = downtime_mean_per_ru[idx_activity]

    df = pd.concat([df, pd.DataFrame([downtime_row, eco_row])], ignore_index=True)

    return df


def export_end_of_life_summary(
    lca_result: LcaResult,
    config: PelcaConfig,
) -> pd.DataFrame:
    """Export end-of-life summary data as DataFrame.

    Args:
        lca_result: LCA results containing end-of-life data.
        config: Configuration containing LCIA methods, units, and costs.

    Returns:
        DataFrame with LCIA methods, units, activities, and economic costs.
    """
    df = pd.DataFrame(
        {
            "Method": config.lcia.names,
            "LCIA Unit": config.lcia.units,
        }
    )

    # Add LCIA impact columns for each end-of-life activity
    for idx_activity, activity in enumerate(config.lca.activity_names.eol):
        df[activity] = lca_result.eol[:, idx_activity]

    # Add economic row
    eco_row = {
        "Method": "ECO",
        "LCIA Unit": "€",
    }

    # Add end-of-life costs for each activity
    for idx_activity, activity in enumerate(config.lca.activity_names.eol):
        eco_row[activity] = config.simulation.cost.end_of_life[idx_activity]

    df = pd.concat([df, pd.DataFrame([eco_row])], ignore_index=True)

    return df


def export_manufacturing_summary(
    lca_result: LcaResult,
    config: PelcaConfig,
) -> pd.DataFrame:
    """Export manufacturing summary data as DataFrame.

    Args:
        lca_result: LCA results containing manufacturing data.
        config: Configuration containing LCIA methods, units, and costs.

    Returns:
        DataFrame with LCIA methods, units, activities, and economic costs.
    """
    df = pd.DataFrame(
        {
            "Method": config.lcia.names,
            "LCIA Unit": config.lcia.units,
        }
    )

    # Add LCIA impact columns for each manufacturing activity
    for idx_activity, activity in enumerate(config.lca.activity_names.manufacturing):
        df[activity] = lca_result.manufacturing[:, idx_activity]

    # Add economic row
    eco_row = {
        "Method": "ECO",
        "LCIA Unit": "Euros",
    }

    # Add manufacturing costs for each activity
    for idx_activity, activity in enumerate(config.lca.activity_names.manufacturing):
        eco_row[activity] = config.simulation.cost.manufacturing[idx_activity]

    df = pd.concat([df, pd.DataFrame([eco_row])], ignore_index=True)

    return df


def export_excel(name: str, data: np.ndarray, output_dir: Path) -> None:
    """Save *data* as an ``.xlsx`` file in *output_dir*.

    Arrays with more than two dimensions are flattened to 2-D by collapsing all
    axes after the first.

    Args:
        name: Base filename (without extension).
        data: NumPy array to export.
        output_dir: Destination directory (created if absent).
    """

    output_dir.mkdir(parents=True, exist_ok=True)
    dest = _unique_path(output_dir, name, "xlsx")
    flat = data.reshape(data.shape[0], -1) if data.ndim > 2 else data
    pd.DataFrame(flat).T.to_excel(str(dest), index=False)
    logger.info("xlsx → %s", dest)


def export_numpy(name: str, array: np.ndarray, output_dir: Path) -> None:
    """Save *array* as a ``.npy`` file in *output_dir*.

    Args:
        name: Base filename (without extension).
        array: NumPy array to save.
        output_dir: Destination directory (created if absent).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = _unique_path(output_dir, name, "npy")
    with dest.open("wb") as fh:
        np.save(fh, array)
    logger.info("npy  → %s", dest)


def _config_to_flat_dict(config: PelcaConfig) -> dict[str, object]:
    """Flatten *config* into a ordered dict of human-readable key-value pairs.

    Keys and value representations are chosen to match the legacy ``dict_file.csv``
    format produced by ``dictionary.py``.
    """
    sim = config.simulation
    fail = sim.failure
    maint = sim.maintenance
    # Build cost matrix as a DataFrame for a compact representation

    # cost_df = pd.DataFrame(
    #     {
    #         "raw": cost.manufacturing,
    #         "planned": cost.planned,
    #         "curative": cost.curative,
    #         "kwh": cost.kwh_cost,
    #         "eol": cost.end_of_life,
    #     }
    # )

    return {
        "path_result_EI": str(config.output.result_path),
        "filename_result_EI": config.output.lca_output_filename,
        "filename_result_lcic": config.output.lcic_output_filename,
        "simulation": "Analysis",
        "directory": config.output.directory,
        "LCA_path": str(config.output.lca_dir),
        "proj_name": config.lca.project_name,
        "database_ecoinvent": config.lca.database,
        "database_ecoinvent_path": config.lca.ecoinvent_path,
        "inventory_name": config.lca.inventory_name,
        "EI_name": str(config.lcia.names),
        "LCIA_unit": str(config.lcia.units),
        "service_life": sim.service_life,
        "num_hourPerYear": sim.hours_per_year,
        "nb_PM": sim.nb_mission_profiles,
        "step": sim.time_step,
        "nb_ite_MC": sim.mc_iterations,
        "selected_EI": sim.selected_ei_name,
        "Early_failure": fail.early_enabled,
        "Random_failure": fail.random_enabled,
        "Wearout_failure": fail.wearout_enabled,
        "Preventive_maintenance": maint.prev_enabled,
        "Modernization_maintenance": maint.modernization_enabled,
        "Remplacement_matrix": str(maint.replacement_matrix),
    }


def export_config(config: PelcaConfig, output_dir: Path) -> None:
    """Save *config* as ``dict_file.csv`` and ``dict_file.pkl`` in *output_dir*.

    The CSV reproduces the legacy key-value format (one row per parameter,
    blank line between rows). The pickle stores the :class:`~app.core.config.PelcaConfig`
    dataclass directly for reliable round-trip loading.

    Args:
        config: Parsed configuration for the current PELCA run.
        output_dir: Destination directory (created if absent).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    flat = _config_to_flat_dict(config)

    # -- CSV: one key,value row per parameter with a blank line between them --
    csv_path = output_dir / "dict_file.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        for key, value in flat.items():
            writer.writerow([key, value])
            writer.writerow([])  # blank separator line, matching legacy format
    logger.info("csv  → %s", csv_path)

    # -- Pickle: store the dataclass directly ---------------------------------
    pkl_path = output_dir / "dict_file.pkl"
    with pkl_path.open("wb") as fh:
        pickle.dump(config, fh)
    logger.info("pkl  → %s", pkl_path)
