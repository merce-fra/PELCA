"""Shared utility functions for PELCA computation and plotting modules.

Provides :func:`build_phase_totals`, which aggregates environmental impacts
from :class:`~app.core.simulation.EnvironmentalResult`,
:class:`~app.core.lca.LcaResult`, and :class:`~app.core.simulation.EconomicResult`
into per-lifecycle-phase vectors extended with downtime and economic cost scalars,
ready for stacked charts or Excel export.
"""

from __future__ import annotations

import numpy as np

from app.core.config import PelcaConfig
from app.core.lca import LcaResult
from app.core.simulation import SimulationResult


def build_phase_totals(
    simulation_result: SimulationResult,
    lca: LcaResult,
    config: PelcaConfig,
    downtime: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]:
    """Aggregate per-phase environmental impacts and append downtime and cost scalars.

    For each lifecycle phase the environmental impact is first reduced to a
    ``(nb_ei,)`` vector by summing over RUs and averaging over Monte Carlo
    iterations (where applicable).  Two extra elements are then appended —
    the downtime contribution (hours) and the economic cost (€) — so every
    returned array has shape ``(nb_ei + 2,)`` and can be used directly as a
    column in a stacked bar chart or Excel sheet.

    The two appended values are always ordered as ``[dwt_value, eco_value]``,
    matching the axis labels ``["DWT (h)", "ECO (€)"]``.

    Args:
        simulation_result: SimulationResult,
        lca: Static LCA impact arrays from :func:`~app.core.lca.lca_generator`.
        config: Full PELCA run configuration, used to build the x-axis labels.
        downtime: Cumulative downtime array per RU.
            Shape ``(usage_time, nb_ite_mc, nb_ru)``.  When ``None``, both
            downtime slots are filled with ``0.0``.

    Returns:
        A 6-tuple ``(manu_total, use_total, cur_maint_total, prev_maint_total,
        eol_total, x_labels)`` where each phase array has shape
        ``(nb_ei + 2,)`` and ``x_labels`` is a list of ``nb_ei + 2`` strings
        suitable for chart axes.
    """
    # Alias
    env = simulation_result.environmental
    eco = simulation_result.economic
    downtime = simulation_result.downtime

    # Resolve downtime scalars: MC- and RU-averaged totals at end of service life.
    dwt_planned_mean = downtime.planned_mean
    dwt_cur_mean = downtime.curative_mean

    # Sum manufacturing impacts over RUs → (nb_ei,).
    manu_env = lca.manufacturing.sum(axis=1)

    # Sum use-phase impacts over activities at t_last → (nb_ei,).
    use_env = env.use[-1, :, :].sum(axis=-1)

    # MC-average planned maintenance over RUs at -1 → (nb_ei,).
    prev_maint_env = np.mean(env.planned_maintenance[-1, :, :, :], axis=0).sum(axis=-1)

    # MC-average curative maintenance over RUs at -1 → (nb_ei,).
    cur_maint_env = np.mean(env.curative_maintenance[-1, :, :, :], axis=0).sum(axis=-1)

    # Sum end-of-life impacts over RUs → (nb_ei,).
    eol_env = lca.eol.sum(axis=1)

    # Manufacturing: no downtime contribution.
    manu_total = np.append(manu_env, [0.0, float(eco.manufacturing.sum())])

    # Use phase: no downtime contribution.
    use_total = np.append(use_env, [0.0, float(eco.use[-1].sum())])

    # Curative maintenance: downtime from curative events.
    cur_maint_total = np.append(
        cur_maint_env,
        [dwt_cur_mean, float(eco.curative_maintenance[-1].sum(axis=-1).mean())],
    )

    # Planned maintenance: downtime from scheduled interventions.
    prev_maint_total = np.append(
        prev_maint_env,
        [dwt_planned_mean, float(eco.planned_maintenance[-1].sum(axis=-1).mean())],
    )

    # End of life: no downtime contribution.
    eol_total = np.append(eol_env, [0.0, float(eco.end_of_life.sum())])

    # Build x-axis labels: one per EI method, then DWT and cost columns.
    ei_labels = [f"{n} ({u})" for n, u in zip(config.lcia.names, config.lcia.units, strict=False)]
    x_labels = ei_labels + ["DWT (h)", "ECO (€)"]

    return manu_total, use_total, cur_maint_total, prev_maint_total, eol_total, x_labels
