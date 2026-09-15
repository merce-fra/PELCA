"""Unit tests for app/io/plots.py."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import pytest

from app.core.lca import LcaResult
from app.core.simulation import (
    DowntimeResult,
    EconomicResult,
    EnvironmentalResult,
    SimulationResult,
)
from app.io.plots import PlotBuilder
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

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_USAGE_TIME = SERVICE_LIFE * TIME_STEP + 1


@pytest.fixture()
def lca_result() -> LcaResult:
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


@pytest.fixture()
def env_result() -> EnvironmentalResult:
    shape_3d_ru = (_USAGE_TIME, MC_ITERATIONS, NB_RU)
    t = np.arange(_USAGE_TIME, dtype=float)
    total = np.outer(t, np.ones(MC_ITERATIONS * NB_EI)).reshape((_USAGE_TIME, MC_ITERATIONS, NB_EI))
    manu_base = np.arange(NB_EI * NB_ACT_MANU, dtype=float).reshape(NB_EI, NB_ACT_MANU) + 1.0
    use_base = np.arange(NB_EI * NB_ACT_USE, dtype=float).reshape(NB_EI, NB_ACT_USE) + 10.0
    use_time = np.outer(t, np.ones(NB_EI * NB_ACT_USE)).reshape((_USAGE_TIME, NB_EI, NB_ACT_USE))
    use_varied = use_time * use_base[np.newaxis, :, :]
    eol_base = np.arange(NB_EI * NB_ACT_EOL, dtype=float).reshape(NB_EI, NB_ACT_EOL) * 0.1 + 100.0
    return EnvironmentalResult(
        total=total,
        manufacturing=manu_base,
        use=use_varied,
        preventive_maintenance=np.zeros((_USAGE_TIME, MC_ITERATIONS, NB_EI, NB_RU)),
        modernization=np.zeros((_USAGE_TIME, MC_ITERATIONS, NB_EI, NB_RU)),
        curative_maintenance=np.zeros((_USAGE_TIME, MC_ITERATIONS, NB_EI, NB_RU)),
        end_of_life=eol_base,
        number_of_faults=np.zeros(shape_3d_ru),
        fault_cause=np.zeros(shape_3d_ru, dtype=object),
        wcdf_total=np.linspace(0.0, 1.0, _USAGE_TIME),
        wcdf_per_ru=np.zeros((_USAGE_TIME, NB_RU)),
        ru_age=np.zeros(shape_3d_ru),
    )


@pytest.fixture()
def eco_result() -> EconomicResult:
    shape_2d = (_USAGE_TIME, MC_ITERATIONS)
    shape_3d = (_USAGE_TIME, MC_ITERATIONS, NB_RU)
    t = np.arange(_USAGE_TIME, dtype=float)
    total = np.outer(t, np.ones(MC_ITERATIONS)).reshape(shape_2d)
    maint_3d = np.zeros(shape_3d)
    return EconomicResult(
        total=total,
        manufacturing=np.arange(NB_ACT_MANU, dtype=float) + 200.0,
        use=np.arange(_USAGE_TIME * NB_ACT_USE, dtype=float).reshape(_USAGE_TIME, NB_ACT_USE) * 0.01
        + 0.1,
        preventive_maintenance=maint_3d,
        modernization=maint_3d,
        curative_maintenance=maint_3d,
        end_of_life=np.arange(NB_ACT_EOL, dtype=float) + 10.0,
    )


@pytest.fixture()
def downtime_result() -> DowntimeResult:
    """Return a minimal downtime result with zero planned and curative hours."""
    shape_3d = (_USAGE_TIME, MC_ITERATIONS, NB_RU)
    return DowntimeResult(
        preventive=np.zeros(shape_3d),
        modernization=np.zeros(shape_3d),
        curative=np.zeros(shape_3d),
    )


@pytest.fixture()
def plot_builder(lca_result, env_result, eco_result, downtime_result) -> PlotBuilder:
    config = make_config()
    # raw_cost and eol_cost are phase-specific arrays in production (not concatenated).
    config.simulation.cost.manufacturing = np.ones(NB_ACT_MANU) * 100.0
    config.simulation.cost.end_of_life = np.ones(NB_ACT_EOL) * 5.0
    # Enable both planned-maintenance subtypes so the full set of plots is produced.
    config.simulation.maintenance.prev_enabled = True
    config.simulation.maintenance.modernization_enabled = True
    return PlotBuilder(
        config,
        lca_result,
        SimulationResult(environmental=env_result, economic=eco_result, downtime=downtime_result),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

_EXPECTED_TITLES = [
    "Manufacturing Impacts",
    "Use Impacts",
    "Preventive Maintenance Impacts",
    "Modernization Impacts",
    "Curative Maintenance Impacts",
    "End-of-Life Impacts",
    "Cumulative Distribution Function",
    "Distribution of Defects",
    "Selected EI",
    "Environmental Impact Over Time",
    "Total impacts at service life (mean)",
    "Economic Impact",
    "Downtime Impact",
]


def test_run_returns_correct_count(plot_builder: PlotBuilder) -> None:
    figs = plot_builder.run(show=False)
    assert len(figs) == len(_EXPECTED_TITLES)


def test_run_returns_expected_titles(plot_builder: PlotBuilder) -> None:
    figs = plot_builder.run(show=False)
    titles = [f["title"] for f in figs]
    assert len(titles) == len(_EXPECTED_TITLES)
    assert titles[0:8] == _EXPECTED_TITLES[0:8]
    assert titles[8].startswith("Selected EI")
    assert titles[9:] == _EXPECTED_TITLES[9:]


def test_run_each_entry_has_required_keys(plot_builder: PlotBuilder) -> None:
    figs = plot_builder.run(show=False)
    for entry in figs:
        assert "title" in entry
        assert "plot" in entry


def test_all_figures_are_plotly_figures(plot_builder: PlotBuilder) -> None:
    figs = plot_builder.run(show=False)
    for entry in figs:
        assert isinstance(entry["plot"], go.Figure)


def test_all_figures_have_at_least_one_trace(plot_builder: PlotBuilder) -> None:
    figs = plot_builder.run(show=False)
    for entry in figs:
        assert len(entry["plot"].data) > 0, f"Figure '{entry['title']}' has no traces"


def test_cdf_values_are_in_unit_interval(plot_builder: PlotBuilder) -> None:
    """CDF traces must stay within [0, 1]."""
    figs = plot_builder.run(show=False)
    cdf_entry = next(f for f in figs if f["title"] == "Cumulative Distribution Function")
    for trace in cdf_entry["plot"].data:
        if trace.y is not None and len(trace.y) > 0:
            y = np.asarray(trace.y, dtype=float)
            assert y.min() >= -1e-9, "CDF trace goes below 0"
            assert y.max() <= 1.0 + 1e-9, "CDF trace exceeds 1"


# ---------------------------------------------------------------------------
# Planned-maintenance subtype flags
# ---------------------------------------------------------------------------


def _make_plot_builder(
    lca_result: LcaResult,
    env_result: EnvironmentalResult,
    eco_result: EconomicResult,
    downtime_result: DowntimeResult,
    prev_enabled: bool = False,
    modernization_enabled: bool = False,
) -> PlotBuilder:
    """Build a ``PlotBuilder`` with cost arrays sized to match the test fixtures."""
    config = make_config()
    config.simulation.cost.manufacturing = np.ones(NB_ACT_MANU) * 100.0
    config.simulation.cost.end_of_life = np.ones(NB_ACT_EOL) * 5.0
    config.simulation.maintenance.prev_enabled = prev_enabled
    config.simulation.maintenance.modernization_enabled = modernization_enabled
    return PlotBuilder(
        config,
        lca_result,
        SimulationResult(environmental=env_result, economic=eco_result, downtime=downtime_result),
    )


def test_run_excludes_preventive_plot_when_disabled(
    lca_result: LcaResult,
    env_result: EnvironmentalResult,
    eco_result: EconomicResult,
    downtime_result: DowntimeResult,
) -> None:
    """When prev_enabled is False, 'Preventive Maintenance Impacts' must be absent."""
    builder = _make_plot_builder(
        lca_result, env_result, eco_result, downtime_result, prev_enabled=False
    )
    titles = [f["title"] for f in builder.run(show=False)]
    assert "Preventive Maintenance Impacts" not in titles


def test_run_includes_preventive_plot_when_enabled(
    lca_result: LcaResult,
    env_result: EnvironmentalResult,
    eco_result: EconomicResult,
    downtime_result: DowntimeResult,
) -> None:
    """When prev_enabled is True, 'Preventive Maintenance Impacts' must be present."""
    builder = _make_plot_builder(
        lca_result, env_result, eco_result, downtime_result, prev_enabled=True
    )
    titles = [f["title"] for f in builder.run(show=False)]
    assert "Preventive Maintenance Impacts" in titles


def test_run_excludes_modernization_plot_when_disabled(
    lca_result: LcaResult,
    env_result: EnvironmentalResult,
    eco_result: EconomicResult,
    downtime_result: DowntimeResult,
) -> None:
    """When modernization_enabled is False, 'Modernization Impacts' must be absent."""
    builder = _make_plot_builder(
        lca_result, env_result, eco_result, downtime_result, modernization_enabled=False
    )
    titles = [f["title"] for f in builder.run(show=False)]
    assert "Modernization Impacts" not in titles


def test_run_includes_modernization_plot_when_enabled(
    lca_result: LcaResult,
    env_result: EnvironmentalResult,
    eco_result: EconomicResult,
    downtime_result: DowntimeResult,
) -> None:
    """When modernization_enabled is True, 'Modernization Impacts' must be present."""
    builder = _make_plot_builder(
        lca_result, env_result, eco_result, downtime_result, modernization_enabled=True
    )
    titles = [f["title"] for f in builder.run(show=False)]
    assert "Modernization Impacts" in titles


def test_run_planned_subtype_plots_preserve_order_when_enabled(
    lca_result: LcaResult,
    env_result: EnvironmentalResult,
    eco_result: EconomicResult,
    downtime_result: DowntimeResult,
) -> None:
    """Preventive then Modernization plots must appear between 'Use Impacts' and
    'Curative Maintenance Impacts'."""
    builder = _make_plot_builder(
        lca_result,
        env_result,
        eco_result,
        downtime_result,
        prev_enabled=True,
        modernization_enabled=True,
    )
    titles = [f["title"] for f in builder.run(show=False)]
    idx_use = titles.index("Use Impacts")
    idx_prev = titles.index("Preventive Maintenance Impacts")
    idx_mod = titles.index("Modernization Impacts")
    idx_cm = titles.index("Curative Maintenance Impacts")
    assert idx_use < idx_prev < idx_mod < idx_cm
