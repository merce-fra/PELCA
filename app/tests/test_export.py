"""Unit tests for app/io/export.py."""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.io.export import (
    _unique_path,
    export_config,
    export_excel,
    export_lcic_summary,
    export_numpy,
)
from app.tests.fixtures import (
    LCIA_NAMES,
    _make_eco_result,
    _make_lca_result,
    _make_simulation_result,
    make_config,
)

# ---------------------------------------------------------------------------
# _unique_path
# ---------------------------------------------------------------------------


def test_unique_path_returns_base_when_free(tmp_path: Path) -> None:
    dest = _unique_path(tmp_path, "report", "xlsx")
    assert dest == tmp_path / "report.xlsx"


def test_unique_path_increments_on_collision(tmp_path: Path) -> None:
    (tmp_path / "report.xlsx").touch()
    dest1 = _unique_path(tmp_path, "report", "xlsx")
    assert dest1 == tmp_path / "report_1.xlsx"
    dest1.touch()
    dest2 = _unique_path(tmp_path, "report", "xlsx")
    assert dest2 == tmp_path / "report_2.xlsx"


# ---------------------------------------------------------------------------
# export_numpy
# ---------------------------------------------------------------------------


def test_export_numpy_roundtrip(tmp_path: Path) -> None:
    arr = np.array([[1.0, 2.0], [3.0, 4.0]])
    export_numpy("data", arr, tmp_path)
    dest = tmp_path / "data.npy"
    assert dest.exists()
    loaded = np.load(dest)
    np.testing.assert_array_equal(loaded, arr)


# ---------------------------------------------------------------------------
# export_excel
# ---------------------------------------------------------------------------


def test_export_excel_2d_array(tmp_path: Path) -> None:
    arr = np.arange(6, dtype=float).reshape(2, 3)
    export_excel("matrix", arr, tmp_path)
    dest = tmp_path / "matrix.xlsx"
    assert dest.exists()
    df = pd.read_excel(dest, header=0)
    assert df.shape == (3, 2)


def test_export_excel_flattens_3d_array(tmp_path: Path) -> None:
    arr = np.ones((4, 3, 2), dtype=float)
    export_excel("cube", arr, tmp_path)
    dest = tmp_path / "cube.xlsx"
    df = pd.read_excel(dest, header=0)
    assert df.shape == (6, 4)


# ---------------------------------------------------------------------------
# export_config
# ---------------------------------------------------------------------------


def test_export_config_creates_csv_and_pkl(tmp_path: Path) -> None:
    cfg = make_config(result_path=tmp_path)
    export_config(cfg, tmp_path)
    assert (tmp_path / "dict_file.csv").exists()
    assert (tmp_path / "dict_file.pkl").exists()


def test_export_config_pickle_roundtrip(tmp_path: Path) -> None:
    cfg = make_config(result_path=tmp_path)
    export_config(cfg, tmp_path)
    with (tmp_path / "dict_file.pkl").open("rb") as fh:
        loaded = pickle.load(fh)
    # PelcaConfig contains numpy arrays; compare scalar fields to avoid
    # the ValueError raised by bool(array == array).
    assert type(loaded) is type(cfg)
    assert loaded.lca.project_name == cfg.lca.project_name
    assert loaded.output.result_path == cfg.output.result_path


# ---------------------------------------------------------------------------
# export_lcic_summary
# ---------------------------------------------------------------------------


def test_export_lcic_summary_creates_file(tmp_path: Path) -> None:
    cfg = make_config(result_path=tmp_path)
    export_lcic_summary(_make_simulation_result(), _make_lca_result(), cfg)
    dest = cfg.output.lca_dir / cfg.output.lcic_output_filename
    assert dest.exists()


def test_export_lcic_summary_columns(tmp_path: Path) -> None:
    cfg = make_config(result_path=tmp_path)
    cfg.simulation.maintenance.enabled = True
    export_lcic_summary(_make_simulation_result(), _make_lca_result(), cfg)
    dest = cfg.output.lca_dir / cfg.output.lcic_output_filename
    df = pd.read_excel(dest)
    expected_cols = [
        "Method",
        "LCIA Unit",
        "Manufacture",
        "Use",
        "Cur. Maint.",
        "Planned Maint.",
        "End Of Life",
    ]
    assert list(df.columns) == expected_cols


def test_export_lcic_summary_row_count(tmp_path: Path) -> None:
    cfg = make_config(result_path=tmp_path)
    export_lcic_summary(_make_simulation_result(), _make_lca_result(), cfg)
    dest = cfg.output.lca_dir / cfg.output.lcic_output_filename
    df = pd.read_excel(dest)
    # One row per LCIA method + one ECO row
    assert len(df) == len(LCIA_NAMES) + 2  # Downtime + ECO


def test_export_lcic_summary_eco_row(tmp_path: Path) -> None:
    cfg = make_config(result_path=tmp_path)
    eco = _make_eco_result()
    export_lcic_summary(_make_simulation_result(), _make_lca_result(), cfg)
    dest = cfg.output.lca_dir / cfg.output.lcic_output_filename
    df = pd.read_excel(dest)
    last_row = df.iloc[-1]
    assert last_row["Method"] == "ECO"
    assert last_row["LCIA Unit"] == "€"
    assert last_row["Manufacture"] == pytest.approx(float(eco.manufacturing.sum()))
    assert last_row["End Of Life"] == pytest.approx(float(eco.end_of_life.sum()))


# ---------------------------------------------------------------------------
# maintenance.enabled flag TODO : Update this part of test since we have 2 != flags
# ---------------------------------------------------------------------------
