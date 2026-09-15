"""PELCA Excel input reader."""

from __future__ import annotations

import logging
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

logger = logging.getLogger(__name__)


def _get(df: pd.DataFrame, label: str, col: int = 1) -> int | float | str | bool:
    """Return the cell value at column ``col`` in the first row that contains ``label``.

    Raises:
        ValueError: If the label is not found or the cell is empty.
    """
    matches = df[df.isin([label]).any(axis=1)].index
    if len(matches) == 0:
        raise ValueError(f"Label {label!r} not found")
    value = df.iloc[matches[0], col]
    if value is None or (isinstance(value, float) and pd.isna(value)):
        raise ValueError(f"Label {label!r} found but cell value is empty")
    return value  # type: ignore[return-value]


def _parse_bool(value: object, label: str) -> bool:
    """Parse a cell value to bool; accepts True/False, 'True'/'False', or 0/1."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        s = value.strip().lower()
        if s == "true":
            return True
        if s == "false":
            return False
    if isinstance(value, int | float) and not isinstance(value, bool):
        return bool(int(value))
    raise ValueError(f"Cannot parse {label!r} as boolean: {value!r}")


def _parse_profile_values(value: object, nb_profiles: int) -> list[float]:
    """Parse a cell that may contain '#'-separated values for multiple profiles.

    Accepts exactly 1 value (broadcast to all profiles) or exactly ``nb_profiles``
    values. Any other count raises ``ValueError``.

    Args:
        value: Raw cell content; may be a number or a string like ``"10#20"``.
            An empty cell (``NaN``) is treated as zero for all profiles.
        nb_profiles: Number of mission profiles declared in the LCIC sheet.

    Returns:
        A list of floats of length ``nb_profiles``.

    Raises:
        ValueError: If the number of '#'-separated parts is neither 1 nor
            ``nb_profiles``.
    """
    # Empty cell → treat as zero for every profile (e.g. maintenance not scheduled).
    if pd.isna(value):
        return [0.0] * nb_profiles
    parts = [p.strip() for p in str(value).split("#")]
    n_parts = len(parts)
    if n_parts != 1 and n_parts != nb_profiles:
        raise ValueError(
            f"Expected 1 or {nb_profiles} '#'-separated value(s) "
            f"(matching the number of mission profiles), got {n_parts}: {value!r}"
        )
    result: list[float] = []
    for i in range(nb_profiles):
        # Use the i-th part when available, otherwise broadcast the single value.
        part = parts[i] if i < n_parts else parts[0]
        try:
            result.append(float(part.replace(",", ".")))
        except ValueError:
            result.append(0.0)
    return result


_WEIBULL_COL_NAMES = [
    "sigma_early",
    "beta_early",
    "sigma_random",
    "beta_random",
    "sigma_wearout",
    "beta_wearout",
]


def _parse_weibull_column(df: pd.DataFrame, col: int, nb_profiles: int) -> np.ndarray:
    """Return a ``(nb_ru, nb_profiles)`` array from one Weibull parameter column."""
    nb_ru = len(df)
    result = np.zeros((nb_ru, nb_profiles), dtype=float)
    col_name = _WEIBULL_COL_NAMES[col] if col < len(_WEIBULL_COL_NAMES) else str(col)
    for ru in range(nb_ru):
        try:
            result[ru] = _parse_profile_values(df.iloc[ru, col], nb_profiles)
        except ValueError as exc:
            raise ValueError(
                f"[Sheet 'Faults'] RU row {ru + 1}, column '{col_name}': {exc}"
            ) from exc
    return result


def _build_failure_mode_mask(df_faults: pd.DataFrame) -> FaultModeMask:
    """Build per-RU failure-mode flags from the sigma/beta fault table.

    A mode is enabled when both sigma and beta are present for a given RU.
    When both are absent the mode is silently disabled for that RU.
    When exactly one of the two is present a ``ValueError`` is raised.
    """

    def _check_pair(
        row: pd.Series, sigma_col: int, beta_col: int, mode_name: str, ru_idx: int
    ) -> bool:
        sigma_present = not pd.isna(row.iloc[sigma_col])
        beta_present = not pd.isna(row.iloc[beta_col])
        if sigma_present and beta_present:
            return True
        if not sigma_present and not beta_present:
            return False
        missing = "beta" if sigma_present else "sigma"
        present = "sigma" if sigma_present else "beta"
        raise ValueError(
            f"[Sheet 'Faults'] RU row {ru_idx + 1}, '{mode_name}' failure: "
            f"{present} is set but {missing} is missing. "
            "Provide both parameters or neither."
        )

    early = np.array(
        [_check_pair(row, 0, 1, "Early", i) for i, (_, row) in enumerate(df_faults.iterrows())],
        dtype=bool,
    )
    random = np.array(
        [_check_pair(row, 2, 3, "Random", i) for i, (_, row) in enumerate(df_faults.iterrows())],
        dtype=bool,
    )
    wearout = np.array(
        [_check_pair(row, 4, 5, "Wearout", i) for i, (_, row) in enumerate(df_faults.iterrows())],
        dtype=bool,
    )
    return FaultModeMask(early=early, random=random, wearout=wearout)


def _parse_inventory_use(df: pd.DataFrame, nb_profiles: int) -> dict[str, list[float]]:
    """Parse the Inventory - Use sheet custom block format.

    Each activity block starts with a row where column 0 is ``"activity"`` and
    column 1 is the activity name. The first ``technosphere`` exchange amount is
    extracted per activity. Amounts may contain ``#``-separated profile values.

    Returns:
        A dict mapping activity name to a list of energy amounts per profile
        (length ``nb_profiles``).
    """
    result: dict[str, list[float]] = {}
    i = 0
    while i < len(df):
        if str(df.iloc[i, 0]).strip().lower() != "activity":
            i += 1
            continue

        name = str(df.iloc[i, 1]).strip()
        if not name:
            i += 1
            continue
        i += 1

        while i < len(df) and str(df.iloc[i, 0]).strip().lower() != "exchanges":
            i += 1
        if i >= len(df) or i + 1 >= len(df):
            break

        headers = df.iloc[i + 1]
        i += 2

        while i < len(df) and pd.notna(df.iloc[i, 0]):
            row = dict(zip(headers, df.iloc[i], strict=False))
            if str(row.get("type", "")).strip().lower() == "technosphere":
                raw_val = str(row.get("amount", "0"))
                try:
                    result[name] = _parse_profile_values(raw_val, nb_profiles)
                except ValueError as exc:
                    raise ValueError(f"[Sheet 'Inventory - Use'] Activity '{name}': {exc}") from exc
                break
            i += 1

    return result


def _validate_downtime(
    df_downtime: pd.DataFrame,
    nb_ru: int,
    fault_mask: FaultModeMask,
    prev_enabled: bool,
    modernization_enabled: bool,
    preventive_schedule: np.ndarray,
    modernization_schedule: np.ndarray,
) -> None:
    """Raise ``ValueError`` when a required downtime value is missing (NaN).

    Rules:
    - 'CUR. MAINT. downtime (hours)' must be defined for any RU that has at
      least one failure mode (early / random / wearout) declared in 'Faults'.
    - 'PREVENTIVE MAINT. downtime (hours)' must be defined for any RU that has
      a non-zero preventive schedule *and* preventive maintenance is enabled in
      the LCIC sheet.
    - 'MODERNIZATION MAINT. downtime (hours)' must be defined for any RU that
      has a non-zero modernization schedule *and* modernization is enabled in
      the LCIC sheet.

    Column order in ``df_downtime`` (B:D, after skipping header rows):
    - index 0 → preventive
    - index 1 → modernization
    - index 2 → curative

    Args:
        df_downtime: Raw downtime DataFrame (skiprows already applied).
        nb_ru: Number of replaceable units.
        fault_mask: Per-RU failure-mode flags built from the Faults sheet.
        prev_enabled: Whether preventive maintenance is enabled (LCIC flag).
        modernization_enabled: Whether modernization is enabled (LCIC flag).
        preventive_schedule: ``(nb_ru, nb_profiles)`` array of preventive
            maintenance frequencies.
        modernization_schedule: ``(nb_ru, nb_profiles)`` array of modernization
            frequencies.
    """
    # Slice the data rows (row 0 is the label row, rows 1..nb_ru are data).
    # Column layout after usecols="A:D": 0=name, 1=preventive, 2=modernization, 3=curative.
    raw_names = df_downtime.iloc[1: nb_ru + 1, 0].reset_index(drop=True)
    raw_prev = df_downtime.iloc[1: nb_ru + 1, 1].reset_index(drop=True)
    raw_moderni = df_downtime.iloc[1: nb_ru + 1, 2].reset_index(drop=True)
    raw_curative = df_downtime.iloc[1: nb_ru + 1, 3].reset_index(drop=True)

    for ru in range(nb_ru):
        # Use the element name from column A; fall back to row index if the cell is empty.
        raw_name = raw_names.iloc[ru]
        label = str(raw_name) if pd.notna(raw_name) else f"row {ru + 1}"

        # Check curative downtime: required when any failure mode is defined.
        has_fault = bool(fault_mask.early[ru] or fault_mask.random[ru] or fault_mask.wearout[ru])
        if has_fault and pd.isna(raw_curative.iloc[ru]):
            raise ValueError(
                f"[Sheet 'Downtime'] '{label}': "
                "'CUR. MAINT. downtime (hours)' is missing (NaN) "
                "but this element has at least one failure mode defined in 'Faults'."
            )

        # Check preventive downtime: required when the schedule is non-zero and flag is on.
        has_prev_schedule = bool(np.any(preventive_schedule[ru] > 0))
        if prev_enabled and has_prev_schedule and pd.isna(raw_prev.iloc[ru]):
            raise ValueError(
                f"[Sheet 'Downtime'] '{label}': "
                "'PREVENTIVE MAINT. downtime (hours)' is missing (NaN) "
                "but this element has a preventive maintenance schedule defined in "
                "'Planned Maint.' and preventive maintenance is enabled in LCIC."
            )

        # Check modernization downtime: required when the schedule is non-zero and flag is on.
        has_moderni_schedule = bool(np.any(modernization_schedule[ru] > 0))
        if modernization_enabled and has_moderni_schedule and pd.isna(raw_moderni.iloc[ru]):
            raise ValueError(
                f"[Sheet 'Downtime'] '{label}': "
                "'MODERNIZATION MAINT. downtime (hours)' is missing (NaN) "
                "but this element has a modernization schedule defined in "
                "'Planned Maint.' and modernization is enabled in LCIC."
            )


def _find_inventory_activities(df):
    """Return a list of activity names from an inventory sheet DataFrame."""
    return [row[1] for _, row in df.iterrows() if row[0] == "Activity"]


def _parse_cost_names(df: pd.DataFrame) -> ActivityNames:
    """Extract activity names from the Cost - Price sheet per lifecycle phase.

    Column 0 holds the activity name; columns 1–5 hold cost values for
    manufacturing, kwh_cost (use phase), planned maintenance, curative
    maintenance, and end-of-life respectively. A name is included for a
    category when both the name cell and the corresponding value cell are
    non-NaN.

    Args:
        df: The Cost - Price DataFrame with column 0 = activity names and
            columns 1–5 = cost values.

    Returns:
        An ``ActivityNames`` instance whose fields list the activity names for
        each lifecycle phase.
    """

    def _names_for_col(col: int) -> list[str]:
        # Keep rows where both the name column and the value column are present.
        mask = df.iloc[:, col].notna() & df.iloc[:, 0].notna()
        return df.iloc[mask.values, 0].astype(str).tolist()

    return ActivityNames(
        manufacturing=_names_for_col(1),
        use=_names_for_col(2),
        planned_maintenance=_names_for_col(3),
        curative_maintenance=_names_for_col(4),
        eol=_names_for_col(5),
    )


class ExcelInputReader:
    """Reads a PELCA input Excel file and returns a validated ``PelcaConfig``.

    Opens the file exactly once using a single ``pd.ExcelFile`` context.
    All validation is performed at read time; a ``ValueError`` is raised with
    context information for any invalid or missing value.
    """

    @staticmethod
    def from_excel(path: Path) -> PelcaConfig:
        """Parse the input Excel file and return a ``PelcaConfig``.

        This reads the workbook into DataFrames and delegates to
        :meth:`from_sheets_data`.
        """
        path = Path(path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")

        logger.info("Reading input file: %s", path)

        with pd.ExcelFile(path) as xl:
            df_lca = pd.read_excel(xl, sheet_name="LCA", header=None, skiprows=1)
            df_lcia = pd.read_excel(xl, sheet_name="LCIA", header=0, skiprows=1)
            df_lcic = pd.read_excel(xl, sheet_name="LCIC", header=None, skiprows=1)
            df_faults = pd.read_excel(
                xl,
                sheet_name="Faults",
                skiprows=[0, 1, 2],
                usecols="B:G",
            )
            df_cost = pd.read_excel(xl, sheet_name="Cost - Price", skiprows=3, usecols="A:F")
            df_rm = pd.read_excel(
                xl,
                sheet_name="Cur. Maint. (replac. matrix)",
                header=None,
                skiprows=[0, 1, 2, 3],
                usecols=lambda x: x != 0,
            )
            df_inv = pd.read_excel(xl, sheet_name="Inventory - Use", header=None)
            df_inv_manu = pd.read_excel(xl, sheet_name="Inventory - Manufacturing", header=None)
            df_inv_planned_maint = pd.read_excel(
                xl, sheet_name="Inventory - Planned Maint.", header=None
            )
            df_inv_curative_maint = pd.read_excel(
                xl, sheet_name="Inventory - Cur. Maint.", header=None
            )
            df_inv_eol = pd.read_excel(xl, sheet_name="Inventory - End of Life", header=None)

            # -- Downtime --
            df_downtime = pd.read_excel(
                xl, sheet_name="Downtime", header=None, skiprows=[0, 1, 2], usecols="A:D"
            )

            # Planned maintenance
            df_planned_maint = pd.read_excel(
                xl, sheet_name="Planned Maint.", header=None, skiprows=[0], usecols="B:C"
            )

        sheets = {
            "LCA": df_lca,
            "LCIA": df_lcia,
            "LCIC": df_lcic,
            "Faults": df_faults,
            "Cost - Price": df_cost,
            "Cur. Maint. (replac. matrix)": df_rm,
            "Inventory - Use": df_inv,
            "Inventory - Manufacturing": df_inv_manu,
            "Inventory - Planned Maint.": df_inv_planned_maint,
            "Inventory - Cur. Maint.": df_inv_curative_maint,
            "Inventory - End of Life": df_inv_eol,
            "Downtime": df_downtime,
            "Planned Maint.": df_planned_maint,
        }
        return ExcelInputReader.from_sheets_data(sheets)

    @staticmethod
    def from_sheets_data(sheets_data: dict[str, pd.DataFrame]) -> PelcaConfig:
        """Build a ``PelcaConfig`` directly from a mapping of sheet name -> DataFrame.

        Accepts the same DataFrame shapes produced by :meth:`from_excel`.
        """
        return ExcelInputReader._build(
            sheets_data["LCA"],
            sheets_data["LCIA"],
            sheets_data["LCIC"],
            sheets_data["Faults"],
            sheets_data["Cost - Price"],
            sheets_data["Cur. Maint. (replac. matrix)"],
            sheets_data["Inventory - Use"],
            sheets_data["Inventory - Manufacturing"],
            sheets_data["Inventory - Planned Maint."],
            sheets_data["Inventory - Cur. Maint."],
            sheets_data["Inventory - End of Life"],
            sheets_data["Downtime"],
            sheets_data["Planned Maint."],
        )

    @staticmethod
    def read(path: Path) -> PelcaConfig:
        """Backward-compatible alias for :meth:`from_excel`."""
        return ExcelInputReader.from_excel(path)

    @staticmethod
    def _build(
        df_lca: pd.DataFrame,
        df_lcia: pd.DataFrame,
        df_lcic: pd.DataFrame,
        df_faults: pd.DataFrame,
        df_cost: pd.DataFrame,
        df_rm: pd.DataFrame,
        df_inv: pd.DataFrame,
        df_inv_manu: pd.DataFrame,
        df_inv_planned_maint: pd.DataFrame,
        df_inv_curative_maint: pd.DataFrame,
        df_inv_eol: pd.DataFrame,
        df_downtime: pd.DataFrame,
        df_planned_maint: pd.DataFrame,
    ) -> PelcaConfig:
        # ── Activities name ───────────────────────────────────────────────
        activities_name = ActivityNames(
            manufacturing=_find_inventory_activities(df_inv_manu),
            use=_find_inventory_activities(df_inv),
            planned_maintenance=_find_inventory_activities(df_inv_planned_maint),
            curative_maintenance=_find_inventory_activities(df_inv_curative_maint),
            eol=_find_inventory_activities(df_inv_eol),
        )

        # ── LCA sheet ────────────────────────────────────────────────────────
        result_path = Path(str(_get(df_lca, "LCA result path")))
        lca_cfg = LcaConfig(
            project_name=str(_get(df_lca, "Project name (brightway)")),
            database=str(_get(df_lca, "Database ecoinvent")),
            ecoinvent_path=str(_get(df_lca, "Ecoinvent path")),
            inventory_name=str(_get(df_lca, "Inventory name")),
            activity_names=activities_name,
        )

        # ── LCIA sheet ───────────────────────────────────────────────────────
        lcia_cfg = LciaConfig(
            names=df_lcia["Acronym"].tolist(),
            units=df_lcia["Unit"].tolist(),
            method_tuples=[
                (
                    str(row["Method name"]),
                    str(row["Impact category"]),
                    str(row["Specific context"]),
                )
                for _, row in df_lcia.iterrows()
            ],
        )

        # ── LCIC sheet — scalar fields ──────────────────────────────────
        service_life = int(_get(df_lcic, "Service life (year)"))
        time_step = int(_get(df_lcic, "Time step (step/year)"))
        mc_iterations = int(_get(df_lcic, "Monte Carlo (number of iteration)"))
        hours_per_year = float(_get(df_lcic, "Annual usage time (hours/year)"))
        if hours_per_year > 8784:
            raise ValueError(f"Annual usage time {hours_per_year} exceeds 8784 hours/year.")
        selected_ei_name = str(_get(df_lcic, "Plot specific env. impact"))

        # ── Mission profiles ─────────────────────────────────────────────────
        if "Mission profile (%)" in df_lcic.values:
            raw_pm = str(_get(df_lcic, "Mission profile (%)"))
            pm_vals: list[float]
            if "#" in raw_pm:
                pm_vals = [float(x) for x in raw_pm.split("#") if x.strip()]
            else:
                pm_vals = [float(raw_pm)]
            nb_profiles = len(pm_vals)
            total = sum(pm_vals)
            if total <= 0:
                raise ValueError("Mission profile percentages sum to zero.")
            if abs(total - 100.0) > 1e-6:
                raise ValueError(
                    f"Mission profile percentages sum to {total:.6g} %%, expected 100 %. "
                    "Check the 'Mission profile (%)' values in the LCIC sheet."
                )
            mission_profile_probs = np.array(pm_vals) / total
        else:
            nb_profiles = 1
            mission_profile_probs = np.array([1.0])

        # ── Failure configuration ────────────────────────────────────────────
        failure_cfg = FailureConfig(
            early_enabled=_parse_bool(_get(df_lcic, "Early failure"), "Early failure"),
            random_enabled=_parse_bool(_get(df_lcic, "Random failure"), "Random failure"),
            wearout_enabled=_parse_bool(_get(df_lcic, "Wearout failure"), "Wearout failure"),
            mode_enabled_by_ru=_build_failure_mode_mask(df_faults),
            sigma_early=_parse_weibull_column(df_faults, 0, nb_profiles),
            beta_early=_parse_weibull_column(df_faults, 1, nb_profiles),
            sigma_random=_parse_weibull_column(df_faults, 2, nb_profiles),
            beta_random=_parse_weibull_column(df_faults, 3, nb_profiles),
            sigma_wearout=_parse_weibull_column(df_faults, 4, nb_profiles),
            beta_wearout=_parse_weibull_column(df_faults, 5, nb_profiles),
        )

        # ── Maintenance configuration ─────────────────────────────────────────
        nb_ru = len(df_faults)
        preventive_schedule = np.zeros((nb_ru, nb_profiles), dtype=float)
        modernization_schedule = np.zeros((nb_ru, nb_profiles), dtype=float)
        for ru in range(nb_ru):
            try:
                preventive_schedule[ru] = _parse_profile_values(
                    df_planned_maint.iloc[ru + 1, 0], nb_profiles
                )
            except ValueError as exc:
                raise ValueError(
                    f"[Sheet 'Planned Maint.'] RU row {ru + 1}, column 'Prev. schedule': {exc}"
                ) from exc
            try:
                modernization_schedule[ru] = _parse_profile_values(
                    df_planned_maint.iloc[ru + 1, 1], nb_profiles
                )
            except ValueError as exc:
                raise ValueError(
                    f"[Sheet 'Planned Maint.'] RU row {ru + 1}, column 'Moderni. schedule': {exc}"
                ) from exc

        maintenance_cfg = MaintenanceConfig(
            prev_enabled=_parse_bool(
                _get(df_lcic, "Preventive Maintenance"), "Preventive Maintenance"
            ),
            modernization_enabled=_parse_bool(_get(df_lcic, "Modernization"), "Modernization"),
            replacement_matrix=df_rm,
            preventive_schedule=preventive_schedule,
            modernization_schedule=modernization_schedule,
            names=df_planned_maint.iloc[0, :].astype(str).tolist(),
        )

        # ── Cost configuration ────────────────────────────────────────────────
        cost_cfg = CostConfig(
            manufacturing=df_cost.iloc[:, 1].dropna().to_numpy(dtype=float),
            kwh_cost=df_cost.iloc[:, 2].dropna().to_numpy(dtype=float),
            planned=df_cost.iloc[:, 3].dropna().to_numpy(dtype=float),
            curative=df_cost.iloc[:, 4].dropna().to_numpy(dtype=float),
            end_of_life=df_cost.iloc[:, 5].dropna().to_numpy(dtype=float),
            names=_parse_cost_names(df_cost),
        )

        # ── Inventory - Use ───────────────────────────────────────────────────
        energy_amounts = _parse_inventory_use(df_inv, nb_profiles)
        logger.info("Found %d activities in Inventory - Use", len(energy_amounts))

        # Validate downtime completeness before extracting values.
        _validate_downtime(
            df_downtime=df_downtime,
            nb_ru=nb_ru,
            fault_mask=failure_cfg.mode_enabled_by_ru,
            prev_enabled=maintenance_cfg.prev_enabled,
            modernization_enabled=maintenance_cfg.modernization_enabled,
            preventive_schedule=preventive_schedule,
            modernization_schedule=modernization_schedule,
        )

        # Downtime configuration — NaN in non-required cells is treated as 0.
        # Column layout: 0=name, 1=preventive, 2=modernization, 3=curative.
        preventive_downtime_hours = df_downtime.iloc[1:, 1].to_numpy(dtype=float)
        np.nan_to_num(preventive_downtime_hours, nan=0.0, copy=False)
        modernization_downtime_hours = df_downtime.iloc[1:, 2].to_numpy(dtype=float)
        np.nan_to_num(modernization_downtime_hours, nan=0.0, copy=False)
        curative_downtime_hours = df_downtime.iloc[1:, 3].to_numpy(dtype=float)
        np.nan_to_num(curative_downtime_hours, nan=0.0, copy=False)

        downtime_cfg = DowntimeConfig(
            preventive_hours=preventive_downtime_hours,
            modernization_hours=modernization_downtime_hours,
            curative_hours=curative_downtime_hours,
        )

        sim_cfg = SimulationConfig(
            service_life=service_life,
            time_step=time_step,
            mc_iterations=mc_iterations,
            hours_per_year=hours_per_year,
            nb_mission_profiles=nb_profiles,
            mission_profile_probs=mission_profile_probs,
            selected_ei_name=selected_ei_name,
            energy_amounts=energy_amounts,
            failure=failure_cfg,
            maintenance=maintenance_cfg,
            cost=cost_cfg,
            downtime=downtime_cfg,
        )
        output_cfg = OutputConfig(result_path=result_path)

        config = PelcaConfig(
            lca=lca_cfg,
            lcia=lcia_cfg,
            simulation=sim_cfg,
            output=output_cfg,
        )

        ExcelInputReader._check_unique_activity_names(config)
        ExcelInputReader._validate_cross_sheet(config, nb_ru)
        return config

    @staticmethod
    def _check_unique_activity_names(lca_config: PelcaConfig) -> None:
        """Raise ``ValueError`` if any activity name is duplicated across inventory sheets."""
        if not lca_config.lca.activity_names._unique:
            raise ValueError("Duplicate activity names found across inventory sheets.")

    @staticmethod
    def _validate_cross_sheet(config: PelcaConfig, nb_ru: int) -> None:
        """Raise ``ValueError`` if cross-sheet consistency checks fail.

        Checks performed:
        - Cost and maintenance arrays have the same length as ``nb_ru``.
        - Inventory - Planned Maint. and Inventory - Cur. Maint. each declare
          exactly ``nb_ru`` activities.
        - Curative maintenance replacement matrix is square with side ``nb_ru``.
        - ``selected_ei_name`` is present in ``lcia.names``.
        """
        sim = config.simulation

        for name, arr in (
            ("planned", sim.cost.planned),
            ("curative", sim.cost.curative),
        ):
            if len(arr) != nb_ru:
                raise ValueError(
                    f"[Sheet 'Cost - Price'] Column '{name}' has {len(arr)} rows "
                    f"but 'Faults' has {nb_ru} RUs."
                )

        for arr_name, arr in (
            ("preventive_schedule", sim.maintenance.preventive_schedule),
            ("modernization_schedule", sim.maintenance.modernization_schedule),
        ):
            if arr.shape[0] != nb_ru:
                raise ValueError(
                    f"[Sheet 'Faults'] Maintenance '{arr_name}' has "
                    f"{arr.shape[0]} rows but expected {nb_ru}."
                )

        # -- Curative maintenance replacement matrix must be nb_ru × nb_ru.
        rm_shape = config.simulation.maintenance.replacement_matrix.shape
        if rm_shape != (nb_ru, nb_ru):
            raise ValueError(
                f"[Sheet 'Cur. Maint. (replac. matrix)'] Matrix has shape {rm_shape} "
                f"but expected ({nb_ru}, {nb_ru}) to match 'Faults' ({nb_ru} RUs)."
            )

        # -- Inventory sheets: each must declare exactly nb_ru activities.
        for sheet_label, names in (
            ("Inventory - Planned Maint.", config.lca.activity_names.planned_maintenance),
            ("Inventory - Cur. Maint.", config.lca.activity_names.curative_maintenance),
        ):
            if len(names) != nb_ru:
                raise ValueError(
                    f"[Sheet '{sheet_label}'] Found {len(names)} activities "
                    f"but 'Faults' has {nb_ru} RUs. "
                    "Every RU must have exactly one planned and one curative maintenance activity."
                )

        if config.simulation.selected_ei_name not in config.lcia.names:
            raise ValueError(
                f"[Sheet 'LCIC'] 'Plot specific env. impact' value "
                f"{config.simulation.selected_ei_name!r} does not match any name "
                f"in the LCIA sheet. Available names: {config.lcia.names}."
            )

        # -- Downtime
        for downtime_type, downtime_hours in (
            ("Preventive", sim.downtime.preventive_hours),
            ("Modernization", sim.downtime.modernization_hours),
            ("Curative", sim.downtime.curative_hours),
        ):
            if len(downtime_hours) != nb_ru:
                msg = (
                    f"[Sheet 'Downtime'] {downtime_type} downtime has "
                    f"{len(downtime_hours)} rows "
                    f"but 'Faults' has {nb_ru} RUs."
                )
                raise ValueError(msg)

    @staticmethod
    def validate_lca_inventory(path: Path, config: PelcaConfig) -> None:
        """Check that brightway2 inventory activity names match ``energy_amounts``.

        Opens the input file a second time (read-only) to read the
        ``Inventory - Manufacturing`` and ``Inventory - Use`` brightway2 sheets,
        then verifies that every activity referenced in
        ``config.simulation.energy_amounts`` appears in at least one of those sheets.

        This method is only called by ``PelcaRunner`` when ``run_lca=True``.

        Args:
            path: Path to the input ``.xlsx`` or ``.xlsm`` file.
            config: Previously parsed configuration for this file.

        Raises:
            ValueError: If any activity in ``energy_amounts`` is absent from the
                brightway2 inventory sheets.
        """
        path = Path(path).resolve()
        inventory_activities: set[str] = set()

        with pd.ExcelFile(path) as xl:
            for sheet in ("Inventory - Use", "Inventory - Manufacturing"):
                if sheet not in xl.sheet_names:
                    continue
                df = pd.read_excel(xl, sheet_name=sheet, header=None)
                for i in range(len(df)):
                    if str(df.iloc[i, 0]).strip().lower() == "activity":
                        name = str(df.iloc[i, 1]).strip()
                        if name:
                            inventory_activities.add(name)

        energy_activities = set(config.simulation.energy_amounts.keys())
        unknown = energy_activities - inventory_activities
        if unknown:
            raise ValueError(
                f"[Sheet 'Inventory - Use'] The following activities are referenced in "
                f"'energy_amounts' but not found in any brightway2 inventory sheet: "
                f"{sorted(unknown)}"
            )
