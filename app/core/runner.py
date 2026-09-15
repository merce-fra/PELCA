"""Pipeline orchestrator: runs a full PELCA computation.

Exposes ``PelcaRunner``, which chains all pipeline steps in sequence:
Excel parsing, LCA (computed or loaded), LCIC simulation, export of summary
files and configuration, and Plotly figure generation.

``PelcaRunner`` can be called from the CLI, a test, or wrapped in a ``QThread`` for the GUI.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.core.config import PelcaConfig
from app.core.lca import LcaResult, lca_generator
from app.core.simulation import run_simulation
from app.io.export import export_config, export_lcic_summary
from app.io.lca_io import export_lca_result, read_lca_output
from app.io.plots import PlotBuilder
from app.io.reader import ExcelInputReader

logger = logging.getLogger(__name__)


class PelcaRunner:
    """Orchestrates a full PELCA computation pipeline.

    Reads the input Excel, optionally runs the brightway2 LCA, then runs the
    Staircase simulation and produces the figures. Pure Python — no Qt, no
    signals — so it can be called from a CLI, a test, or wrapped in a Qt
    worker for the GUI.

    Args:
        input_path: Path to the input ``.xlsx``/``.xlsm`` file.
        run_lca: If ``True``, run the brightway2 LCA before the simulation.
            If ``False``, the LCA output Excel must already exist.
    """

    def __init__(self, input_path: str, run_lca: bool = False) -> None:
        self.input_path: str = input_path
        self.run_lca: bool = run_lca

    def run(self) -> dict[str, Any]:
        """Execute the pipeline and return results.

        Returns:
            A dict with the following keys:

            - ``plots``: list of ``{"title": str, "plot": Figure}`` dicts.
            - ``env_result``: :class:`~app.core.simulation.EnvironmentalResult`.
            - ``eco_result``: :class:`~app.core.simulation.EconomicResult`.
            - ``config``: :class:`~app.core.config.PelcaConfig`.
        """
        logger.info("Processing file: %s", self.input_path)

        # -- Read config from Excel -------------------------------------------
        pelca_config: PelcaConfig = ExcelInputReader.from_excel(path=Path(self.input_path))

        # -- Run or load LCA --------------------------------------------------
        lca_result: LcaResult
        if self.run_lca:
            lca_result = lca_generator(Path(self.input_path), pelca_config)
            # Persist LCA results so a subsequent --lcic-only run can load them
            export_lca_result(lca_result, pelca_config)
        else:
            lca_result = read_lca_output(
                path=Path(pelca_config.output.lca_file),
                config=pelca_config,
            )

        # -- Run LCIC simulation -----------------------------------------
        simulation_result = run_simulation(lca_result, pelca_config)
        export_lcic_summary(simulation_result, lca_result, pelca_config)
        export_config(pelca_config, pelca_config.output.lca_dir)

        # -- Build Plotly figures ---------------------------------------------
        plot_builder = PlotBuilder(pelca_config, lca_result, simulation_result)
        figs = plot_builder.run(show=False)

        return {
            "plots": figs,
            "env_result": simulation_result.environmental,
            "eco_result": simulation_result.economic,
            "config": pelca_config,
        }
