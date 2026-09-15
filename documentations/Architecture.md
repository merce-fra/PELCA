# PELCA – Architecture

## Overview

PELCA has a layered architecture with a clean separation between domain computation, file I/O,
and the Qt GUI. This enables a zero-Qt CLI (`main_cli.py`), unit-testable business logic,
and a single Excel parse per simulation run.

![Data flow](images/Architecture/PELCA%20-%20Data%20Flow.png)

Fig. 1: PELCA pipeline data flow

The pipeline is orchestrated by `PelcaRunner` (`app/core/runner.py`): it reads the input
Excel file, runs or loads the LCA, runs the Monte Carlo simulation, builds the figures, and
exports results. The GUI wraps this in a background `QThread`; the CLI calls it directly.

---

## Folder structure

![Folder structure](images/Architecture/PELCA%20-%20Folder%20Structure.png)

Fig. 2: Folder structure of the PELCA software

**Import rule:**

```
core/   may import io/ (for orchestration); never gui/
io/     may import core/ (for types); never gui/
gui/    may import core/ and io/; never the reverse
```

---

## Module specifications

### `app/core/config.py`

All types are `@dataclass`. `PelcaConfig` is the top-level configuration object, composed
of `LcaConfig`, `LciaConfig`, `SimulationConfig` (which nests `FailureConfig`,
`MaintenanceConfig`, `CostConfig`), and `OutputConfig`. Treated as immutable after
construction — only `ExcelInputReader` sets attributes.

### `app/core/lca.py`

Defines `LcaResult` (manufacturing, use, and end-of-life impact arrays) and
`lca_generator()`, which runs the brightway2 computation against ecoinvent for all mission
profiles. No file I/O — the caller decides whether to persist the result.

### `app/core/simulation.py`

Defines `EnvironmentalResult` and `EconomicResult` (time-series arrays over the service
life with Monte Carlo sampling), and `run_simulation()` which produces both from a
`LcaResult` and `PelcaConfig`.

### `app/core/runner.py`

`PelcaRunner` is the pipeline orchestrator. `run()` chains:
`ExcelInputReader.from_excel()` → LCA (generate or load) → `run_simulation()` →
exports → `PlotBuilder.run()`. Returns a dict with `plots`, `env_result`, `eco_result`,
`config`. No Qt — shared by CLI and GUI.

### `app/io/reader.py`

`ExcelInputReader.from_excel()` opens the input file once with `pd.ExcelFile`, parses all
sheets in sequence, runs cross-sheet validation, and returns a `PelcaConfig`.
`validate_lca_inventory()` is a separate method called only when `run_lca=True`; it
verifies brightway2 inventory sheet activity names against `energy_amounts`.

### `app/io/lca_io.py`

Two functions operating on `LCA output.xlsx`: `read_lca_output()` (used when skipping LCA
recomputation) and `export_lca_result()` (called after `lca_generator()`).

### `app/io/plots.py`

`PlotBuilder.run()` takes the simulation results and returns a list of Plotly figures
(with titles), one per analysis type (environmental staircase, CDF, cost breakdown, etc.).

### `app/io/export.py`

Stateless functions for all file output: `export_html/png/svg/numpy/excel`,
`export_lcic_summary()` (Excel summary of all LCIA methods and cost stages), and
`export_config()` (CSV + pickle of the full config).

### `app/gui/main.py` and `app/gui/header.py`

`MainWindow` is the top-level Qt window. `HeaderWidget` is the shared banner image widget
used by both `MainWindow` and `ControlsWidget`.

### `app/gui/launch/`

`RunnerThread` (`worker.py`) wraps `PelcaRunner` in a `QThread`, emitting `finished(dict)`,
`error(str)`, and `progress(str)` signals. `RunPanel` (`run_panel.py`) provides the file
selection row, run-mode buttons, and live console; `EmittingStream` redirects
`sys.stdout`/`sys.stderr` to the console via a Qt signal, handling `\r`-based progress bars.

### `app/gui/results/`

`PlotWindow` (`window.py`) displays results in a two-panel layout: `ImageButtonsWidget`
(thumbnail navigation) and `PlotWidget` (stacked figures), with navigation state coordinated
by `IndexSwitcher`. `ControlsWidget` (`controls.py`) provides save/export buttons that
delegate to `app.io.export`.

---

## Test coverage

The test suite is in `app/tests/`. See [Tests.md](Tests.md) for the full list of test cases.

| Module | Scope |
|---|---|
| `fixtures.py` | Factory functions to build `PelcaConfig` and related objects in pure Python — no Excel required |
| `test_reader.py` | `ExcelInputReader.from_excel()` against the real sample file; unit tests for `_parse_profile_values`; in-memory multi-profile integration tests via `from_sheets_data` |
| `test_lca.py` | `lca_generator()` end-to-end with brightway2 |
| `test_lca_io.py` | `export_lca_result()` / `read_lca_output()` roundtrip, single and multi-profile |
| `test_simulation.py` | `run_simulation()` output shapes, monotonicity, result keys — synthetic data |
| `test_export.py` | All `export_*` functions — file creation, format, roundtrip — synthetic data |
| `test_plots.py` | `PlotBuilder.run()` figure count, titles, structure, CDF validity — synthetic data |
| `test_main.py` | `MainWindow` initialization and UI structure |

---

## Verification checklist

1. `python -m pytest app/tests/` — all tests pass.
2. `python main_cli.py -i "PELCA datasets/E-Fuse/PELCA_v2.0.0_Efuse.xlsm" -v` — runs without PySide6 installed.
3. `python main_gui.py` — GUI launches and a full run completes without error.
4. `python -c "from app.core.runner import PelcaRunner"` — no PySide6 import triggered.
5. Second run with `run_lca=False` reads `LCA output.xlsx` produced by run 1 without error.
