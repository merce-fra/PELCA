"""LCA result types and brightway2 computation engine.

Exposes ``LcaResult`` (manufacturing, use, and end-of-life impact arrays) and
``lca_generator()``, which drives the brightway2 computation against an
ecoinvent database for every mission profile defined in the input Excel.
No file I/O: the caller (``PelcaRunner``) decides whether to persist the result.
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import brightway2 as bw
import numpy as np
import pandas as pd

from app.core.config import LcaConfig, LciaConfig, PelcaConfig

logger = logging.getLogger(__name__)


@dataclass
class LcaResult:
    """Environmental impact arrays computed or loaded from ``LCA output.xlsx``.

    All arrays use rows = LCIA methods (``nb_ei``).

    Attributes:
        manufacturing: Shape ``(nb_ei, nb_ru_manu)``.
        use: Weighted average across profiles. Shape ``(nb_ei, nb_ru_use)``.
        eol: Shape ``(nb_ei, nb_ru_eol)``.
        use_per_profile: Mapping of profile index to ``(nb_ei, nb_ru_use)`` array.
        nb_ru: Total RU count across all three phases.
    """

    manufacturing: np.ndarray
    use: np.ndarray
    planned_maintenance: np.ndarray
    curative_maintenance: np.ndarray
    eol: np.ndarray
    use_per_profile: dict[int, np.ndarray]
    nb_ru: int

    @property
    def manufacturing_total(self) -> np.ndarray:
        """Total manufacturing impact per method, summed across RUs."""
        return self.manufacturing.sum(axis=1)

    @property
    def use_total(self) -> np.ndarray:
        """Total use impact per method, summed across RUs."""
        return self.use.sum(axis=1)

    @property
    def planned_maintenance_total(self) -> np.ndarray:
        """Total planned maintenance impact per method, summed across RUs."""
        return self.planned_maintenance.sum(axis=1)

    @property
    def curative_maintenance_total(self) -> np.ndarray:
        """Total curative maintenance impact per method, summed across RUs."""
        return self.curative_maintenance.sum(axis=1)

    @property
    def eol_total(self) -> np.ndarray:
        """Total end-of-life impact per method, summed across RUs."""
        return self.eol.sum(axis=1)

    @property
    def nb_activity_manufacturing(self) -> int:
        """Number of manufacturing activities (RU count)."""
        return self.manufacturing.shape[1]

    @property
    def nb_activity_use(self) -> int:
        """Number of use activities (RU count)."""
        return self.use.shape[1]

    @property
    def nb_activity_eol(self) -> int:
        """Number of end-of-life activities (RU count)."""
        return self.eol.shape[1]

    @property
    def nb_env_impacts(self) -> int:
        """Number of environmental impact methods."""
        return self.manufacturing.shape[0]


def _get_cache_dirs() -> list[str]:
    """Return OS-specific cache directories."""
    system = platform.system()
    if system == "Windows":
        return [os.path.join(os.path.expandvars("%USERPROFILE%"), "AppData")]
    if system == "Darwin":
        return [os.path.expanduser("~/Library/Caches")]
    return [os.path.expanduser("~/.cache"), os.path.expanduser("~/.local/share")]


def _delete_project_cache(project_name: str) -> None:
    """Delete brightway cache folders whose name contains *project_name*."""
    for base_dir in _get_cache_dirs():
        if not os.path.isdir(base_dir):
            continue
        for root, dirs, _ in os.walk(base_dir):
            for dir_name in dirs:
                if project_name in dir_name:
                    folder_path = os.path.join(root, dir_name)
                    try:
                        shutil.rmtree(folder_path)
                        logger.debug("Deleted cache folder: %s", folder_path)
                    except OSError as exc:
                        logger.warning("Could not delete cache folder %s: %s", folder_path, exc)


def _force_amount_float(data: list[Any], profile_index: int, nb_profiles: int) -> list[Any]:
    """Brightway2 importer strategy that converts '#'-separated amounts to floats.

    Selects the value at *profile_index* when amounts encode multiple profiles.
    """
    data_temp = data.copy() if profile_index == 0 else data
    for item in data_temp:
        if "exchanges" not in item:
            continue
        for exc in item["exchanges"]:
            amount = exc.get("amount")
            if not isinstance(amount, str):
                continue
            try:
                if nb_profiles > 1 and "#" in amount:
                    amount = amount.split("#")[profile_index]
                exc["amount"] = float(amount.replace(",", "."))
            except (ValueError, IndexError) as parse_exc:
                logger.warning("Could not convert amount %r: %s", amount, parse_exc)
    return data_temp


def _setup_brightway_project(lca_config: LcaConfig) -> None:
    """Initialise the brightway2 project and import ecoinvent if not already present."""
    _delete_project_cache(lca_config.project_name)
    bw.projects.set_current(lca_config.project_name)
    bw.bw2setup()
    if lca_config.database not in bw.databases:
        logger.info("Importing ecoinvent database from %s", lca_config.ecoinvent_path)
        importer = bw.SingleOutputEcospold2Importer(
            lca_config.ecoinvent_path, lca_config.database, use_mp=False
        )
        importer.apply_strategies()
        importer.statistics()
        importer.write_database()
    bw.create_core_migrations()


def _import_inventory_for_profile(
    input_path: Path,
    lca_config: LcaConfig,
    profile_index: int,
    nb_profiles: int,
) -> Any:
    """Import the Excel inventory for one mission profile into brightway2.

    Returns:
        The loaded ``bw.Database`` for the current project.
    """
    imp = bw.ExcelImporter(str(input_path))
    imp.strategies.append(
        lambda data, idx=profile_index, n=nb_profiles: _force_amount_float(data, idx, n)
    )
    imp.apply_strategies()
    imp.match_database(fields=("name", "unit", "location"))
    imp.match_database(lca_config.database, fields=("name", "unit", "location"))
    imp.statistics()
    imp.write_database()
    return bw.Database(lca_config.inventory_name)


def _compute_lca_scores(
    activities: Any,
    methods: list[tuple[str, str, str]],
    activity_names: list[str] | None = None,
) -> list[tuple[str, str, float]]:
    """Run unit LCA for each activity and method combination.

    Args:
        activities: Brightway2 database of activities to evaluate.
        methods: LCIA method tuples ``(method_name, impact_category, context)``.
        activity_names: If given, only activities whose name is in this list are processed.

    Returns:
        List of ``(activity_name, method_category, score)`` tuples.
    """
    results: list[tuple[str, str, float]] = []
    for act in activities:
        if activity_names is not None and act["name"] not in activity_names:
            continue
        logger.info("Computing LCA for activity: %s", act)
        lca = bw.LCA({act: 1})
        lca.lci()
        for method in methods:
            lca.switch_method(method)
            lca.lcia()
            results.append((act["name"], method[1].title(), lca.score))
    return results


def _scores_to_array(
    raw_scores: list[tuple[str, str, float]],
    lcia_config: LciaConfig,
    activity_names: list[str],
) -> np.ndarray:
    """Convert raw LCA score tuples to a ``(nb_ei, nb_ru)`` numpy array.

    Rows are ordered by ``lcia_config.names``; columns follow *activity_names*.
    """
    df = pd.DataFrame(raw_scores, columns=["Name", "Method", "Score"])
    method_order = df["Method"].unique()
    df = df.pivot(index="Method", columns="Name", values="Score")
    df = df.reindex(method_order)
    rename_dict = dict(zip(method_order, lcia_config.names, strict=False))
    df = df.rename(index=rename_dict)
    ordered_cols = [c for c in activity_names if c in df.columns]
    return df[ordered_cols].to_numpy(dtype=float)


def _compute_use_weighted_average(
    use_per_profile: dict[int, np.ndarray],
    mission_profile_probs: np.ndarray,
) -> np.ndarray:
    """Return the profile-weighted average of use impact arrays.

    Each profile is weighted by its fraction of total operating time.
    """
    weighted: np.ndarray = np.sum(
        [use_per_profile[i] * mission_profile_probs[i] for i in range(len(mission_profile_probs))],
        axis=0,
    )
    return weighted


def lca_generator(input_path: Path, config: PelcaConfig) -> LcaResult:
    """Run brightway2 LCA calculations for all mission profiles and return results.

    For the first profile, manufacturing, use, and end-of-life impacts are computed.
    For subsequent profiles, only use impacts are recomputed with profile-specific
    amounts. Manufacturing and EoL results are identical across profiles.

    Args:
        input_path: Path to the PELCA input Excel workbook used as brightway2 inventory.
        config: Fully parsed PELCA configuration.

    Returns:
        An ``LcaResult`` containing per-phase impact arrays and per-profile use data.

    Raises:
        RuntimeError: If manufacturing or EoL arrays were not produced (should not happen).
    """
    # Unpack config sections for readability.
    lca_cfg = config.lca
    lcia_cfg = config.lcia
    sim_cfg = config.simulation

    methods = lcia_cfg.method_tuples
    nb_profiles = sim_cfg.nb_mission_profiles

    # Placeholders filled on the first profile pass.
    manufacturing_array: np.ndarray | None = None
    planned_maintenance_array: np.ndarray | None = None
    curative_maintenance_array: np.ndarray | None = None
    eol_array: np.ndarray | None = None
    use_per_profile: dict[int, np.ndarray] = {}

    for profile_index in range(nb_profiles):
        logger.info("Processing mission profile %d / %d", profile_index + 1, nb_profiles)
        # Reinitialise the brightway2 project and import inventory for this profile.
        _setup_brightway_project(lca_cfg)
        activities = _import_inventory_for_profile(input_path, lca_cfg, profile_index, nb_profiles)

        if profile_index == 0:
            # First pass: compute manufacturing, use, and EoL scores in one call.
            all_activity_names = (
                lca_cfg.activity_names.manufacturing
                + lca_cfg.activity_names.use
                + lca_cfg.activity_names.planned_maintenance
                + lca_cfg.activity_names.curative_maintenance
                + lca_cfg.activity_names.eol
            )
            scores = _compute_lca_scores(activities, methods, activity_names=all_activity_names)

            # Split scores by life-cycle phase and convert to (nb_ei, nb_ru) arrays.
            manufacturing_array = _scores_to_array(
                [s for s in scores if s[0] in lca_cfg.activity_names.manufacturing],
                lcia_cfg,
                lca_cfg.activity_names.manufacturing,
            )
            eol_array = _scores_to_array(
                [s for s in scores if s[0] in lca_cfg.activity_names.eol],
                lcia_cfg,
                lca_cfg.activity_names.eol,
            )
            planned_maintenance_array = _scores_to_array(
                [s for s in scores if s[0] in lca_cfg.activity_names.planned_maintenance],
                lcia_cfg,
                lca_cfg.activity_names.planned_maintenance,
            )
            curative_maintenance_array = _scores_to_array(
                [s for s in scores if s[0] in lca_cfg.activity_names.curative_maintenance],
                lcia_cfg,
                lca_cfg.activity_names.curative_maintenance,
            )
            use_scores = [s for s in scores if s[0] in lca_cfg.activity_names.use]
        else:
            # Subsequent passes: only use-phase activities differ across profiles.
            use_scores = _compute_lca_scores(
                activities, methods, activity_names=lca_cfg.activity_names.use
            )

        use_per_profile[profile_index] = _scores_to_array(
            use_scores, lcia_cfg, lca_cfg.activity_names.use
        )

    if manufacturing_array is None or eol_array is None:
        raise RuntimeError("Manufacturing or EoL LCA scores were not computed.")

    # Compute weighted-average use array across all profiles.
    use_weighted = _compute_use_weighted_average(use_per_profile, sim_cfg.mission_profile_probs)
    nb_ru = planned_maintenance_array.shape[1]

    return LcaResult(
        manufacturing=manufacturing_array,
        use=use_weighted,
        planned_maintenance=planned_maintenance_array,
        curative_maintenance=curative_maintenance_array,
        eol=eol_array,
        use_per_profile=use_per_profile,
        nb_ru=nb_ru,
    )
