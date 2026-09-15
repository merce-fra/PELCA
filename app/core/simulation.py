"""Staircase Monte Carlo simulation engine.

Executes the Life Cycle Impact Curve simulation over the full service life of a
power-electronics system, accumulating environmental impacts and economic costs
across every time step and Monte Carlo iteration.

Entry point: :func:`run_simulation`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from scipy.stats import weibull_min

from app.core.config import FailureConfig, MaintenanceConfig, PelcaConfig, SimulationConfig
from app.core.lca import LcaResult

logger = logging.getLogger(__name__)


# ── Result types ──────────────────────────────────────────────────────────────


@dataclass
class SimulationResult:
    """Time-series simulation results for a single PELCA run.

    Attributes:
        environmental: Time-series environmental impact arrays.
        economic: Time-series economic cost arrays.
        downtime: Cumulative planned and curative maintenance downtime per RU.
            Each array has shape ``(usage_time, nb_ite_mc, nb_ru)``.
    """

    environmental: EnvironmentalResult
    economic: EconomicResult
    downtime: DowntimeResult


@dataclass
class DowntimeResult:
    """Time-series downtime arrays from a staircase simulation.

    The regular time axis has length ``service_life * time_step + 1`` (``usage_time``).
    Planned downtime is split between preventive maintenance and modernization;
    ``planned`` is exposed as the sum of both contributions for backward compatibility.

    Attributes:
        preventive: Cumulative preventive maintenance downtime per RU.
            Shape ``(usage_time, nb_ite_mc, nb_ru)``.
        modernization: Cumulative modernization downtime per RU.
            Shape ``(usage_time, nb_ite_mc, nb_ru)``.
        curative: Cumulative curative maintenance downtime per RU.
            Shape ``(usage_time, nb_ite_mc, nb_ru)``.
    """

    preventive: np.ndarray
    modernization: np.ndarray
    curative: np.ndarray

    @property
    def planned(self) -> np.ndarray:
        """Cumulative planned downtime per RU (preventive + modernization).

        Shape ``(usage_time, nb_ite_mc, nb_ru)``.
        """
        return self.preventive + self.modernization

    @property
    def per_maintenance(self) -> np.ndarray:
        """Cumulative total maintenance downtime (planned + curative) per RU.

        Shape ``(usage_time, nb_ite_mc, nb_ru)``.
        """
        return self.planned + self.curative

    @property
    def planned_mean(self) -> float:
        """Total planned downtime at end of service life, MC- and RU-averaged."""
        return float(self.planned[-1, :, :].sum(axis=-1).mean())

    @property
    def preventive_mean(self) -> float:
        """Total preventive downtime at end of service life, MC- and RU-averaged."""
        return float(self.preventive[-1, :, :].sum(axis=-1).mean())

    @property
    def modernization_mean(self) -> float:
        """Total modernization downtime at end of service life, MC- and RU-averaged."""
        return float(self.modernization[-1, :, :].sum(axis=-1).mean())

    @property
    def curative_mean(self) -> float:
        """Total curative downtime at end of service life, MC- and RU-averaged."""
        return float(self.curative[-1, :, :].sum(axis=-1).mean())


@dataclass
class EnvironmentalResult:
    """Time-series environmental impact arrays from a staircase simulation.

    The regular time axis has length ``service_life * time_step + 1`` (``usage_time``).
    ``total`` has one extra step at index ``usage_time`` that incorporates end-of-life.

    Attributes:
        total: Cumulative total EI including end-of-life at the last step.
            Shape ``(usage_time + 1, nb_ite_mc, nb_ei)``.
        manufacturing: Manufacturing EI per activity from LCA; punctual, no time
            or MC dimension. Shape ``(nb_ei, nb_ru_manu)``.
        use: Cumulative use-phase EI per activity, averaged across MC iterations.
            Shape ``(usage_time, nb_ei, nb_activity_use)``.
        preventive_maintenance: Cumulative preventive maintenance EI per RU.
            Shape ``(usage_time, nb_ite_mc, nb_ei, nb_ru)``.
        modernization: Cumulative modernization EI per RU.
            Shape ``(usage_time, nb_ite_mc, nb_ei, nb_ru)``.
        curative_maintenance: Cumulative curative maintenance EI per RU.
            Shape ``(usage_time, nb_ite_mc, nb_ei, nb_ru)``.
        end_of_life: End-of-life EI per activity from LCA; punctual, no time
            or MC dimension. Shape ``(nb_ei, nb_ru_eol)``.
        number_of_faults: Cumulative replacement count per RU.
            Shape ``(usage_time, nb_ite_mc, nb_ru)``.
        fault_cause: Fault mode label per event (``"Early"``, ``"Random"``,
            ``"Wearout"`` or ``""``). Shape ``(usage_time, nb_ite_mc, nb_ru)``.
        wcdf_total: Deterministic total-system failure CDF.
            Shape ``(usage_time,)``.
        wcdf_per_ru: Deterministic per-RU failure CDF.
            Shape ``(usage_time, nb_ru)``.
        ru_age: Tracked RU age in years after replacements.
            Shape ``(usage_time, nb_ite_mc, nb_ru)``.
    """

    total: np.ndarray
    manufacturing: np.ndarray
    use: np.ndarray
    preventive_maintenance: np.ndarray
    modernization: np.ndarray
    curative_maintenance: np.ndarray
    end_of_life: np.ndarray
    number_of_faults: np.ndarray
    fault_cause: np.ndarray
    wcdf_total: np.ndarray
    wcdf_per_ru: np.ndarray
    ru_age: np.ndarray

    @property
    def planned_maintenance(self) -> np.ndarray:
        """Cumulative planned maintenance EI per RU (preventive + modernization).

        Shape ``(usage_time, nb_ite_mc, nb_ei, nb_ru)``.
        """
        return self.preventive_maintenance + self.modernization

    @property
    def manufacturing_total(self) -> np.ndarray:
        """Total manufacturing EI per method, summed across activities. Shape ``(nb_ei,)``."""
        return self.manufacturing.sum(axis=-1)

    @property
    def use_total(self) -> np.ndarray:
        """Cumulative use EI per step and method, summed across activities.

        Shape ``(usage_time, nb_ei)``.
        """
        return self.use.sum(axis=-1)

    @property
    def preventive_maintenance_total(self) -> np.ndarray:
        """Cumulative preventive maintenance EI, summed over RUs.

        Shape ``(usage_time, nb_ite_mc, nb_ei)``.
        """
        return self.preventive_maintenance.sum(axis=-1)

    @property
    def modernization_total(self) -> np.ndarray:
        """Cumulative modernization EI, summed over RUs.

        Shape ``(usage_time, nb_ite_mc, nb_ei)``.
        """
        return self.modernization.sum(axis=-1)

    @property
    def planned_maintenance_total(self) -> np.ndarray:
        """Cumulative planned maintenance EI, summed over RUs.

        Shape ``(usage_time, nb_ite_mc, nb_ei)``.
        """
        return self.planned_maintenance.sum(axis=-1)

    @property
    def curative_maintenance_total(self) -> np.ndarray:
        """Cumulative curative maintenance EI, summed over RUs.

        Shape ``(usage_time, nb_ite_mc, nb_ei)``.
        """
        return self.curative_maintenance.sum(axis=-1)

    @property
    def end_of_life_total(self) -> np.ndarray:
        """Total end-of-life EI per method, summed across activities. Shape ``(nb_ei,)``."""
        return self.end_of_life.sum(axis=-1)

    @property
    def preventive_maintenance_mean(self) -> np.ndarray:
        """MC-averaged preventive maintenance EI.

        Shape ``(nb_ei, nb_ru)``.
        """
        return np.mean(self.preventive_maintenance[-1, :, :, :], axis=0)

    @property
    def modernization_mean(self) -> np.ndarray:
        """MC-averaged modernization EI.

        Shape ``(nb_ei, nb_ru)``.
        """
        return np.mean(self.modernization[-1, :, :, :], axis=0)

    @property
    def planned_maintenance_mean(self) -> np.ndarray:
        """MC-averaged planned maintenance EI (preventive + modernization).

        Shape ``(nb_ei, nb_ru)``.
        """
        return np.mean(self.planned_maintenance[-1, :, :, :], axis=0)

    @property
    def curative_maintenance_mean(self) -> np.ndarray:
        """MC-averaged curative maintenance EI.

        Shape ``(nb_ei, nb_ru)``.
        """
        return np.mean(self.curative_maintenance[-1, :, :, :], axis=0)


@dataclass
class EconomicResult:
    """Time-series economic cost arrays from a staircase simulation.

    The regular time axis has length ``service_life * time_step + 1`` (``usage_time``).
    ``total`` has one extra step at index ``usage_time`` that incorporates end-of-life cost.

    Attributes:
        total: Cumulative total cost including end-of-life at the last step.
            Shape ``(usage_time + 1, nb_ite_mc)``.
        manufacturing: Raw manufacturing cost per RU from ``CostConfig.raw_cost``.
            Shape ``(nb_ru_manu,)``.
        use: Cumulative energy use cost per RU per step, MC-profile-averaged.
            Shape ``(usage_time, nb_ru)``.
        preventive_maintenance: Cumulative preventive maintenance cost per RU.
            Shape ``(usage_time, nb_ite_mc, nb_ru)``.
        modernization: Cumulative modernization cost per RU.
            Shape ``(usage_time, nb_ite_mc, nb_ru)``.
        curative_maintenance: Cumulative curative maintenance cost per RU.
            Shape ``(usage_time, nb_ite_mc, nb_ru)``.
        end_of_life: End-of-life cost per RU from ``CostConfig.eol_cost``.
            Shape ``(nb_ru_eol,)``.
    """

    total: np.ndarray
    manufacturing: np.ndarray
    use: np.ndarray
    preventive_maintenance: np.ndarray
    modernization: np.ndarray
    curative_maintenance: np.ndarray
    end_of_life: np.ndarray

    @property
    def planned_maintenance(self) -> np.ndarray:
        """Cumulative planned maintenance cost per RU (preventive + modernization).

        Shape ``(usage_time, nb_ite_mc, nb_ru)``.
        """
        return self.preventive_maintenance + self.modernization


# ── Public API ────────────────────────────────────────────────────────────────


def run_simulation(
    lca_result: LcaResult,
    config: PelcaConfig,
) -> SimulationResult:
    """Run the staircase Monte Carlo simulation.

    Translates a pre-computed ``LcaResult`` and a full ``PelcaConfig`` into
    cumulative time-series arrays covering the entire service life.

    Args:
        lca_result: Environmental impacts per RU, produced by ``lca_generator``
            or loaded from ``LCA output.xlsx`` via :mod:`app.io.lca_io`.
        config: Complete PELCA run configuration parsed from the input Excel
            file by :class:`app.io.reader.ExcelInputReader`.

    Returns:
        A ``SimulationResult`` object with time-series arrays from step 0 to
        ``service_life * time_step`` inclusive.
    """
    sim = config.simulation
    nb_ite_mc = sim.mc_iterations
    nb_ru = lca_result.nb_ru

    logger.info(
        "Starting simulation: service_life=%d yr, time_step=%d/yr, nb_ite_mc=%d, nb_ru=%d",
        sim.service_life,
        sim.time_step,
        nb_ite_mc,
        nb_ru,
    )
    logger.info(
        "Failure flags — early_enabled=%s, random_enabled=%s, wearout_enabled=%s",
        sim.failure.early_enabled,
        sim.failure.random_enabled,
        sim.failure.wearout_enabled,
    )

    # Assign a fixed mission profile to each MC iteration (1-based index).
    profile_per_mc = _assign_mission_profiles(sim, nb_ite_mc)

    # Time vector in years (avoid zero to prevent Weibull division errors).
    epsilon = 1e-10
    t = np.linspace(epsilon, sim.service_life, sim.usage_time)

    # Weibull CDF look-up tables and conditional fault-type probabilities.
    weibull_e, weibull_r, weibull_w = _build_weibull_cdfs(
        t, sim.failure, sim.mission_profile_probs, sim.time_step
    )
    prob_e, prob_r, prob_w = _build_fault_type_probabilities(weibull_e, weibull_r, weibull_w)

    # Mean use-phase EI per activity per time step, averaged across MC iterations.
    mean_use_ei_per_act_step = _compute_mean_use_ei_per_act_step(lca_result, profile_per_mc, sim)

    # Mean energy use cost per RU per time step, averaged across MC iterations.
    mean_use_cost_per_act_step = _compute_mean_use_cost_per_act_step(sim, profile_per_mc)

    # Initial manufacturing cost (raw materials only, no assembly/disassembly).
    cost_manu_initial = float(sim.cost.manufacturing.sum())

    simulation_result = _run_loop(
        nb_ru=nb_ru,
        profile_per_mc=profile_per_mc,
        lca_result=lca_result,
        mean_use_ei_per_act_step=mean_use_ei_per_act_step,
        mean_use_cost_per_act_step=mean_use_cost_per_act_step,
        cost_manu_initial=cost_manu_initial,
        weibull_e=weibull_e,
        weibull_r=weibull_r,
        weibull_w=weibull_w,
        prob_e=prob_e,
        prob_r=prob_r,
        prob_w=prob_w,
        sim=sim,
    )

    logger.info("Simulation complete.")
    return simulation_result


# ── Internal helpers ──────────────────────────────────────────────────────────


def _assign_mission_profiles(sim: SimulationConfig, nb_ite_mc: int) -> np.ndarray:
    """Return a 1-D integer array of shape ``(nb_ite_mc,)`` with 1-based profile indices.

    Each MC iteration draws one profile at the start and keeps it for the
    entire service life. Profiles are selected with probability proportional
    to ``sim.mission_profile_probs``.

    Args:
        sim: Simulation configuration.
        nb_ite_mc: Number of Monte Carlo iterations.

    Returns:
        Array of 1-based profile indices, one per MC iteration.
    """
    nb_profiles = sim.nb_mission_profiles
    if nb_profiles == 1:
        return np.ones(nb_ite_mc, dtype=int)

    # Draw profile indices (0-based) with nominal probabilities, then shift to 1-based.
    return np.random.choice(nb_profiles, size=nb_ite_mc, p=sim.mission_profile_probs) + 1


def _build_weibull_cdfs(
    t: np.ndarray,
    failure: FailureConfig,
    mission_profile_probs: np.ndarray,
    time_step: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build Weibull CDF look-up tables indexed by ``(time_index, ru_index)``.

    For each failure mode, computes one CDF per mission profile and combines them
    as a probability-weighted average: ``CDF_eff = Σ pₖ × CDF_k(t, σₖ, βₖ)``.
    This is the statistically correct combination for a per-step profile draw model:
    averaging the CDF values (not the parameters) avoids the Jensen-inequality bias
    that arises when a non-linear function is applied to averaged inputs.
    Disabled failure modes return a zero-filled table.

    Args:
        t: Time vector in years. Shape ``(usage_time,)``.
        failure: Weibull parameters per RU per profile.
            Each array has shape ``(nb_ru, nb_profiles)``.
        mission_profile_probs: Fraction of operating time for each profile.
            Values sum to ``1.0``. Shape ``(nb_profiles,)``.
        time_step: Number of simulation steps per year.

    Returns:
        ``(weibull_e, weibull_r, weibull_w)`` – each shape ``(usage_time, nb_ru)``.
    """
    nb_ru = failure.sigma_early.shape[0]
    nb_profiles = failure.sigma_early.shape[1]
    usage_time = len(t)
    dt = 1.0 / time_step

    # Profile probabilities passed directly from SimulationConfig.
    probs = mission_profile_probs

    # time_shifted[i, j] = t[i] – dt  →  age at start of time step i (in years).
    time_matrix = np.broadcast_to(t[:, np.newaxis], (usage_time, nb_ru)).copy()
    time_shifted = time_matrix - dt  # shift back by one step

    weibull_e = np.zeros((usage_time, nb_ru), dtype=float)
    weibull_r = np.zeros((usage_time, nb_ru), dtype=float)
    weibull_w = np.zeros((usage_time, nb_ru), dtype=float)

    mode_mask = failure.mode_enabled_by_ru
    # Effective enable per RU: the global flag must be True AND the RU must
    # have both sigma and beta configured.  Disabling either level sets the
    # Weibull table column to zero, which propagates automatically through
    # the CDF, the conditional probabilities, and the fault classification
    # — no additional flag checks are needed downstream.
    eff_early = mode_mask.early if failure.early_enabled else np.zeros(nb_ru, dtype=bool)
    eff_random = mode_mask.random if failure.random_enabled else np.zeros(nb_ru, dtype=bool)
    eff_wearout = mode_mask.wearout if failure.wearout_enabled else np.zeros(nb_ru, dtype=bool)

    # For each active mode, accumulate the probability-weighted per-profile CDF.
    # Disabled RUs receive safe parameter defaults (σ=1, β=1) to avoid scipy
    # warnings; their contribution is masked to zero in the same expression.
    if np.any(eff_early):
        for k in range(nb_profiles):
            sigma_e = np.where(eff_early, failure.sigma_early[:, k], 1.0)
            beta_e = np.where(eff_early, failure.beta_early[:, k], 1.0)
            weibull_e += probs[k] * np.where(
                eff_early, weibull_min.cdf(time_shifted, beta_e, scale=sigma_e), 0.0
            )

    if np.any(eff_random):
        for k in range(nb_profiles):
            sigma_r = np.where(eff_random, failure.sigma_random[:, k], 1.0)
            beta_r = np.where(eff_random, failure.beta_random[:, k], 1.0)
            weibull_r += probs[k] * np.where(
                eff_random, weibull_min.cdf(time_shifted, beta_r, scale=sigma_r), 0.0
            )

    if np.any(eff_wearout):
        for k in range(nb_profiles):
            sigma_w = np.where(eff_wearout, failure.sigma_wearout[:, k], 1.0)
            beta_w = np.where(eff_wearout, failure.beta_wearout[:, k], 1.0)
            weibull_w += probs[k] * np.where(
                eff_wearout, weibull_min.cdf(time_shifted, beta_w, scale=sigma_w), 0.0
            )

    return weibull_e, weibull_r, weibull_w


def _build_fault_type_probabilities(
    weibull_e: np.ndarray,
    weibull_r: np.ndarray,
    weibull_w: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute the conditional probability of each fault mode given a fault event.

    ``prob_e[i, j]`` is the probability that a fault on RU ``j`` at time index
    ``i`` is an early failure, conditioned on a failure having occurred.

    Args:
        weibull_e: Early-failure CDF table. Shape ``(usage_time, nb_ru)``.
        weibull_r: Random-failure CDF table. Shape ``(usage_time, nb_ru)``.
        weibull_w: Wearout-failure CDF table. Shape ``(usage_time, nb_ru)``.

    Returns:
        ``(prob_e, prob_r, prob_w)`` – conditional probabilities, same shapes
        as inputs.
    """
    wcdf_sum = weibull_e + weibull_r + weibull_w
    nonzero = wcdf_sum != 0

    prob_e = np.divide(weibull_e, wcdf_sum, out=np.zeros_like(weibull_e), where=nonzero)
    prob_r = np.divide(weibull_r, wcdf_sum, out=np.zeros_like(weibull_r), where=nonzero)
    prob_w = np.divide(weibull_w, wcdf_sum, out=np.zeros_like(weibull_w), where=nonzero)

    return prob_e, prob_r, prob_w


def _compute_mean_use_ei_per_act_step(
    lca_result: LcaResult,
    profile_per_mc: np.ndarray,
    sim: SimulationConfig,
) -> np.ndarray:
    """Compute the MC-frequency-weighted mean use-phase ei per activity per time step.

    Averages per-profile use arrays weighted by the fraction of MC iterations
    assigned to each profile, then scales by ``hours_per_year / time_step``.

    Args:
        lca_result: Precomputed LCA result containing ``use_per_profile``.
        profile_per_mc: 1-based profile assignment per MC iteration.
        sim: Simulation configuration.

    Returns:
        Array of shape ``(nb_ei, nb_activity_use)`` representing the mean
        per-activity use-phase ei for one time step.
    """
    nb_profiles = sim.nb_mission_profiles
    # Compute frequency-based weights for each profile.
    counts = np.bincount(profile_per_mc - 1, minlength=nb_profiles).astype(float)
    weights = counts / counts.sum() if counts.sum() > 0 else np.full(nb_profiles, 1.0 / nb_profiles)
    # Weighted average of per-profile use arrays.
    mean_use: np.ndarray = np.sum(
        [weights[p] * lca_result.use_per_profile[p] for p in range(nb_profiles)],
        axis=0,
    )  # (nb_ei, nb_activity_use)
    # Scale to the per-time-step amount.
    return mean_use * sim.hours_per_year / sim.time_step


def _compute_mean_use_cost_per_act_step(
    sim: SimulationConfig,
    profile_per_mc: np.ndarray,
) -> np.ndarray:
    """Compute the MC-frequency-weighted mean energy use cost per activity per time step.

    For each mission profile, the per-activity cost is ``energy_per_act * kwh_cost *
    hours_per_year / time_step``.  Profiles are averaged weighted by the fraction
    of MC iterations assigned to each, matching the approach used for use-phase ei.

    Args:
        sim: Simulation configuration.
        profile_per_mc: 1-based profile assignment per MC iteration.

    Returns:
        Per-activity energy cost for one time step. Shape ``(nb_activity_use,)``.
    """
    nb_profiles = sim.nb_mission_profiles
    kwh_cost = sim.cost.kwh_cost
    activity_names = list(sim.energy_amounts.keys())

    # Build per-profile per-activity cost vectors.
    per_profile: list[np.ndarray] = []
    for p in range(1, nb_profiles + 1):
        energy_vals: list[float] = [
            sim.energy_amounts[name][p - 1]
            if len(sim.energy_amounts[name]) >= p
            else sim.energy_amounts[name][0]
            for name in activity_names
        ]
        ea = energy_vals[:]
        energy_per_act = np.array(
            [0.0 if cost == 0 else ea.pop(0) for cost in kwh_cost], dtype=float
        )
        per_profile.append(energy_per_act * kwh_cost * sim.hours_per_year / sim.time_step)

    # Weighted mean by MC profile frequency.
    counts = np.bincount(profile_per_mc - 1, minlength=nb_profiles).astype(float)
    weights = counts / counts.sum() if counts.sum() > 0 else np.full(nb_profiles, 1.0 / nb_profiles)
    return np.sum([weights[p] * per_profile[p] for p in range(nb_profiles)], axis=0)


def _expand_maintenance_schedule(
    schedule: np.ndarray,
    profile_per_mc: np.ndarray,
    nb_profiles: int,
    nb_ite_mc: int,
) -> np.ndarray:
    """Expand a ``(nb_ru, nb_profiles)`` maintenance schedule to ``(nb_ite_mc, nb_ru)``.

    Each MC row receives the schedule for its assigned mission profile.

    Args:
        schedule: Per-RU, per-profile maintenance schedule in years.
            Shape ``(nb_ru, nb_profiles)``.
        profile_per_mc: 1-based profile index per MC iteration.
        nb_profiles: Total number of mission profiles.
        nb_ite_mc: Number of MC iterations.

    Returns:
        Shape ``(nb_ite_mc, nb_ru)``.
    """
    nb_ru = schedule.shape[0]
    if nb_profiles == 1:
        return np.tile(schedule[:, 0], (nb_ite_mc, 1))

    expanded = np.zeros((nb_ite_mc, nb_ru), dtype=float)
    for it in range(nb_ite_mc):
        expanded[it] = schedule[:, profile_per_mc[it] - 1]
    return expanded


def _lookup_wcdf(
    ru_age: np.ndarray,
    weibull_e: np.ndarray,
    weibull_r: np.ndarray,
    weibull_w: np.ndarray,
    time_step: int,
) -> np.ndarray:
    """Look up the composite failure CDF at each RU's current age.

    Converts component ages (in years) to table indices and reads the
    pre-computed Weibull CDF tables by fancy indexing.

    Args:
        ru_age: Current age of each ``(mc, ru)`` pair in years.
            Shape ``(nb_ite_mc, nb_ru)``.
        weibull_e: Early-failure CDF table. Shape ``(usage_time, nb_ru)``.
        weibull_r: Random-failure CDF table. Shape ``(usage_time, nb_ru)``.
        weibull_w: Wearout-failure CDF table. Shape ``(usage_time, nb_ru)``.
        time_step: Simulation steps per year, used to convert age to index.

    Returns:
        Combined CDF ``1 – Π(1 – P_mode)`` per ``(mc, ru)`` pair.
        Shape ``(nb_ite_mc, nb_ru)``.
    """
    nb_ru = ru_age.shape[1]
    max_idx = weibull_e.shape[0] - 1
    indices = np.clip(np.round(ru_age * time_step).astype(int), 0, max_idx)
    ru_idx = np.arange(nb_ru)

    # The Weibull tables already encode both global and per-RU disabling
    # (columns are zero for disabled modes); no extra flag checks needed.
    e = weibull_e[indices, ru_idx]
    r = weibull_r[indices, ru_idx]
    w = weibull_w[indices, ru_idx]

    return 1.0 - (1.0 - e) * (1.0 - r) * (1.0 - w)


def _run_loop(
    nb_ru: int,
    profile_per_mc: np.ndarray,
    lca_result: LcaResult,
    mean_use_ei_per_act_step: np.ndarray,
    mean_use_cost_per_act_step: np.ndarray,
    cost_manu_initial: float,
    weibull_e: np.ndarray,
    weibull_r: np.ndarray,
    weibull_w: np.ndarray,
    prob_e: np.ndarray,
    prob_r: np.ndarray,
    prob_w: np.ndarray,
    sim: SimulationConfig,
) -> SimulationResult:
    """Execute the main time-stepping staircase loop.

    Iterates from step 1 to ``usage_time - 1``, applying preventive and
    curative maintenance events, accumulating environmental impacts and costs,
    and tracking RU ages and fault statistics.  Appends a final end-of-life
    step at index ``usage_time`` to ``total`` (environmental and economic).

    Args:
        t: Time vector in years.
        usage_time: Number of regular simulation steps (``service_life * time_step + 1``).
        nb_ite_mc: Number of Monte Carlo iterations.
        nb_ru: Total number of replaceable units.
        profile_per_mc: 1-based profile assignment per MC iteration.
        ei_manu: Manufacturing EI per activity. Shape ``(nb_ei, nb_ru_manu)``.
        ei_planned_maintenance: Planned maintenance EI per RU. Shape ``(nb_ei, nb_ru)``.
        ei_curative_maintenance: Curative maintenance EI per RU. Shape ``(nb_ei, nb_ru)``.
        ei_eol: End-of-life EI per activity. Shape ``(nb_ei, nb_ru_eol)``.
        mean_use_ei_per_act_step: MC-averaged use EI per activity per time step.
            Shape ``(nb_ei, nb_activity_use)``.
        mean_use_cost_per_act_step: MC-profile-averaged energy use cost per RU per time step.
            Shape ``(nb_ru,)``.
        cost_manu_initial: Initial manufacturing cost (scalar).
        raw_cost: Raw manufacturing cost per RU. Shape ``(nb_ru_manu,)``.
        eol_cost: End-of-life cost per RU. Shape ``(nb_ru_eol,)``.
        weibull_e: Early-failure CDF table.
        weibull_r: Random-failure CDF table.
        weibull_w: Wearout-failure CDF table.
        prob_e: Conditional early-failure probability.
        prob_r: Conditional random-failure probability.
        prob_w: Conditional wearout-failure probability.
        sim: Simulation configuration.

    Returns:
        A pair ``(EnvironmentalResult, EconomicResult)``.
    """
    # ╔════════════════════════════════════════════════════════╗
    # ║      Parameter extraction to improve readability       ║
    # ╚════════════════════════════════════════════════════════╝
    raw_cost = sim.cost.manufacturing
    eol_cost = sim.cost.end_of_life
    ei_manu = lca_result.manufacturing
    ei_planned_maintenance = lca_result.planned_maintenance
    ei_curative_maintenance = lca_result.curative_maintenance
    ei_eol = lca_result.eol
    usage_time: int = sim.usage_time
    nb_ite_mc: int = sim.mc_iterations
    failure: FailureConfig = sim.failure
    maintenance: MaintenanceConfig = sim.maintenance
    time_step: int = sim.time_step
    nb_profiles: int = sim.nb_mission_profiles
    dt: float = 1.0 / time_step

    rm = maintenance.replacement_matrix
    row_r, col_r = rm.shape
    rm_values = rm.values  # (row_r, col_r) numpy array for fast row indexing
    planned_maint_cost_per_ru = sim.cost.planned  # (nb_ru,)
    curative_maint_cost_per_ru = sim.cost.curative  # (nb_ru,)

    # ── Derived dimensions ────────────────────────────────────────────────────
    nb_ei: int = lca_result.nb_env_impacts
    nb_act_use: int = lca_result.nb_activity_use

    # Pre-computed scalar totals for building the grand total at each step.
    ei_manu_total = ei_manu.sum(axis=-1)  # (nb_ei,)
    ei_eol_total = ei_eol.sum(axis=-1)  # (nb_ei,)

    # ── Random draw matrices ───────────────────────────────────────────────────
    # random_fault_time[mc, ru]: threshold compared against composite CDF to
    # detect a fault event.  Refreshed when a replacement occurs.
    random_fault_time = np.random.uniform(0.0, 1.0, size=(nb_ite_mc, nb_ru))
    # random_fault_type[mc, ru]: threshold used to determine the fault mode
    # (Early / Random / Wearout) given that a fault has occurred.
    random_fault_type = np.random.uniform(0.0, 1.0, size=(nb_ite_mc, nb_ru))

    # ── State arrays ──────────────────────────────────────────────────────────
    ru_age = np.zeros((usage_time, nb_ite_mc, nb_ru), dtype=float)
    # replacement[mc, ru_source, ru_dest]: replacement pattern for one fault event.
    replacement = np.zeros((nb_ite_mc, row_r, col_r), dtype=float)
    # replacement_or[mc, ru]: binary indicator – 1 if RU was replaced this step.
    replacement_or = np.zeros((nb_ite_mc, nb_ru), dtype=float)
    random_replacement_ratio = np.random.uniform(0.0, 1.0, size=(nb_ite_mc, row_r, col_r))

    # ── Environmental impact accumulators ─────────────────────────────────────
    # total: (usage_time + 1, nb_ite_mc, nb_ei) — extra step reserved for EoL.
    ei_total = np.zeros((usage_time + 1, nb_ite_mc, nb_ei), dtype=float)
    ei_total[0] = ei_manu_total  # step 0: manufacturing only, same for all MC

    # use EI: (usage_time, nb_ei, nb_act_use) — profile-weighted average, no MC dimension.
    ei_use_per_act = np.zeros((usage_time, nb_ei, nb_act_use), dtype=float)

    # planned/curative: (usage_time, nb_ite_mc, nb_ei, nb_ru) — per-RU, cumulative.
    # Preventive and modernization are tracked separately so a downstream bar plot
    # can attribute per-RU impacts to each calendar; the total planned contribution
    # is exposed by the ``EnvironmentalResult.planned_maintenance`` property.
    ei_preventive_maint = np.zeros((usage_time, nb_ite_mc, nb_ei, nb_ru), dtype=float)
    ei_modernization = np.zeros((usage_time, nb_ite_mc, nb_ei, nb_ru), dtype=float)
    ei_curative_maint = np.zeros((usage_time, nb_ite_mc, nb_ei, nb_ru), dtype=float)

    # -- Downtime: separate preventive, modernization and curative accumulators.
    downtime_preventive_per_ru = np.zeros((usage_time, nb_ite_mc, nb_ru), dtype=float)
    downtime_modernization_per_ru = np.zeros((usage_time, nb_ite_mc, nb_ru), dtype=float)
    downtime_curative_per_ru = np.zeros((usage_time, nb_ite_mc, nb_ru), dtype=float)

    # ── Cost accumulators ─────────────────────────────────────────────────────
    # use: (usage_time, nb_act_use) — MC-profile-averaged cumulative energy cost per use activity.
    cost_use_per_act = np.zeros((usage_time, nb_act_use), dtype=float)
    # preventive/modernization/curative: (usage_time, nb_ite_mc, nb_ru) — cumulative per RU and MC.
    cost_preventive_maint_per_ru = np.zeros((usage_time, nb_ite_mc, nb_ru), dtype=float)
    cost_modernization_per_ru = np.zeros((usage_time, nb_ite_mc, nb_ru), dtype=float)
    cost_curative_maint_per_ru = np.zeros((usage_time, nb_ite_mc, nb_ru), dtype=float)
    # total cost: (usage_time + 1, nb_ite_mc) — extra step for EoL.
    cost_total = np.zeros((usage_time + 1, nb_ite_mc), dtype=float)
    cost_total[0] = cost_manu_initial

    # ── Fault tracking ────────────────────────────────────────────────────────
    number_of_faults = np.zeros((usage_time, nb_ite_mc, nb_ru), dtype=float)
    fault_cause = np.full((usage_time, nb_ite_mc, nb_ru), "", dtype="<U10")

    # ── Deterministic Weibull summary (mean CDF, no MC variability) ───────────
    wcdf_det = 1.0 - (1.0 - weibull_e) * (1.0 - weibull_r) * (1.0 - weibull_w)
    wcdf_per_ru = wcdf_det  # (usage_time, nb_ru)
    wcdf_total = 1.0 - np.prod(1.0 - wcdf_det, axis=1)  # (usage_time,)

    # ── Maintenance schedule expanded to (nb_ite_mc, nb_ru) ──────────────────
    maint_schedule_mc = _expand_maintenance_schedule(
        maintenance.preventive_schedule, profile_per_mc, nb_profiles, nb_ite_mc
    )
    mod_schedule_mc = _expand_maintenance_schedule(
        maintenance.modernization_schedule, profile_per_mc, nb_profiles, nb_ite_mc
    )

    # ── Composite CDF trackers: shape (nb_ite_mc, nb_ru) ─────────────────────
    wcdf_prev = np.zeros((nb_ite_mc, nb_ru), dtype=float)
    wcdf_curr = np.zeros((nb_ite_mc, nb_ru), dtype=float)

    # ═════════════════════════════════════════════════════════════════════════
    #                          Time-stepping loop
    # ═════════════════════════════════════════════════════════════════════════
    for step in range(1, usage_time):
        # Age increment.
        ru_age[step] = ru_age[step - 1] + dt

        # ── Planned maintenance (preventive + modernization) ─────────────────
        # Per-RU preventive / modernization EI for this step: (nb_ite_mc, nb_ei, nb_ru).
        prev_step_per_ru = np.zeros((nb_ite_mc, nb_ei, nb_ru), dtype=float)
        mod_step_per_ru = np.zeros((nb_ite_mc, nb_ei, nb_ru), dtype=float)
        # Per-RU cost step: (nb_ite_mc, nb_ru), split per planned-maintenance subtype.
        prev_cost_step_per_ru = np.zeros((nb_ite_mc, nb_ru), dtype=float)
        mod_cost_step_per_ru = np.zeros((nb_ite_mc, nb_ru), dtype=float)

        # Downtime step contributions per subtype.
        downtime_prev_step_per_ru = np.zeros((nb_ite_mc, nb_ru), dtype=float)
        downtime_mod_step_per_ru = np.zeros((nb_ite_mc, nb_ru), dtype=float)
        downtime_curative_step_per_ru = np.zeros((nb_ite_mc, nb_ru), dtype=float)

        # Build per-RU due masks for preventive (age-based, resets after each
        # replacement) and modernization (absolute simulation calendar). When
        # both calendars match the same RU, modernization takes over and the
        # replacement impact is attributed to the modernization bucket only.
        prev_due_mask = np.zeros((nb_ite_mc, nb_ru), dtype=bool)
        mod_due_mask = np.zeros((nb_ite_mc, nb_ru), dtype=bool)

        if maintenance.prev_enabled:
            prev_steps = (maint_schedule_mc * time_step).astype(int)
            age_steps = (ru_age[step] * time_step).astype(int)
            prev_due_mask = (prev_steps > 0) & (age_steps == prev_steps)

        if maintenance.modernization_enabled:
            mod_steps = (mod_schedule_mc * time_step).astype(int)
            mod_due_mask = (mod_steps > 0) & (step % np.maximum(mod_steps, 1) == 0)

        # Modernization is prioritary when both calendars trigger on the same RU.
        prev_only_mask = prev_due_mask & ~mod_due_mask
        maint_due_mask = prev_due_mask | mod_due_mask
        maint_due = np.where(maint_due_mask)

        if maint_due[0].size > 0:
            # Binary per-subtype masks broadcast against per-RU ei / downtime vectors.
            prev_mask_f = prev_only_mask.astype(float)
            mod_mask_f = mod_due_mask.astype(float)

            # Reset the age of every RU that was serviced this step (any subtype).
            replacement_or[maint_due[0], maint_due[1]] = 1.0
            ru_age[step] = np.round(1.0 - replacement_or[:, :nb_ru]) * ru_age[step]

            # Per-RU EI contributions: broadcast (1, nb_ei, nb_ru) × (nb_ite_mc, 1, nb_ru).
            prev_step_per_ru = (
                ei_planned_maintenance[np.newaxis, :, :] * prev_mask_f[:, np.newaxis, :]
            )
            mod_step_per_ru = (
                ei_planned_maintenance[np.newaxis, :, :] * mod_mask_f[:, np.newaxis, :]
            )

            # Per-RU downtime contributions.
            downtime_prev_step_per_ru = sim.downtime.preventive_hours[np.newaxis, :] * prev_mask_f
            downtime_mod_step_per_ru = sim.downtime.modernization_hours[np.newaxis, :] * mod_mask_f

            # Per-RU cost contributions.
            prev_cost_step_per_ru = prev_mask_f * planned_maint_cost_per_ru
            mod_cost_step_per_ru = mod_mask_f * planned_maint_cost_per_ru

            replacement_or[:] = 0.0

            # New random draws for maintained components.
            random_fault_time[maint_due] = np.random.uniform(0.0, 1.0, size=maint_due[0].size)
            random_fault_type[maint_due] = np.random.uniform(0.0, 1.0, size=maint_due[0].size)
            random_replacement_ratio = np.random.uniform(0.0, 1.0, size=(nb_ite_mc, row_r, col_r))

        # ── Curative maintenance (fault detection) ────────────────────────────
        # CDF lookup uses the age at the END of the previous step (before the
        # current increment) to stay consistent with the legacy algorithm.
        wcdf_prev = wcdf_curr
        wcdf_curr = _lookup_wcdf(ru_age[step - 1], weibull_e, weibull_r, weibull_w, time_step)

        fault_mask = (wcdf_prev <= random_fault_time) & (random_fault_time <= wcdf_curr)
        fault_rows, fault_cols = np.where(fault_mask)

        if fault_rows.size > 0:
            # Age index of each faulted component (for fault-type lookup).
            fault_age_steps = np.clip(
                np.round(ru_age[step, fault_rows, fault_cols] * time_step).astype(int),
                0,
                wcdf_per_ru.shape[0] - 1,
            )
            p_e = prob_e[fault_age_steps, fault_cols]
            p_r = prob_r[fault_age_steps, fault_cols]

            draws = random_fault_type[fault_rows, fault_cols]

            # Classify each fault by comparing the draw to the conditional mode
            # probabilities.  prob_e/r/w are already zero for globally or
            # per-RU disabled modes (guaranteed by _build_weibull_cdfs), so
            # the threshold comparisons produce the correct classification
            # without any additional mode-flag checks.
            # prob_e + prob_r + prob_w == 1 by construction, so the three
            # masks are mutually exclusive and collectively exhaustive.
            early_mask = draws <= p_e
            mc_e, ru_e = fault_rows[early_mask], fault_cols[early_mask]
            fault_cause[step, mc_e, ru_e] = "Early"
            replacement[mc_e, ru_e, :] = rm_values[ru_e]

            rand_mask = (draws > p_e) & (draws <= p_e + p_r)
            mc_r, ru_r = fault_rows[rand_mask], fault_cols[rand_mask]
            fault_cause[step, mc_r, ru_r] = "Random"
            replacement[mc_r, ru_r, :] = rm_values[ru_r]

            # Remaining faults → wearout.  When wearout is disabled, p_e+p_r
            # equals 1.0 exactly, so this mask is empty.
            wear_mask = ~early_mask & ~rand_mask
            mc_w, ru_w = fault_rows[wear_mask], fault_cols[wear_mask]
            fault_cause[step, mc_w, ru_w] = "Wearout"
            replacement[mc_w, ru_w, :] = rm_values[ru_w]

            # Apply stochastic replacement ratio.
            replacement[replacement >= random_replacement_ratio] = 1.0
            replacement[replacement < random_replacement_ratio] = 0.0

            # New random draws for replaced components.
            random_fault_time[fault_rows, fault_cols] = np.random.uniform(
                0.0, 1.0, size=fault_rows.size
            )
            random_fault_type[fault_rows, fault_cols] = np.random.uniform(
                0.0, 1.0, size=fault_rows.size
            )
            random_replacement_ratio = np.random.uniform(0.0, 1.0, size=(nb_ite_mc, row_r, col_r))

        # Binary replacement indicator: 1 if at least one source triggered replacement.
        replacement_or = np.clip(replacement.sum(axis=1), 0.0, 1.0)

        # ── Environmental impact accumulation ─────────────────────────────────
        # Per-RU curative EI: broadcast (1, nb_ei, nb_ru) × (nb_ite_mc, 1, nb_ru).
        curative_step_per_ru = (
            ei_curative_maintenance[np.newaxis, :, :] * replacement_or[:, np.newaxis, :]
        )  # (nb_ite_mc, nb_ei, nb_ru)

        downtime_curative_step_per_ru = (
            sim.downtime.curative_hours[np.newaxis, :] * replacement_or
        )  # (nb_ite_mc, nb_ru)

        # Accumulate per-activity and per-RU arrays.
        ei_use_per_act[step] = ei_use_per_act[step - 1] + mean_use_ei_per_act_step
        ei_preventive_maint[step] = ei_preventive_maint[step - 1] + prev_step_per_ru
        ei_modernization[step] = ei_modernization[step - 1] + mod_step_per_ru
        ei_curative_maint[step] = ei_curative_maint[step - 1] + curative_step_per_ru

        # Grand total: manu + use + planned (preventive + modernization) + curative.
        use_sum = ei_use_per_act[step].sum(axis=-1)  # (nb_ei,)
        planned_sum = (ei_preventive_maint[step] + ei_modernization[step]).sum(
            axis=-1
        )  # (nb_ite_mc, nb_ei)
        curative_sum = ei_curative_maint[step].sum(axis=-1)  # (nb_ite_mc, nb_ei)
        ei_total[step] = (
            ei_manu_total[np.newaxis, :] + use_sum[np.newaxis, :] + planned_sum + curative_sum
        )

        # Downtime accumulation: preventive, modernization and curative tracked separately.
        downtime_preventive_per_ru[step] = (
            downtime_preventive_per_ru[step - 1] + downtime_prev_step_per_ru
        )  # (nb_ite_mc, nb_ru)
        downtime_modernization_per_ru[step] = (
            downtime_modernization_per_ru[step - 1] + downtime_mod_step_per_ru
        )  # (nb_ite_mc, nb_ru)
        downtime_curative_per_ru[step] = (
            downtime_curative_per_ru[step - 1] + downtime_curative_step_per_ru
        )  # (nb_ite_mc, nb_ru)

        # ── Cost accumulation ─────────────────────────────────────────────────
        # Per-RU curative cost: (nb_ite_mc, nb_ru).
        curative_cost_step_per_ru = replacement_or * curative_maint_cost_per_ru

        cost_use_per_act[step] = cost_use_per_act[step - 1] + mean_use_cost_per_act_step

        cost_preventive_maint_per_ru[step] = (
            cost_preventive_maint_per_ru[step - 1] + prev_cost_step_per_ru
        )
        cost_modernization_per_ru[step] = cost_modernization_per_ru[step - 1] + mod_cost_step_per_ru
        cost_curative_maint_per_ru[step] = (
            cost_curative_maint_per_ru[step - 1] + curative_cost_step_per_ru
        )
        # Grand total: manu + use (MC-averaged, scalar) + planned + curative per MC.
        cost_total[step] = (
            cost_manu_initial
            + cost_use_per_act[step].sum()
            + cost_preventive_maint_per_ru[step].sum(axis=-1)
            + cost_modernization_per_ru[step].sum(axis=-1)
            + cost_curative_maint_per_ru[step].sum(axis=-1)
        )

        # ── Age and fault count update ─────────────────────────────────────────
        ru_age[step] = np.round(1.0 - replacement_or[:, :nb_ru]) * ru_age[step]
        number_of_faults[step] = number_of_faults[step - 1] + replacement_or[:, :nb_ru]

        # Reset for next step.
        replacement[:] = 0.0
        replacement_or[:] = 0.0

    # ── End-of-life step (index usage_time) ───────────────────────────────────
    ei_total[usage_time] = ei_total[usage_time - 1] + ei_eol_total[np.newaxis, :]
    cost_total[usage_time] = cost_total[usage_time - 1] + eol_cost.sum()

    # Defensive: if a global flag is off, clear any residual label in fault_cause.
    # This guards against floating-point edge cases and makes the intent explicit.
    if not failure.early_enabled:
        fault_cause[fault_cause == "Early"] = ""
    if not failure.random_enabled:
        fault_cause[fault_cause == "Random"] = ""
    if not failure.wearout_enabled:
        fault_cause[fault_cause == "Wearout"] = ""

    # Log the effective fault counts per mode for traceability.
    n_early = int(np.sum(fault_cause == "Early"))
    n_random = int(np.sum(fault_cause == "Random"))
    n_wearout = int(np.sum(fault_cause == "Wearout"))
    logger.info("Fault counts — Early: %d, Random: %d, Wearout: %d", n_early, n_random, n_wearout)

    env = EnvironmentalResult(
        total=ei_total,
        manufacturing=ei_manu,
        use=ei_use_per_act,
        preventive_maintenance=ei_preventive_maint,
        modernization=ei_modernization,
        curative_maintenance=ei_curative_maint,
        end_of_life=ei_eol,
        number_of_faults=number_of_faults,
        fault_cause=fault_cause,
        wcdf_total=wcdf_total,
        wcdf_per_ru=wcdf_per_ru,
        ru_age=ru_age,
    )
    eco = EconomicResult(
        total=cost_total,
        manufacturing=raw_cost,
        use=cost_use_per_act,
        preventive_maintenance=cost_preventive_maint_per_ru,
        modernization=cost_modernization_per_ru,
        curative_maintenance=cost_curative_maint_per_ru,
        end_of_life=eol_cost,
    )
    return SimulationResult(
        environmental=env,
        economic=eco,
        downtime=DowntimeResult(
            preventive=downtime_preventive_per_ru,
            modernization=downtime_modernization_per_ru,
            curative=downtime_curative_per_ru,
        ),
    )
