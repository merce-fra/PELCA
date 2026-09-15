"""PELCA domain configuration types.

Defines all dataclasses that describe a single PELCA run: ``PelcaConfig`` is
the top-level object, composed of ``LcaConfig``, ``LciaConfig``,
``SimulationConfig`` (nesting ``FailureConfig``, ``MaintenanceConfig``,
``CostConfig``), and ``OutputConfig``. All types are treated as immutable
after construction by ``ExcelInputReader``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class LcaConfig:
    """brightway2 project and database settings.

    Attributes:
        project_name: Name of the brightway2 project to create or reuse.
        database: Name of the ecoinvent background database.
        ecoinvent_path: File-system path to the ecoinvent dataset folder.
        inventory_name: Name given to the foreground inventory database.
        activity_names: Activity name lists, split by life-cycle phase.
    """

    project_name: str
    database: str
    ecoinvent_path: str
    inventory_name: str
    activity_names: ActivityNames


@dataclass
class ActivityNames:
    """Names of activities corresponding to the LCA result analysis.

    Attributes:
        manufacturing: List of activity names for the manufacturing phase.
        use: List of activity names for the use phase.
        planned_maintenance: List of activity names for the planned maintenance phase.
        curative_maintenance: List of activity names for the curative maintenance phase.
        eol: List of activity names for the end-of-life phase.
    """

    manufacturing: list[str]
    use: list[str]
    planned_maintenance: list[str]
    curative_maintenance: list[str]
    eol: list[str]

    @property
    def all(self) -> list[str]:
        """Concatenated list of all activity names."""
        return (
            self.manufacturing
            + self.use
            + self.planned_maintenance
            + self.curative_maintenance
            + self.eol
        )

    @property
    def _unique(self) -> bool:
        """True if all activity names are unique across all phases."""
        return len(set(self.all)) == len(self.all)


@dataclass
class LciaConfig:
    """LCIA method definitions from the LCIA sheet.

    Attributes:
        names: Short display names for each LCIA method (e.g. ``"GWP 100a"``).
        units: Physical units for each method (e.g. ``"kg CO2 eq"``).
        method_tuples: Full brightway2 method tuples ``(family, category, context)``.
    """

    names: list[str]
    units: list[str]
    method_tuples: list[tuple[str, str, str]]


@dataclass
class SimulationConfig:
    """Staircase simulation parameters.

    Attributes:
        service_life: Total service life in years.
        time_step: Number of simulation steps per year.
        mc_iterations: Number of Monte Carlo iterations.
        hours_per_year: Operating hours per year.
        nb_mission_profiles: Number of distinct mission profiles.
        mission_profile_probs: Fraction of operating time for each profile.
            Values sum to ``1.0``. Shape ``(nb_profiles,)``.
        selected_ei_name: Name of the LCIA indicator selected for the single-EI plot.
            Must match one of the entries in ``LciaConfig.names``.
        energy_amounts: Energy consumption per activity per profile.
            Keys are activity names; values are lists of length ``nb_profiles``.
        failure: Weibull failure parameters.
        maintenance: Preventive maintenance schedule and replacement matrix.
        cost: Cost components per replaceable unit.
        downtime: Downtime parameters for each mission profile.
    """

    service_life: int
    time_step: int
    mc_iterations: int
    hours_per_year: float
    nb_mission_profiles: int
    mission_profile_probs: np.ndarray
    selected_ei_name: str
    energy_amounts: dict[str, list[float]]
    failure: FailureConfig
    maintenance: MaintenanceConfig
    cost: CostConfig
    downtime: DowntimeConfig

    @property
    def usage_time(self) -> int:
        """Total operating hours over the service life."""
        return int(self.service_life * self.time_step + 1)


@dataclass
class CostConfig:
    """Cost components per replaceable unit (RU).

    All arrays have shape ``(nb_ru,)``.
    """

    manufacturing: np.ndarray
    planned: np.ndarray
    curative: np.ndarray
    kwh_cost: np.ndarray
    end_of_life: np.ndarray
    names: ActivityNames


@dataclass
class DowntimeConfig:
    """Downtime parameters for each mission profile.

    Attributes:
        preventive_hours: Preventive downtime hours per year for each profile.
            Shape ``(nb_profiles,)``.
        modernization_hours: Modernization downtime hours per year for each profile.
            Shape ``(nb_profiles,)``.
        curative_hours: Curative downtime hours per year for each profile.
            Shape ``(nb_profiles,)``.
    """

    # Planned
    preventive_hours: np.ndarray
    modernization_hours: np.ndarray
    # Curative
    curative_hours: np.ndarray


@dataclass
class FailureConfig:
    """Weibull failure parameters for early, random, and wearout failure modes.

    All six parameter arrays have shape ``(nb_ru, nb_profiles)``.
    The simulation engine builds one CDF per profile and combines them as a
    probability-weighted average to form the effective failure CDF.
    """

    early_enabled: bool
    random_enabled: bool
    wearout_enabled: bool
    mode_enabled_by_ru: FaultModeMask
    sigma_early: np.ndarray
    beta_early: np.ndarray
    sigma_random: np.ndarray
    beta_random: np.ndarray
    sigma_wearout: np.ndarray
    beta_wearout: np.ndarray


@dataclass
class FaultModeMask:
    """Per-RU activation masks for each failure mode.

    Each array has shape ``(nb_ru,)`` and uses ``True`` to keep the corresponding
    fault mode enabled for that replaceable unit.
    """

    early: np.ndarray
    random: np.ndarray
    wearout: np.ndarray

    @classmethod
    def all_enabled(cls, nb_ru: int) -> FaultModeMask:
        """Return a mask that enables every failure mode for every RU."""
        enabled = np.ones(nb_ru, dtype=bool)
        return cls(early=enabled.copy(), random=enabled.copy(), wearout=enabled.copy())


@dataclass
class MaintenanceConfig:
    """Preventive maintenance schedule and curative replacement matrix."""

    prev_enabled: bool
    modernization_enabled: bool
    replacement_matrix: pd.DataFrame
    preventive_schedule: np.ndarray
    modernization_schedule: np.ndarray
    names: list[str] = None


@dataclass
class OutputConfig:
    """Output paths derived from the input Excel 'LCA result path' cell."""

    result_path: Path
    directory: str = "Results PELCA"
    lca_output_filename: str = "LCA output.xlsx"
    lcic_output_filename: str = "LCIC output.xlsx"

    @property
    def lca_dir(self) -> Path:
        """Root results directory: ``result_path / directory``."""
        return self.result_path / self.directory

    @property
    def plot_dir(self) -> Path:
        """Directory that receives plot sub-folders (``html/``, ``png/``, ``svg/``)."""
        return self.lca_dir / "plots"

    @property
    def numpy_dir(self) -> Path:
        """Directory that receives exported ``.npy`` files."""
        return self.lca_dir / "numpy"

    @property
    def lca_file(self) -> Path:
        """Full path to the LCA output Excel file."""
        return self.lca_dir / self.lca_output_filename


@dataclass
class PelcaConfig:
    """Complete configuration for one PELCA run, parsed from a single input Excel file."""

    lca: LcaConfig
    lcia: LciaConfig
    simulation: SimulationConfig
    output: OutputConfig
