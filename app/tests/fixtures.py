"""Shared test fixtures that build configuration objects without touching the filesystem."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from app.core.config import (
    ActivityNames,
    CostConfig,
    DowntimeConfig,
    FailureConfig,
    FaultModeMask,
    LcaConfig,
    LciaConfig,
    MaintenanceConfig,
    OutputConfig,
    PelcaConfig,
    SimulationConfig,
)
from app.core.lca import LcaResult
from app.core.simulation import (
    DowntimeResult,
    EconomicResult,
    EnvironmentalResult,
    SimulationResult,
)

# ---------------------------------------------------------------------------
# Default dimensions used across all fixtures
# ---------------------------------------------------------------------------

NB_RU = 2
NB_PROFILES = 1
NB_EI = 3
NB_ACT_MANU = 5
NB_ACT_USE = 2
NB_ACT_PM = NB_RU
NB_ACT_CM = NB_RU
NB_ACT_EOL = 3
SERVICE_LIFE = 5
TIME_STEP = 1
MC_ITERATIONS = 10
HOURS_PER_YEAR = 2000.0
_USAGE_TIME = SERVICE_LIFE * TIME_STEP + 1

INPUT_PATH = Path("tests/data/minimal.xlsx")
RESULT_PATH = Path("tests/data/results")

LCIA_NAMES = ["GWP", "AP", "EP"]
LCIA_UNITS = ["kg CO2 eq", "kg SO2 eq", "kg PO4 eq"]
LCIA_METHOD_TUPLES = [
    ("EF v3.0", "climate change", "global warming potential (GWP100)"),
    ("EF v3.0", "acidification", "accumulated exceedance (AE)"),
    ("EF v3.0", "eutrophication", "fraction of nutrients reaching freshwater end compartment (P)"),
]


def make_failure_config(nb_ru: int = NB_RU, nb_profiles: int = NB_PROFILES) -> FailureConfig:
    """Return a ``FailureConfig`` with simple constant Weibull parameters."""
    ones = np.ones((nb_ru, nb_profiles), dtype=float)
    return FailureConfig(
        early_enabled=True,
        random_enabled=True,
        wearout_enabled=True,
        mode_enabled_by_ru=FaultModeMask.all_enabled(nb_ru),
        sigma_early=ones * 1.0,
        beta_early=ones * 0.5,
        sigma_random=ones * 5.0,
        beta_random=ones * 1.0,
        sigma_wearout=ones * 10.0,
        beta_wearout=ones * 3.5,
    )


def make_maintenance_config(
    nb_ru: int = NB_RU, nb_profiles: int = NB_PROFILES
) -> MaintenanceConfig:
    """Return a ``MaintenanceConfig`` with a trivial replacement matrix."""
    return MaintenanceConfig(
        prev_enabled=False,
        modernization_enabled=False,
        preventive_schedule=np.zeros((nb_ru, nb_profiles), dtype=float),
        modernization_schedule=np.zeros((nb_ru, nb_profiles), dtype=float),
        replacement_matrix=pd.DataFrame(
            np.eye(nb_ru, dtype=float),
            index=[f"RU{i + 1}" for i in range(nb_ru)],
            columns=[f"RU{i + 1}" for i in range(nb_ru)],
        ),
    )


def make_cost_config() -> CostConfig:
    """Return a ``CostConfig`` with unit costs for all RUs."""
    return CostConfig(
        manufacturing=np.ones(NB_ACT_MANU, dtype=float) * 100.0,
        planned=np.ones(NB_ACT_PM, dtype=float) * 10.0,
        curative=np.ones(NB_ACT_CM, dtype=float) * 10.0,
        kwh_cost=np.ones(NB_ACT_USE, dtype=float) * 0.15,
        end_of_life=np.ones(NB_ACT_EOL, dtype=float) * 5.0,
        names=ActivityNames(
            manufacturing=[f"activity_manu_{i + 1}" for i in range(NB_ACT_MANU)],
            use=[f"activity_use_{i + 1}" for i in range(NB_ACT_USE)],
            planned_maintenance=[f"activity_pm_{i + 1}" for i in range(NB_ACT_PM)],
            curative_maintenance=[f"activity_cm_{i + 1}" for i in range(NB_ACT_CM)],
            eol=[f"activity_eol_{i + 1}" for i in range(NB_ACT_EOL)],
        ),
    )


def make_downtime_config(nb_ru: int = NB_RU) -> DowntimeConfig:
    """Return a ``DowntimeConfig`` with zero planned and curative hours."""
    ones = np.ones(nb_ru, dtype=float)
    return DowntimeConfig(
        preventive_hours=ones * 10.0,
        modernization_hours=ones * 5.0,
        curative_hours=ones * 25.0,
    )


def make_simulation_config(
    nb_ru: int = NB_RU,
    nb_profiles: int = NB_PROFILES,
) -> SimulationConfig:
    """Return a minimal ``SimulationConfig``."""
    return SimulationConfig(
        service_life=SERVICE_LIFE,
        time_step=TIME_STEP,
        mc_iterations=MC_ITERATIONS,
        hours_per_year=HOURS_PER_YEAR,
        nb_mission_profiles=nb_profiles,
        mission_profile_probs=np.full(nb_profiles, 1.0 / nb_profiles),
        selected_ei_name="GWP",
        energy_amounts={
            f"activity_use_{i + 1}": [float(i + 1)] * nb_profiles for i in range(NB_ACT_USE)
        },
        failure=make_failure_config(nb_ru, nb_profiles),
        maintenance=make_maintenance_config(nb_ru, nb_profiles),
        cost=make_cost_config(),
        downtime=make_downtime_config(nb_ru),
    )


def make_config(
    nb_ru: int = NB_RU,
    nb_profiles: int = NB_PROFILES,
    result_path: Path = RESULT_PATH,
) -> PelcaConfig:
    """Return a fully populated ``PelcaConfig`` without reading any file.

    Suitable for unit tests of ``core/`` modules that depend on ``PelcaConfig``
    but must not touch the filesystem.
    """
    return PelcaConfig(
        lca=LcaConfig(
            project_name="test_project",
            database="ecoinvent-3.9-cutoff",
            ecoinvent_path="/data/ecoinvent",
            inventory_name="test_inventory",
            activity_names=ActivityNames(
                manufacturing=[f"activity_manu_{i + 1}" for i in range(NB_ACT_MANU)],
                use=[f"activity_use_{i + 1}" for i in range(NB_ACT_USE)],
                planned_maintenance=[f"activity_pm_{i + 1}" for i in range(NB_ACT_PM)],
                curative_maintenance=[f"activity_cm_{i + 1}" for i in range(NB_ACT_CM)],
                eol=[f"activity_eol_{i + 1}" for i in range(NB_ACT_EOL)],
            ),
        ),
        lcia=LciaConfig(
            names=LCIA_NAMES,
            units=LCIA_UNITS,
            method_tuples=LCIA_METHOD_TUPLES,
        ),
        simulation=make_simulation_config(nb_ru, nb_profiles),
        output=OutputConfig(result_path=result_path),
    )


def _make_lca_result() -> LcaResult:
    """Return a minimal ``LcaResult`` compatible with ``make_config()``."""
    return LcaResult(
        manufacturing=np.arange(NB_EI * NB_ACT_MANU, dtype=float).reshape(NB_EI, NB_ACT_MANU) + 1.0,
        use=np.arange(NB_EI * NB_ACT_USE, dtype=float).reshape(NB_EI, NB_ACT_USE) + 10.0,
        planned_maintenance=np.arange(NB_EI * NB_ACT_PM, dtype=float).reshape(NB_EI, NB_ACT_PM)
        * 0.1
        + 0.05,
        curative_maintenance=np.arange(NB_EI * NB_ACT_CM, dtype=float).reshape(NB_EI, NB_ACT_CM)
        * 0.2
        + 0.1,
        eol=np.arange(NB_EI * NB_ACT_EOL, dtype=float).reshape(NB_EI, NB_ACT_EOL) * 0.1 + 100.0,
        use_per_profile={
            0: np.arange(NB_EI * NB_ACT_USE, dtype=float).reshape(NB_EI, NB_ACT_USE) + 10.0
        },
        nb_ru=NB_RU,
    )


def _make_env_result() -> EnvironmentalResult:
    """Return a minimal ``EnvironmentalResult`` with monotonically increasing totals."""
    shape_3d = (_USAGE_TIME, MC_ITERATIONS, NB_EI)
    shape_3d_ru = (_USAGE_TIME, MC_ITERATIONS, NB_RU)
    shape_2d = (_USAGE_TIME, NB_RU)
    t = np.arange(_USAGE_TIME, dtype=float)
    total = np.outer(t, np.ones(MC_ITERATIONS * NB_EI)).reshape(shape_3d)
    # Vary data by position rather than constant values
    manu_base = np.arange(NB_EI * NB_ACT_MANU, dtype=float).reshape(NB_EI, NB_ACT_MANU) + 1.0
    use_base = np.arange(NB_EI * NB_ACT_USE, dtype=float).reshape(NB_EI, NB_ACT_USE) + 10.0
    use_time = np.outer(t, np.ones(NB_EI * NB_ACT_USE)).reshape((_USAGE_TIME, NB_EI, NB_ACT_USE))
    use_varied = use_time * use_base[np.newaxis, :, :]
    eol_base = np.arange(NB_EI * NB_ACT_EOL, dtype=float).reshape(NB_EI, NB_ACT_EOL) * 0.1 + 100.0
    return EnvironmentalResult(
        total=total,
        manufacturing=manu_base,
        use=use_varied,
        preventive_maintenance=np.zeros((_USAGE_TIME, MC_ITERATIONS, NB_EI, NB_ACT_PM)),
        modernization=np.zeros((_USAGE_TIME, MC_ITERATIONS, NB_EI, NB_ACT_PM)),
        curative_maintenance=np.zeros((_USAGE_TIME, MC_ITERATIONS, NB_EI, NB_ACT_CM)),
        end_of_life=eol_base,
        number_of_faults=np.zeros(shape_3d_ru),
        fault_cause=np.zeros(shape_3d_ru),
        wcdf_total=np.linspace(0, 1, _USAGE_TIME),
        wcdf_per_ru=np.zeros(shape_2d),
        ru_age=np.zeros(shape_3d_ru),
    )


def _make_eco_result() -> EconomicResult:
    """Return a minimal ``EconomicResult`` matching the new structure."""
    total = np.outer(np.arange(_USAGE_TIME + 1, dtype=float), np.ones(MC_ITERATIONS))
    return EconomicResult(
        total=total,
        manufacturing=np.arange(NB_ACT_MANU, dtype=float) + 200.0,
        use=np.arange(_USAGE_TIME * NB_ACT_USE, dtype=float).reshape(_USAGE_TIME, NB_ACT_USE) * 0.01
        + 0.1,
        preventive_maintenance=np.zeros((_USAGE_TIME, MC_ITERATIONS, NB_ACT_PM)),
        modernization=np.zeros((_USAGE_TIME, MC_ITERATIONS, NB_ACT_PM)),
        curative_maintenance=np.zeros((_USAGE_TIME, MC_ITERATIONS, NB_ACT_CM)),
        end_of_life=np.arange(NB_ACT_EOL, dtype=float) + 10.0,
    )


def _make_downtime_result() -> DowntimeResult:
    """Return a minimal downtime array matching the new structure."""
    return DowntimeResult(
        preventive=np.arange(_USAGE_TIME * MC_ITERATIONS * NB_ACT_PM, dtype=float).reshape(
            _USAGE_TIME, MC_ITERATIONS, NB_ACT_PM
        )
        * 0.001
        + 0.2,
        modernization=np.arange(_USAGE_TIME * MC_ITERATIONS * NB_ACT_PM, dtype=float).reshape(
            _USAGE_TIME, MC_ITERATIONS, NB_ACT_PM
        )
        * 0.0005
        + 0.15,
        curative=np.arange(_USAGE_TIME * MC_ITERATIONS * NB_ACT_CM, dtype=float).reshape(
            _USAGE_TIME, MC_ITERATIONS, NB_ACT_CM
        )
        * 0.0008
        + 0.15,
    )


def _make_simulation_result() -> SimulationResult:
    """Return a minimal ``SimulationResult`` with monotonically increasing totals."""
    return SimulationResult(
        environmental=_make_env_result(),
        economic=_make_eco_result(),
        downtime=_make_downtime_result(),
    )
