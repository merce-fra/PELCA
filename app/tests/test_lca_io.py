"""Tests for app/io/lca_io.py"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.core.lca import LcaResult
from app.io import lca_io
from app.tests.fixtures import (
    NB_ACT_CM,
    NB_ACT_EOL,
    NB_ACT_MANU,
    NB_ACT_PM,
    NB_ACT_USE,
    NB_EI,
    _make_lca_result,
    make_config,
)


def _make_ei_df(index: list[str], units: list[str], arr: np.ndarray) -> pd.DataFrame:
    nb_ru = arr.shape[1]
    cols = [f"RU{i + 1}" for i in range(nb_ru)]
    df = pd.DataFrame(arr, index=index, columns=cols)
    df.insert(0, "Unit", units)
    df.index.name = "Method"
    return df


def test_export_and_read_roundtrip_single_profile(tmp_path: Path):
    cfg = make_config()

    # Expected values based on _make_lca_result() with current dimensions
    manu = np.arange(NB_EI * NB_ACT_MANU, dtype=float).reshape(NB_EI, NB_ACT_MANU) + 1.0
    use = np.arange(NB_EI * NB_ACT_USE, dtype=float).reshape(NB_EI, NB_ACT_USE) + 10.0
    eol = np.arange(NB_EI * NB_ACT_EOL, dtype=float).reshape(NB_EI, NB_ACT_EOL) * 0.1 + 100.0

    result = _make_lca_result()

    out = tmp_path / "LCA output.xlsx"
    lca_io.export_lca_result(result, cfg, output_path=out)

    loaded = lca_io.read_lca_output(out, cfg)

    assert np.allclose(loaded.manufacturing, manu)
    # For single profile, read_lca_output returns `use` equal to the single profile array
    assert np.allclose(loaded.use, use)
    assert np.allclose(loaded.eol, eol)
    assert 0 in loaded.use_per_profile and np.allclose(loaded.use_per_profile[0], use)


def test_export_and_read_roundtrip_multi_profile(tmp_path: Path):
    cfg = make_config(nb_ru=1, nb_profiles=2)
    nb_ei = len(cfg.lcia.names)

    # Create test data with correct dimensions matching NB_ACT_* constants
    manu = np.arange(nb_ei * NB_ACT_MANU, dtype=float).reshape(nb_ei, NB_ACT_MANU) + 2.0
    use0 = np.arange(nb_ei * NB_ACT_USE, dtype=float).reshape(nb_ei, NB_ACT_USE) + 3.0
    use1 = np.arange(nb_ei * NB_ACT_USE, dtype=float).reshape(nb_ei, NB_ACT_USE) + 5.0
    eol = np.arange(nb_ei * NB_ACT_EOL, dtype=float).reshape(nb_ei, NB_ACT_EOL) + 7.0

    # Expected weighted use: average because fixtures give equal mission_profile_probs
    expected_use = (use0 + use1) / 2.0

    result = LcaResult(
        manufacturing=manu,
        use=expected_use,
        planned_maintenance=np.zeros((nb_ei, NB_ACT_PM)),
        curative_maintenance=np.zeros((nb_ei, NB_ACT_CM)),
        eol=eol,
        use_per_profile={0: use0, 1: use1},
        nb_ru=1,
    )

    out = tmp_path / "LCA output.xlsx"
    lca_io.export_lca_result(result, cfg, output_path=out)

    loaded = lca_io.read_lca_output(out, cfg)

    assert np.allclose(loaded.manufacturing, manu)
    assert np.allclose(loaded.use, expected_use)
    assert np.allclose(loaded.eol, eol)
    assert 0 in loaded.use_per_profile and 1 in loaded.use_per_profile


def test_read_missing_sheets_raises(tmp_path: Path):
    cfg = make_config()
    nb_ei = len(cfg.lcia.names)

    # Write an Excel with only Manufacturing (missing Use and EoL)
    manu = np.ones((nb_ei, 1), dtype=float)
    df_manu = _make_ei_df(cfg.lcia.names, cfg.lcia.units, manu)
    out = tmp_path / "bad_lca.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df_manu.to_excel(writer, sheet_name="Manufacturing", index=True)

    with pytest.raises(ValueError):
        lca_io.read_lca_output(out, cfg)
