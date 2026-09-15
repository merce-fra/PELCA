from pathlib import Path

import pytest

from app.core.lca import lca_generator
from app.io import reader

_HERE = Path(__file__).parent
_SAMPLE = (
    Path(__file__).parents[2]
    / "PELCA datasets"
    / "PowerModuleAndCapacitor"
    / "PELCA_v2.0.0_PowerModuleAndCapacitor.xlsx"
)


@pytest.mark.slow
@pytest.mark.skipif(not _SAMPLE.exists(), reason="Sample Excel not available")
def test_lca_generator_runs_without_error():
    pelca_config = reader.ExcelInputReader.from_excel(_SAMPLE)
    config = lca_generator(_SAMPLE, pelca_config)
    assert config is not None, "LCA generator should return a config object"
