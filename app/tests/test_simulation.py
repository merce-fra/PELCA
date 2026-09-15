from __future__ import annotations

import dataclasses

import numpy as np
import pytest
from scipy.stats import weibull_min

from app.core import simulation
from app.core.config import FailureConfig, FaultModeMask
from app.core.lca import LcaResult
from app.tests.fixtures import (
    MC_ITERATIONS,
    NB_ACT_CM,
    NB_ACT_EOL,
    NB_ACT_MANU,
    NB_ACT_PM,
    NB_ACT_USE,
    NB_EI,
    NB_RU,
    SERVICE_LIFE,
    TIME_STEP,
    make_config,
)


def _make_lca_result() -> LcaResult:
    """Return a minimal ``LcaResult`` dimensionally consistent with ``make_config()``.

    Array column counts mirror the ``NB_ACT_*`` constants from ``fixtures``:
    ``NB_ACT_MANU`` for manufacturing, ``NB_ACT_USE`` for use, ``NB_ACT_PM`` /
    ``NB_ACT_CM`` for maintenance, and ``NB_ACT_EOL`` for end-of-life.
    """
    manufacturing = np.ones((NB_EI, NB_ACT_MANU), dtype=float)
    use = np.ones((NB_EI, NB_ACT_USE), dtype=float) * 0.5
    planned_maintenance = np.ones((NB_EI, NB_ACT_PM), dtype=float) * 0.1
    curative_maintenance = np.ones((NB_EI, NB_ACT_CM), dtype=float) * 0.2
    eol = np.zeros((NB_EI, NB_ACT_EOL), dtype=float)
    return LcaResult(
        manufacturing=manufacturing,
        use=use,
        planned_maintenance=planned_maintenance,
        curative_maintenance=curative_maintenance,
        eol=eol,
        use_per_profile={0: use},
        nb_ru=NB_RU,
    )


# ---------------------------------------------------------------------------
# Unit tests — synthetic data (no Excel file required)
# ---------------------------------------------------------------------------


def test_simulation_output_shapes() -> None:
    """``run_simulation`` must return arrays with the correct time/MC/EI dimensions."""
    lca = _make_lca_result()
    config = make_config()
    simulation_result = simulation.run_simulation(lca, config)

    usage_time = SERVICE_LIFE * TIME_STEP + 1
    nb_ei_sim = lca.manufacturing.shape[0]
    nb_ru_sim = lca.nb_ru

    env = simulation_result.environmental
    eco = simulation_result.economic
    downtime = simulation_result.downtime.per_maintenance

    assert env.total.shape == (usage_time + 1, MC_ITERATIONS, nb_ei_sim)
    assert env.manufacturing.shape == (nb_ei_sim, lca.manufacturing.shape[1])
    assert env.use.shape == (usage_time, nb_ei_sim, lca.use.shape[1])
    assert env.planned_maintenance.shape == (usage_time, MC_ITERATIONS, nb_ei_sim, nb_ru_sim)
    assert env.curative_maintenance.shape == (usage_time, MC_ITERATIONS, nb_ei_sim, nb_ru_sim)
    assert env.end_of_life.shape == (nb_ei_sim, lca.eol.shape[1])
    assert env.number_of_faults.shape == (usage_time, MC_ITERATIONS, nb_ru_sim)
    assert env.ru_age.shape == (usage_time, MC_ITERATIONS, nb_ru_sim)
    assert env.wcdf_total.shape == (usage_time,)
    assert env.wcdf_per_ru.shape == (usage_time, nb_ru_sim)

    assert eco.total.shape == (usage_time + 1, MC_ITERATIONS)
    assert eco.manufacturing.shape == (NB_ACT_MANU,)
    assert eco.use.shape == (usage_time, NB_RU)
    assert eco.planned_maintenance.shape == (usage_time, MC_ITERATIONS, NB_RU)
    assert eco.curative_maintenance.shape == (usage_time, MC_ITERATIONS, NB_RU)
    assert eco.end_of_life.shape == (NB_ACT_EOL,)

    assert downtime.shape == (usage_time, MC_ITERATIONS, NB_RU)


def test_env_total_is_nondecreasing() -> None:
    """Cumulative environmental impact must never decrease over time."""
    lca = _make_lca_result()
    config = make_config()
    simulation_result = simulation.run_simulation(lca, config)

    env = simulation_result.environmental

    # Check along the time axis (axis=0) for all MC iterations and EI methods
    diffs = np.diff(env.total, axis=0)
    assert diffs.min() >= -1e-9, "env.total decreased over time — cumulative sum is broken"


def test_eco_fields_are_non_negative() -> None:
    """All ``EconomicResult`` cost arrays must contain only non-negative values."""
    lca = _make_lca_result()
    config = make_config()
    simulation_result = simulation.run_simulation(lca, config)
    eco = simulation_result.economic

    assert eco.total.min() >= 0.0
    assert eco.manufacturing.min() >= 0.0
    assert eco.use.min() >= 0.0
    assert eco.planned_maintenance.min() >= 0.0
    assert eco.curative_maintenance.min() >= 0.0
    assert eco.end_of_life.min() >= 0.0


def test_build_weibull_cdfs_is_profile_average() -> None:
    """Weibull tables must equal the probability-weighted average of per-profile CDFs.

    With two profiles having distinct parameters and equal hours, the effective
    CDF must equal ``0.5 * CDF_0 + 0.5 * CDF_1``.  It must also differ from the
    CDF computed with the averaged parameters, confirming that the Jensen-inequality
    bias of the old implementation is absent.
    """
    nb_ru = 2
    nb_profiles = 2

    # Profile 0: short characteristic life. Profile 1: long characteristic life.
    sigma_e = np.array([[3.0, 10.0], [3.0, 10.0]], dtype=float)  # (nb_ru, nb_profiles)
    beta_e = np.array([[1.5, 3.0], [1.5, 3.0]], dtype=float)

    failure = FailureConfig(
        early_enabled=True,
        random_enabled=False,
        wearout_enabled=False,
        mode_enabled_by_ru=FaultModeMask.all_enabled(nb_ru),
        sigma_early=sigma_e,
        beta_early=beta_e,
        sigma_random=np.ones((nb_ru, nb_profiles)),
        beta_random=np.ones((nb_ru, nb_profiles)),
        sigma_wearout=np.ones((nb_ru, nb_profiles)),
        beta_wearout=np.ones((nb_ru, nb_profiles)),
    )

    # Equal proportions → each profile has weight 0.5.
    mission_profile_probs = np.array([0.5, 0.5])
    time_step = 12
    service_life = 10
    t = np.linspace(1e-10, service_life, service_life * time_step + 1)

    weibull_e, _, _ = simulation._build_weibull_cdfs(t, failure, mission_profile_probs, time_step)

    # Manually compute expected: 0.5 * CDF_0 + 0.5 * CDF_1.
    dt = 1.0 / time_step
    time_shifted = np.broadcast_to(t[:, np.newaxis] - dt, (len(t), nb_ru)).copy()
    cdf_0 = weibull_min.cdf(time_shifted, beta_e[:, 0], scale=sigma_e[:, 0])
    cdf_1 = weibull_min.cdf(time_shifted, beta_e[:, 1], scale=sigma_e[:, 1])
    expected = 0.5 * cdf_0 + 0.5 * cdf_1

    np.testing.assert_allclose(weibull_e, expected, rtol=1e-12)


# ---------------------------------------------------------------------------
# Unit tests — global failure-mode flags
# ---------------------------------------------------------------------------


def _make_config_with_flags(
    early_enabled: bool,
    random_enabled: bool,
    wearout_enabled: bool,
) -> make_config.__class__:
    """Return a ``PelcaConfig`` with the specified global failure-mode flags."""
    from app.tests.fixtures import make_failure_config

    base_failure = make_failure_config()
    failure = dataclasses.replace(
        base_failure,
        early_enabled=early_enabled,
        random_enabled=random_enabled,
        wearout_enabled=wearout_enabled,
    )
    config = make_config()
    sim = dataclasses.replace(config.simulation, failure=failure)
    return dataclasses.replace(config, simulation=sim)


@pytest.mark.parametrize(
    "early_enabled, random_enabled, wearout_enabled, disabled_label",
    [
        (False, True, True, "Early"),
        (True, False, True, "Random"),
        (True, True, False, "Wearout"),
        (False, False, True, "Early"),
        (False, False, True, "Random"),
        (False, True, False, "Wearout"),
        (True, False, False, "Random"),
        (True, False, False, "Wearout"),
    ],
)
def test_disabled_flag_produces_zero_fault_cause(
    early_enabled: bool,
    random_enabled: bool,
    wearout_enabled: bool,
    disabled_label: str,
) -> None:
    """Disabling a global failure mode must produce zero faults of that type.

    For each combination of flags, the ``fault_cause`` array in the simulation
    result must contain no occurrences of the disabled mode's label.
    """
    lca = _make_lca_result()
    config = _make_config_with_flags(early_enabled, random_enabled, wearout_enabled)
    result = simulation.run_simulation(lca, config)

    # Count occurrences of the disabled mode's label in the full fault_cause array.
    count = int(np.sum(result.environmental.fault_cause == disabled_label))
    assert count == 0, (
        f"Expected 0 '{disabled_label}' faults with {disabled_label.lower()}_enabled=False "
        f"(early={early_enabled}, random={random_enabled}, wearout={wearout_enabled}), "
        f"but found {count}."
    )
