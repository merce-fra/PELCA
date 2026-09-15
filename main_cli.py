#!/usr/bin/env python3
"""PELCA CLI — headless runner.

Run a full PELCA analysis (LCA + LCIC) or lcic-only from the
terminal and export figures and numpy arrays.

Main entry point: ``main()``.

Usage:
    python main_cli.py -i "PELCA datasets/E-Fuse/PELCA_v2.0.0_Efuse.xlsm"
    python main_cli.py -i mydata.xlsx --lcic-only
    python main_cli.py -i mydata.xlsx -v

Exit codes:
    0  success
    2  invalid arguments or missing input file
    3  runtime error raised by the pipeline
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from app.core.runner import PelcaRunner
from app.core.simulation import EnvironmentalResult
from app.io.export import export_html, export_numpy, export_png, export_svg

logger = logging.getLogger(__name__)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    if not argv:
        argv = ["--help"]
    p = argparse.ArgumentParser(
        description=(
            "Run PELCA headlessly (no GUI). Default: full LCA + LCIC. "
            "Use --lcic-only to skip LCA when LCA outputs already exist."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "-i",
        "--input",
        required=True,
        type=Path,
        help="Input Excel path (.xlsx/.xlsm).",
    )
    p.add_argument(
        "-t",
        "--lcic-only",
        action="store_true",
        help="Run only the LCIC phase (skip LCA).",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose logging output.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI pipeline and return an exit code.

    Args:
        argv: Argument list. Defaults to ``sys.argv[1:]``.

    Returns:
        0 on success, 2 for bad arguments or missing file, 3 for pipeline errors.
    """
    args = _parse_args(list(argv) if argv is not None else sys.argv[1:])

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s — %(message)s",
    )
    # Silence peewee (brightway2 ORM) and other chatty third-party loggers.
    logging.getLogger("peewee").setLevel(logging.WARNING)
    logging.getLogger("bw2data").setLevel(logging.WARNING)
    logging.getLogger("bw2calc").setLevel(logging.WARNING)

    input_path: Path = args.input.expanduser().resolve()
    if not input_path.exists():
        logger.error("File not found: %s", input_path)
        return 2

    run_lca = not args.lcic_only
    logger.info("Mode: %s", "full LCA + LCIC" if run_lca else "LCIC only")

    try:
        result = PelcaRunner(str(input_path), run_lca=run_lca).run()
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        return 3

    plots: list[dict] = result["plots"]
    env_result: EnvironmentalResult = result["env_result"]
    config = result["config"]

    plot_dir = config.output.plot_dir
    numpy_dir = config.output.numpy_dir

    logger.info("Exporting %d figures to %s", len(plots), plot_dir)
    for entry in plots:
        fig = entry["plot"]
        title = entry["title"]
        try:
            export_html(fig, title, plot_dir)
            export_png(fig, title, plot_dir)
            export_svg(fig, title, plot_dir)
        except Exception as exc:
            logger.warning("Failed to export figure %r: %s", title, exc)

    logger.info("Exporting numpy arrays to %s", numpy_dir)
    export_numpy("Impact_total", env_result.total, numpy_dir)
    export_numpy("Impact_manu", env_result.manufacturing, numpy_dir)
    export_numpy("Impact_use", env_result.use, numpy_dir)
    export_numpy("fault_cause", env_result.fault_cause, numpy_dir)
    export_numpy("RU_age", env_result.ru_age, numpy_dir)

    logger.info("Done. Results in %s", config.output.lca_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
