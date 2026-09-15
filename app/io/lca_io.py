"""Read and write the LCA output Excel artefact (``LCA output.xlsx``)."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from app.core.config import PelcaConfig
from app.core.lca import LcaResult
from app.io.export import _auto_adjust_column_width

logger = logging.getLogger(__name__)

_REQUIRED_SHEETS = {"Manufacturing", "EoL"}


def read_lca_output(path: Path, config: PelcaConfig) -> LcaResult:
    """Read a ``LCA output.xlsx`` file and return a validated ``LcaResult``.

    Accepts any valid file regardless of its origin: a previous PELCA run,
    a copy from another machine, or an externally produced file.

    Args:
        path: Full path to ``LCA output.xlsx``.
        config: The ``PelcaConfig`` for this run (used to extract ``nb_ei``
            and to determine the number of mission profiles).

    Returns:
        A populated ``LcaResult``.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        ValueError: If required sheets are missing or array dimensions are
            inconsistent with ``config``.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"LCA output file not found: {path}")

    nb_ei = len(config.lcia.names)
    nb_profiles = config.simulation.nb_mission_profiles

    logger.info("Reading LCA output: %s", path)

    with pd.ExcelFile(path) as xl:
        present = set(xl.sheet_names)
        use_sheets = _discover_use_sheets(nb_profiles)

        missing = (_REQUIRED_SHEETS | set(use_sheets)) - present
        if missing:
            raise ValueError(f"[LCA output] Missing sheet(s): {sorted(missing)} in {path}")

        manufacturing = _read_ei_sheet(xl, "Manufacturing", nb_ei, path)
        planned_maintenance = _read_ei_sheet(xl, "Planned Maintenance", nb_ei, path)
        curative_maintenance = _read_ei_sheet(xl, "Curative Maintenance", nb_ei, path)
        eol = _read_ei_sheet(xl, "EoL", nb_ei, path)

        use_per_profile: dict[int, np.ndarray] = {}
        for i, sheet in enumerate(use_sheets):
            use_per_profile[i] = _read_ei_sheet(xl, sheet, nb_ei, path)

    if nb_profiles == 1:
        use: np.ndarray = use_per_profile[0]
    else:
        probs = config.simulation.mission_profile_probs
        use = sum(use_per_profile[i] * probs[i] for i in range(nb_profiles))

    nb_ru = planned_maintenance.shape[1]

    return LcaResult(
        manufacturing=manufacturing,
        use=use,
        planned_maintenance=planned_maintenance,
        curative_maintenance=curative_maintenance,
        eol=eol,
        use_per_profile=use_per_profile,
        nb_ru=nb_ru,
    )


def export_lca_result(
    result: LcaResult, config: PelcaConfig, output_path: Path | None = None
) -> None:
    """Write a ``LcaResult`` to ``LCA output.xlsx``.

    Overwrites any existing file. Creates parent directories if absent.

    Args:
        result: The LCA result to persist.
        config: Run configuration (provides output path and LCIA metadata).
        output_path: Override destination path. Defaults to
            ``config.output.lca_file``.
    """
    dest = Path(output_path) if output_path is not None else config.output.lca_file
    dest.parent.mkdir(parents=True, exist_ok=True)

    method_acronyms = config.lcia.names
    units = config.lcia.units

    logger.info("Writing LCA output: %s", dest)

    with pd.ExcelWriter(dest, engine="openpyxl") as writer:
        _write_ei_sheet(
            writer,
            "Manufacturing",
            result.manufacturing,
            config.lca.activity_names.manufacturing,
            method_acronyms,
            units,
        )

        for i, arr in result.use_per_profile.items():
            sheet = "Use" if len(result.use_per_profile) == 1 else f"Use{i + 1}"
            _write_ei_sheet(
                writer, sheet, arr, config.lca.activity_names.use, method_acronyms, units
            )

        _write_ei_sheet(
            writer,
            "Planned Maintenance",
            result.planned_maintenance,
            config.lca.activity_names.planned_maintenance,
            method_acronyms,
            units,
        )

        _write_ei_sheet(
            writer,
            "Curative Maintenance",
            result.curative_maintenance,
            config.lca.activity_names.curative_maintenance,
            method_acronyms,
            units,
        )

        _write_ei_sheet(
            writer, "EoL", result.eol, config.lca.activity_names.eol, method_acronyms, units
        )

    _auto_adjust_column_width(dest)


# ── helpers ──────────────────────────────────────────────────────────────────


def _discover_use_sheets(nb_profiles: int) -> list[str]:
    """Return ordered list of Use sheet names expected for ``nb_profiles``."""
    if nb_profiles == 1:
        return ["Use"]
    return [f"Use{i + 1}" for i in range(nb_profiles)]


def _read_ei_sheet(xl: pd.ExcelFile, sheet: str, nb_ei: int, source: Path) -> np.ndarray:
    """Read one EI sheet and return an ``(nb_ei, nb_ru)`` array.

    The sheet is expected to have an index column (method names) and a ``Unit``
    column, with the remaining columns being RU/activity values.
    """
    df = pd.read_excel(xl, sheet_name=sheet, index_col=0)
    if "Unit" in df.columns:
        df = df.drop(columns=["Unit"])
    arr = df.to_numpy(dtype=float)
    if arr.shape[0] != nb_ei:
        raise ValueError(
            f"[LCA output sheet '{sheet}'] Expected {nb_ei} rows (LCIA methods) "
            f"but found {arr.shape[0]} in {source}."
        )
    return arr


def _write_ei_sheet(
    writer: pd.ExcelWriter,
    sheet: str,
    arr: np.ndarray,
    activity_names: list[str],
    index: list[str],
    units: list[str],
) -> None:
    """Write one ``(nb_ei, nb_ru)`` array to an Excel sheet with a Unit column."""
    ru_cols = activity_names
    df = pd.DataFrame(arr, index=index, columns=ru_cols)
    df.insert(0, "Unit", units)
    df.index.name = "Method"
    df.to_excel(writer, sheet_name=sheet, index=True)
