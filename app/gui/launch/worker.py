"""Qt worker thread that runs the PELCA pipeline without blocking the GUI.

Exposes ``RunnerThread``, a ``QThread`` subclass that wraps ``PelcaRunner.run()``.
Emits ``finished(dict)`` on success, ``error(str)`` on any exception, and
``progress(str)`` for log messages forwarded from the pipeline.
"""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QThread, Signal

from app.core.runner import PelcaRunner

logger = logging.getLogger(__name__)


class RunnerThread(QThread):
    """Run :class:`~app.core.runner.PelcaRunner` in a background thread.

    Signals:
        finished: Emitted on success with the pipeline result dict
            (``"plots"``, ``"env_result"``, ``"eco_result"``, ``"config"``).
        error: Emitted on failure with a human-readable error message.
        progress: Emitted with short status strings at key milestones.

    Args:
        input_path: Path to the input ``.xlsx``/``.xlsm`` file.
        run_lca: If ``True``, run the brightway2 LCA; otherwise load an
            existing ``LCA output.xlsx``.
    """

    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, input_path: str, run_lca: bool = False) -> None:
        super().__init__()
        self._input_path = input_path
        self._run_lca = run_lca

    def run(self) -> None:
        """Execute the pipeline and emit results or an error."""
        try:
            self.progress.emit("Starting pipeline…")
            result: dict[str, Any] = PelcaRunner(self._input_path, run_lca=self._run_lca).run()
            logger.info("Pipeline completed: %d figures produced", len(result.get("plots", [])))
            self.finished.emit(result)
        except FileNotFoundError as exc:
            logger.error("Input file not found: %s", exc)
            self.error.emit(f"File not found: {exc}")
        except ValueError as exc:
            logger.error("Invalid input data: %s", exc)
            self.error.emit(f"Invalid input: {exc}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected pipeline error: %s", exc)
            self.error.emit(f"Unexpected error: {exc}")
