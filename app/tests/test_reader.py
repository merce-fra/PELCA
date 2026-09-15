"""Tests for app/io/reader.py — ExcelInputReader."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.core.config import PelcaConfig
from app.io.reader import ExcelInputReader, _parse_profile_values
from app.tests.fixtures import NB_RU

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = Path(__file__).parent
_SAMPLE = (
    Path(__file__).parents[2]
    / "PELCA datasets"
    / "PowerModuleAndCapacitor"
    / "PELCA_v2.0.0_PowerModuleAndCapacitor.xlsx"
)


# ---------------------------------------------------------------------------
# Happy path — real sample file
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _SAMPLE.exists(), reason="Sample Excel not available")
def test_read_valid_returns_pelca_config():
    config = ExcelInputReader.from_excel(_SAMPLE)
    assert isinstance(config, PelcaConfig)


@pytest.mark.skipif(not _SAMPLE.exists(), reason="Sample Excel not available")
def test_read_valid_lcia_names_non_empty():
    config = ExcelInputReader.from_excel(_SAMPLE)
    assert len(config.lcia.names) > 0


@pytest.mark.skipif(not _SAMPLE.exists(), reason="Sample Excel not available")
def test_read_valid_service_life_positive():
    config = ExcelInputReader.from_excel(_SAMPLE)
    assert config.simulation.service_life > 0


@pytest.mark.skipif(not _SAMPLE.exists(), reason="Sample Excel not available")
def test_read_valid_failure_config_shapes_match():
    config = ExcelInputReader.from_excel(_SAMPLE)
    sim = config.simulation
    nb_profiles = sim.nb_mission_profiles
    for arr in (
        sim.failure.sigma_early,
        sim.failure.beta_early,
        sim.failure.sigma_random,
        sim.failure.beta_random,
        sim.failure.sigma_wearout,
        sim.failure.beta_wearout,
    ):
        assert arr.shape[1] == nb_profiles


@pytest.mark.skipif(not _SAMPLE.exists(), reason="Sample Excel not available")
def test_read_valid_cost_shape_matches_faults():
    config = ExcelInputReader.from_excel(_SAMPLE)
    sim = config.simulation
    nb_ru = sim.failure.sigma_early.shape[0]
    for arr in (
        sim.cost.planned,
        sim.cost.curative,
    ):
        assert len(arr) == nb_ru


@pytest.mark.skipif(not _SAMPLE.exists(), reason="Sample Excel not available")
def test_read_valid_selected_ei_name_in_lcia_names():
    config = ExcelInputReader.from_excel(_SAMPLE)
    assert config.simulation.selected_ei_name in config.lcia.names


@pytest.mark.skipif(not _SAMPLE.exists(), reason="Sample Excel not available")
def test_read_valid_mission_profile_probs_sum():
    config = ExcelInputReader.from_excel(_SAMPLE)
    sim = config.simulation
    total = float(sim.mission_profile_probs.sum())
    assert abs(total - 1.0) < 1e-9, f"Profile probs sum {total} != 1.0"


@pytest.mark.skipif(not _SAMPLE.exists(), reason="Sample Excel not available")
def test_read_valid_energy_amounts_non_empty():
    config = ExcelInputReader.from_excel(_SAMPLE)
    assert len(config.simulation.energy_amounts) > 0


# ---------------------------------------------------------------------------
# Error cases — file-level
# ---------------------------------------------------------------------------


def test_read_missing_file_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        ExcelInputReader.from_excel(Path("nonexistent_file.xlsx"))


# ---------------------------------------------------------------------------
# Error cases — sheet-level (use a minimal in-memory Excel)
# ---------------------------------------------------------------------------


def _write_minimal_excel(tmp_path: Path, sheets: dict[str, pd.DataFrame]) -> Path:
    """Write a minimal Excel with exactly the given sheets and return the path."""
    dest = tmp_path / "test.xlsx"
    with pd.ExcelWriter(dest, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
    return dest


def _make_all_required_sheets() -> dict[str, pd.DataFrame]:
    """Return minimal valid DataFrames for every required sheet (NB_RU RUs, single profile)."""
    lca = pd.DataFrame(
        {
            0: [
                "LCA result path",
                "Project name (brightway)",
                "Database ecoinvent",
                "Ecoinvent path",
                "Inventory name",
            ],
            1: [".", "proj", "db", "/path", "inv"],
        }
    )
    lcia = pd.DataFrame(
        {
            "Acronym": ["GWP"],
            "Unit": ["kg CO2 eq"],
            "Method name": ["EF v3.0"],
            "Impact category": ["climate change"],
            "Specific context": ["GWP100"],
        }
    )
    lcic = pd.DataFrame(
        {
            0: [
                "Service life (year)",
                "Time step (step/year)",
                "Monte Carlo (number of iteration)",
                "Annual usage time (hours/year)",
                "Early failure",
                "Random failure",
                "Wearout failure",
                "Preventive Maintenance",
                "Modernization",
                "Plot specific env. impact",
            ],
            1: [5, 1, 10, 2000, True, True, True, False, False, "GWP"],
        }
    )
    # NB_RU RUs; all Weibull columns present (no NaN) -> all fault modes enabled.
    faults = pd.DataFrame(
        {
            0: [1.0] * NB_RU,
            1: [0.5] * NB_RU,
            2: [5.0] * NB_RU,
            3: [1.0] * NB_RU,
            4: [10.0] * NB_RU,
            5: [3.5] * NB_RU,
        }
    )
    cost = pd.DataFrame(
        {
            0: [f"RU{i + 1}" for i in range(NB_RU)],
            1: [100.0] * NB_RU,
            2: [0.15] * NB_RU,
            3: [10.0] * NB_RU,
            4: [10.0] * NB_RU,
            5: [5.0] * NB_RU,
        }
    )
    rm = pd.DataFrame(np.eye(NB_RU, dtype=float), columns=range(1, NB_RU + 1))
    # Row 0 is sub-header; actual RU data starts at iloc[1:].
    # Column layout: 0=name, 1=preventive, 2=modernization, 3=curative.
    downtime = pd.DataFrame(
        {
            0: [None] + [f"RU{i + 1}" for i in range(NB_RU)],
            1: [None] + [12.0] * NB_RU,
            2: [None] + [6.0] * NB_RU,
            3: [None] + [24.0] * NB_RU,
        }
    )
    # Row 0 holds column names; rows 1+ hold per-RU schedules.
    planned_maint = pd.DataFrame(
        {
            0: ["Prev. schedule"] + [0.0] * NB_RU,
            1: ["Moderni. schedule"] + [0.0] * NB_RU,
        }
    )
    empty_inv = pd.DataFrame({0: [], 1: []})
    # Planned / curative maintenance inventories need exactly NB_RU activities each.
    inv_pm = pd.DataFrame(
        {0: ["Activity"] * NB_RU, 1: [f"planned_maint_RU{i + 1}" for i in range(NB_RU)]}
    )
    inv_cm = pd.DataFrame(
        {0: ["Activity"] * NB_RU, 1: [f"curative_maint_RU{i + 1}" for i in range(NB_RU)]}
    )
    return {
        "LCA": lca,
        "LCIA": lcia,
        "LCIC": lcic,
        "Faults": faults,
        "Cost - Price": cost,
        "Cur. Maint. (replac. matrix)": rm,
        "Inventory - Use": empty_inv,
        "Inventory - Manufacturing": empty_inv,
        "Inventory - Planned Maint.": inv_pm,
        "Inventory - Cur. Maint.": inv_cm,
        "Inventory - End of Life": empty_inv,
        "Downtime": downtime,
        "Planned Maint.": planned_maint,
    }


@pytest.mark.skipif(not _SAMPLE.exists(), reason="Sample Excel not available")
def test_read_valid_roundtrip_lca_config_project_name():
    """Project name is correctly extracted from the LCA sheet."""
    config = ExcelInputReader.from_excel(_SAMPLE)
    assert isinstance(config.lca.project_name, str)
    assert len(config.lca.project_name) > 0


def test_exceed_max_annual_usage_time():
    """ValueError when annual usage time exceeds 8784 h/year."""
    input_example = _make_all_required_sheets()
    input_example["LCIC"].iloc[3, 1] = 88895
    with pytest.raises(ValueError):
        ExcelInputReader.from_sheets_data(input_example)


def test_wrong_downtime_length():
    """ValueError when downtime row count does not match the number of RUs."""
    input_example = _make_all_required_sheets()
    # Replace with a DataFrame whose data section has NB_RU + 1 rows.
    input_example["Downtime"] = pd.DataFrame(
        {
            0: [None] + [f"RU{i + 1}" for i in range(NB_RU + 1)],
            1: [None] + [12.0] * (NB_RU + 1),
            2: [None] + [6.0] * (NB_RU + 1),
            3: [None] + [24.0] * (NB_RU + 1),
        }
    )
    with pytest.raises(ValueError):
        ExcelInputReader.from_sheets_data(input_example)


def test_fault_mode_mask_disables_when_both_parameters_absent():
    """When both sigma and beta are absent for a mode, that mode is silently disabled."""
    sheets = _make_all_required_sheets()
    sheets["Faults"] = pd.DataFrame(
        {
            0: [1.0] * NB_RU,
            1: [0.5] * NB_RU,
            2: [np.nan] * NB_RU,
            3: [np.nan] * NB_RU,
            4: [np.nan] * NB_RU,
            5: [np.nan] * NB_RU,
        }
    )
    config = ExcelInputReader.from_sheets_data(sheets)
    mask = config.simulation.failure.mode_enabled_by_ru
    assert mask.early.tolist() == [True] * NB_RU
    assert mask.random.tolist() == [False] * NB_RU
    assert mask.wearout.tolist() == [False] * NB_RU


def test_fault_mode_mask_raises_when_only_sigma_present():
    """sigma present but beta absent for a mode raises ValueError."""
    sheets = _make_all_required_sheets()
    sheets["Faults"] = pd.DataFrame(
        {
            0: [1.0] * NB_RU,
            1: [0.5] * NB_RU,
            2: [5.0] * NB_RU,
            3: [np.nan] * NB_RU,
            4: [10.0] * NB_RU,
            5: [3.5] * NB_RU,
        }
    )
    with pytest.raises(ValueError, match="sigma is set but beta is missing"):
        ExcelInputReader.from_sheets_data(sheets)


def test_fault_mode_mask_raises_when_only_beta_present():
    """beta present but sigma absent for a mode raises ValueError."""
    sheets = _make_all_required_sheets()
    sheets["Faults"] = pd.DataFrame(
        {
            0: [1.0] * NB_RU,
            1: [0.5] * NB_RU,
            2: [np.nan] * NB_RU,
            3: [1.0] * NB_RU,
            4: [10.0] * NB_RU,
            5: [3.5] * NB_RU,
        }
    )
    with pytest.raises(ValueError, match="beta is set but sigma is missing"):
        ExcelInputReader.from_sheets_data(sheets)


# ---------------------------------------------------------------------------
# Unit tests — _parse_profile_values
# ---------------------------------------------------------------------------


def test_parse_profile_values_nan_returns_zeros():
    """An empty (NaN) cell returns 0.0 for every profile."""
    assert _parse_profile_values(float("nan"), 2) == [0.0, 0.0]


def test_parse_profile_values_scalar_repeated():
    assert _parse_profile_values("20", 2) == [20.0, 20.0]


def test_parse_profile_values_hash_separated_exact():
    assert _parse_profile_values("20#30", 2) == [20.0, 30.0]


def test_parse_profile_values_count_mismatch_raises():
    """2 '#'-separated values with nb_profiles=3 is neither 1 nor 3 → ValueError."""
    with pytest.raises(ValueError, match="Expected 1 or 3"):
        _parse_profile_values("10#20", 3)


def test_parse_profile_values_too_many_for_single_profile_raises():
    """Multiple values when only 1 profile is declared → ValueError."""
    with pytest.raises(ValueError, match="Expected 1 or 1"):
        _parse_profile_values("15#15", 1)


def test_parse_profile_values_exact_match_two_profiles():
    """Exactly nb_profiles values → parsed without error."""
    assert _parse_profile_values("10#20", 2) == [10.0, 20.0]


def test_parse_profile_values_comma_decimal():
    assert _parse_profile_values("1,5", 1) == [1.5]


def test_parse_profile_values_numeric_input():
    assert _parse_profile_values(42, 2) == [42.0, 42.0]


# ---------------------------------------------------------------------------
# Integration — multi-profile parsing via from_sheets_data
# ---------------------------------------------------------------------------


def _make_two_profile_sheets() -> dict[str, pd.DataFrame]:
    """Return minimal valid DataFrames for a 2-profile (80 % / 20 %) PELCA config."""
    lca = pd.DataFrame(
        {
            0: [
                "LCA result path",
                "Project name (brightway)",
                "Database ecoinvent",
                "Ecoinvent path",
                "Inventory name",
            ],
            1: [".", "proj", "db", "/path", "inv"],
        }
    )
    lcia = pd.DataFrame(
        {
            "Acronym": ["GWP"],
            "Unit": ["kg CO2 eq"],
            "Method name": ["EF v3.0"],
            "Impact category": ["climate change"],
            "Specific context": ["GWP100"],
        }
    )
    lcic = pd.DataFrame(
        {
            0: [
                "Service life (year)",
                "Time step (step/year)",
                "Monte Carlo (number of iteration)",
                "Annual usage time (hours/year)",
                "Mission profile (%)",
                "Early failure",
                "Random failure",
                "Wearout failure",
                "Preventive Maintenance",
                "Modernization",
                "Plot specific env. impact",
            ],
            1: [5, 1, 10, 2000.0, "80#20", True, True, True, False, False, "GWP"],
        }
    )
    # NB_RU RUs; sigma_early uses '#'-separated values, beta_early is a scalar.
    faults = pd.DataFrame(
        {
            0: ["10#12"] * NB_RU,
            1: [0.5] * NB_RU,
            2: [5.0] * NB_RU,
            3: [1.0] * NB_RU,
            4: [10.0] * NB_RU,
            5: [3.5] * NB_RU,
        }
    )
    cost = pd.DataFrame(
        {
            0: [f"RU{i + 1}" for i in range(NB_RU)],
            1: [100.0] * NB_RU,
            2: [0.15] * NB_RU,
            3: [10.0] * NB_RU,
            4: [10.0] * NB_RU,
            5: [5.0] * NB_RU,
        }
    )
    rm = pd.DataFrame(np.eye(NB_RU, dtype=float), columns=range(1, NB_RU + 1))
    # Row 0 is sub-header; actual RU data starts at iloc[1:].
    # Column layout: 0=name, 1=preventive, 2=modernization, 3=curative.
    downtime = pd.DataFrame(
        {
            0: [None] + [f"RU{i + 1}" for i in range(NB_RU)],
            1: [None] + [12.0] * NB_RU,
            2: [None] + [6.0] * NB_RU,
            3: [None] + [24.0] * NB_RU,
        }
    )
    # Row 0 holds column names; rows 1+ hold per-RU schedules.
    planned_maint = pd.DataFrame(
        {
            0: ["Prev. schedule"] + [0.0] * NB_RU,
            1: ["Moderni. schedule"] + [0.0] * NB_RU,
        }
    )
    empty_inv = pd.DataFrame({0: [], 1: []})
    # Planned / curative maintenance inventories need exactly NB_RU activities each.
    inv_pm = pd.DataFrame(
        {0: ["Activity"] * NB_RU, 1: [f"planned_maint_RU{i + 1}" for i in range(NB_RU)]}
    )
    inv_cm = pd.DataFrame(
        {0: ["Activity"] * NB_RU, 1: [f"curative_maint_RU{i + 1}" for i in range(NB_RU)]}
    )
    return {
        "LCA": lca,
        "LCIA": lcia,
        "LCIC": lcic,
        "Faults": faults,
        "Cost - Price": cost,
        "Cur. Maint. (replac. matrix)": rm,
        "Inventory - Use": empty_inv,
        "Inventory - Manufacturing": empty_inv,
        "Inventory - Planned Maint.": inv_pm,
        "Inventory - Cur. Maint.": inv_cm,
        "Inventory - End of Life": empty_inv,
        "Downtime": downtime,
        "Planned Maint.": planned_maint,
    }


def test_from_sheets_data_two_profiles_nb_mission_profiles():
    config = ExcelInputReader.from_sheets_data(_make_two_profile_sheets())
    assert config.simulation.nb_mission_profiles == 2


def test_from_sheets_data_two_profiles_probs_sum():
    config = ExcelInputReader.from_sheets_data(_make_two_profile_sheets())
    sim = config.simulation
    assert abs(sim.mission_profile_probs.sum() - 1.0) < 1e-9


def test_from_sheets_data_two_profiles_weibull_shape():
    config = ExcelInputReader.from_sheets_data(_make_two_profile_sheets())
    assert config.simulation.failure.sigma_early.shape == (NB_RU, 2)


def test_from_sheets_data_two_profiles_scalar_faults_expanded():
    """A scalar Weibull value in Faults is broadcast to all profiles."""
    config = ExcelInputReader.from_sheets_data(_make_two_profile_sheets())
    beta = config.simulation.failure.beta_early
    assert beta.shape == (NB_RU, 2)
    assert np.all(beta == 0.5)


# ---------------------------------------------------------------------------
# Mission profile consistency — error cases via from_sheets_data
# ---------------------------------------------------------------------------


def test_single_profile_multi_value_in_faults_raises():
    """A '#'-separated value in Faults when only 1 profile is declared → ValueError."""
    sheets = _make_all_required_sheets()
    # Replace sigma_early (col 0) with a multi-value string -> inconsistent with 1 profile.
    sheets["Faults"] = pd.DataFrame(
        {
            0: ["15#15"] * NB_RU,
            1: [0.5] * NB_RU,
            2: [5.0] * NB_RU,
            3: [1.0] * NB_RU,
            4: [10.0] * NB_RU,
            5: [3.5] * NB_RU,
        }
    )
    with pytest.raises(ValueError, match="Faults"):
        ExcelInputReader.from_sheets_data(sheets)


def test_single_profile_multi_value_in_planned_maint_raises():
    """A '#'-separated value in Planned Maint. when only 1 profile → ValueError."""
    sheets = _make_all_required_sheets()
    sheets["Planned Maint."] = pd.DataFrame(
        {0: ["Prev. schedule", "0#0"], 1: ["Moderni. schedule", 0.0]}
    )
    with pytest.raises(ValueError, match="Planned Maint"):
        ExcelInputReader.from_sheets_data(sheets)


def test_two_profiles_wrong_count_in_faults_raises():
    """3 '#'-separated values in Faults when 2 profiles declared → ValueError."""
    sheets = _make_two_profile_sheets()
    sheets["Faults"] = pd.DataFrame(
        {
            0: ["10#12#14"] * NB_RU,
            1: [0.5] * NB_RU,
            2: [5.0] * NB_RU,
            3: [1.0] * NB_RU,
            4: [10.0] * NB_RU,
            5: [3.5] * NB_RU,
        }
    )
    with pytest.raises(ValueError, match="Expected 1 or 2"):
        ExcelInputReader.from_sheets_data(sheets)


def test_two_profiles_wrong_count_in_planned_maint_raises():
    """3 '#'-separated values in Planned Maint. when 2 profiles declared → ValueError."""
    sheets = _make_two_profile_sheets()
    sheets["Planned Maint."] = pd.DataFrame(
        {0: ["Prev. schedule", "0#0#0"], 1: ["Moderni. schedule", 0.0]}
    )
    with pytest.raises(ValueError, match="Expected 1 or 2"):
        ExcelInputReader.from_sheets_data(sheets)


def test_mission_profile_not_summing_to_100_raises():
    """Mission profile percentages that don't sum to 100 ± 0.5 → ValueError."""
    sheets = _make_two_profile_sheets()
    # Replace "80#20" with "60#30" (sums to 90, not 100).
    sheets["LCIC"].iloc[sheets["LCIC"][0].tolist().index("Mission profile (%)"), 1] = "60#30"
    with pytest.raises(ValueError, match="sum to"):
        ExcelInputReader.from_sheets_data(sheets)


def test_duplicate_activity_names_across_inventory_sheets_raises():
    """Duplicate activity names across inventory sheets → ValueError."""
    sheets = _make_all_required_sheets()
    # Add a duplicate activity name to the Cur. Maint. inventory sheet.
    sheets["Inventory - Cur. Maint."] = pd.DataFrame(
        {0: ["Activity"] * NB_RU, 1: ["planned_maint_RU1"] * NB_RU}
    )
    with pytest.raises(ValueError, match="Duplicate activity names"):
        ExcelInputReader.from_sheets_data(sheets)


# ---------------------------------------------------------------------------
# Downtime validation — error cases
# ---------------------------------------------------------------------------


def _sheets_with_faults_only_ru0() -> dict[str, pd.DataFrame]:
    """Return sheets where only RU 0 has a failure mode; RU 1 has no failure mode."""
    sheets = _make_all_required_sheets()
    # RU 0: early mode only. RU 1: all NaN → no failure mode.
    sheets["Faults"] = pd.DataFrame(
        {
            0: [1.0, np.nan],
            1: [0.5, np.nan],
            2: [np.nan, np.nan],
            3: [np.nan, np.nan],
            4: [np.nan, np.nan],
            5: [np.nan, np.nan],
        }
    )
    return sheets


def test_downtime_curative_nan_for_ru_with_fault_raises():
    """Missing curative downtime for a RU that has a failure mode → ValueError."""
    sheets = _make_all_required_sheets()
    # Element 'toto' (row index 2) curative downtime set to NaN.
    sheets["Downtime"] = pd.DataFrame(
        {
            0: [None, "RU1", "toto"],  # custom name
            1: [None] + [12.0] * NB_RU,
            2: [None] + [6.0] * NB_RU,
            3: [None, 24.0, np.nan],  # toto is NaN
        }
    )
    with pytest.raises(ValueError, match="CUR. MAINT. downtime"):
        ExcelInputReader.from_sheets_data(sheets)


def test_downtime_curative_nan_error_message_contains_element_name():
    """The ValueError message includes the element name from column 0, not a generic index."""
    sheets = _make_all_required_sheets()
    sheets["Downtime"] = pd.DataFrame(
        {
            0: [None, "RU1", "toto"],
            1: [None] + [12.0] * NB_RU,
            2: [None] + [6.0] * NB_RU,
            3: [None, 24.0, np.nan],
        }
    )
    with pytest.raises(ValueError, match="toto"):
        ExcelInputReader.from_sheets_data(sheets)


def test_downtime_curative_zero_for_ru_with_fault_is_valid():
    """Curative downtime of 0.0 (not NaN) is accepted even if a failure mode is defined."""
    sheets = _make_all_required_sheets()
    sheets["Downtime"] = pd.DataFrame(
        {
            0: [None] + [f"RU{i + 1}" for i in range(NB_RU)],
            1: [None] + [12.0] * NB_RU,
            2: [None] + [6.0] * NB_RU,
            3: [None] + [0.0] * NB_RU,  # 0 is valid
        }
    )
    # Must not raise.
    ExcelInputReader.from_sheets_data(sheets)


def test_downtime_curative_nan_ignored_for_ru_without_fault():
    """NaN curative downtime is accepted for a RU that has no failure mode defined."""
    sheets = _sheets_with_faults_only_ru0()
    # RU 1 (row index 2 in downtime) has NaN curative → OK because no fault mode.
    sheets["Downtime"] = pd.DataFrame(
        {
            0: [None, "RU1", "RU2"],
            1: [None, 12.0, np.nan],
            2: [None, 6.0, np.nan],
            3: [None, 24.0, np.nan],
        }
    )
    # Must not raise.
    ExcelInputReader.from_sheets_data(sheets)


def test_downtime_preventive_nan_when_schedule_set_and_flag_true_raises():
    """Missing preventive downtime when schedule > 0 and prev_enabled → ValueError."""
    sheets = _make_all_required_sheets()
    # Enable preventive maintenance in LCIC.
    sheets["LCIC"].iloc[7, 1] = True
    # Give RU 0 a non-zero preventive schedule.
    sheets["Planned Maint."] = pd.DataFrame(
        {
            0: ["Prev. schedule", 2.0, 0.0],
            1: ["Moderni. schedule", 0.0, 0.0],
        }
    )
    # RU 0 (row index 1 in downtime) preventive column set to NaN.
    sheets["Downtime"] = pd.DataFrame(
        {
            0: [None, "RU1", "RU2"],
            1: [None, np.nan, 12.0],  # RU1 NaN
            2: [None, 6.0, 6.0],
            3: [None, 24.0, 24.0],
        }
    )
    with pytest.raises(ValueError, match="PREVENTIVE MAINT. downtime"):
        ExcelInputReader.from_sheets_data(sheets)


def test_downtime_preventive_nan_when_flag_false_is_valid():
    """NaN preventive downtime is accepted when prev_enabled is False."""
    sheets = _make_all_required_sheets()
    # prev_enabled remains False (default in _make_all_required_sheets).
    sheets["Planned Maint."] = pd.DataFrame(
        {
            0: ["Prev. schedule", 2.0, 2.0],
            1: ["Moderni. schedule", 0.0, 0.0],
        }
    )
    sheets["Downtime"] = pd.DataFrame(
        {
            0: [None] + [f"RU{i + 1}" for i in range(NB_RU)],
            1: [None] + [np.nan] * NB_RU,  # NaN but flag is False → OK
            2: [None] + [6.0] * NB_RU,
            3: [None] + [24.0] * NB_RU,
        }
    )
    # Must not raise.
    ExcelInputReader.from_sheets_data(sheets)


def test_downtime_preventive_nan_when_schedule_zero_is_valid():
    """NaN preventive downtime is accepted when schedule is zero, even if flag is True."""
    sheets = _make_all_required_sheets()
    sheets["LCIC"].iloc[7, 1] = True
    # All preventive schedules remain 0.0 (default).
    sheets["Downtime"] = pd.DataFrame(
        {
            0: [None] + [f"RU{i + 1}" for i in range(NB_RU)],
            1: [None] + [np.nan] * NB_RU,  # NaN but schedule is 0 → OK
            2: [None] + [6.0] * NB_RU,
            3: [None] + [24.0] * NB_RU,
        }
    )
    # Must not raise.
    ExcelInputReader.from_sheets_data(sheets)


def test_downtime_modernization_nan_when_schedule_set_and_flag_true_raises():
    """Missing modernization downtime when schedule > 0 and modernization_enabled → ValueError."""
    sheets = _make_all_required_sheets()
    # Enable modernization in LCIC.
    sheets["LCIC"].iloc[8, 1] = True
    # Give RU 1 a non-zero modernization schedule.
    sheets["Planned Maint."] = pd.DataFrame(
        {
            0: ["Prev. schedule", 0.0, 0.0],
            1: ["Moderni. schedule", 0.0, 3.0],
        }
    )
    # RU 1 (row index 2 in downtime) modernization column set to NaN.
    sheets["Downtime"] = pd.DataFrame(
        {
            0: [None, "RU1", "RU2"],
            1: [None] + [12.0] * NB_RU,
            2: [None, 6.0, np.nan],  # RU2 NaN
            3: [None] + [24.0] * NB_RU,
        }
    )
    with pytest.raises(ValueError, match="MODERNIZATION MAINT. downtime"):
        ExcelInputReader.from_sheets_data(sheets)


def test_downtime_modernization_nan_when_flag_false_is_valid():
    """NaN modernization downtime is accepted when modernization_enabled is False."""
    sheets = _make_all_required_sheets()
    # modernization_enabled remains False (default).
    sheets["Planned Maint."] = pd.DataFrame(
        {
            0: ["Prev. schedule", 0.0, 0.0],
            1: ["Moderni. schedule", 3.0, 3.0],
        }
    )
    sheets["Downtime"] = pd.DataFrame(
        {
            0: [None] + [f"RU{i + 1}" for i in range(NB_RU)],
            1: [None] + [12.0] * NB_RU,
            2: [None] + [np.nan] * NB_RU,  # NaN but flag is False → OK
            3: [None] + [24.0] * NB_RU,
        }
    )
    # Must not raise.
    ExcelInputReader.from_sheets_data(sheets)


def test_downtime_modernization_zero_for_ru_with_schedule_is_valid():
    """Modernization downtime of 0.0 (not NaN) is accepted when schedule > 0."""
    sheets = _make_all_required_sheets()
    sheets["LCIC"].iloc[8, 1] = True
    sheets["Planned Maint."] = pd.DataFrame(
        {
            0: ["Prev. schedule", 0.0, 0.0],
            1: ["Moderni. schedule", 3.0, 3.0],
        }
    )
    sheets["Downtime"] = pd.DataFrame(
        {
            0: [None] + [f"RU{i + 1}" for i in range(NB_RU)],
            1: [None] + [12.0] * NB_RU,
            2: [None] + [0.0] * NB_RU,  # 0 is valid
            3: [None] + [24.0] * NB_RU,
        }
    )
    # Must not raise.
    ExcelInputReader.from_sheets_data(sheets)
