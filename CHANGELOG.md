# Changelog

# Update notes regarding PELCA 2.0

The version 2.0 of the PELCA software includes the following new features compared to the version 1.4 :

- Ability to handle multiple mission profiles, with associated levels of energy consumption, Weibull fault rates, and planned maintenance calendars ;
- Macro-enabled .xlsm input workbooks to manage mission profiles, with updated E-Fuse and Power Module and Capacitor example datasets ;
- Addition of planned maintenance, curative maintenance and end-of-life inventories for a finer modeling of the service life of a system ;
- Split of the Planned Maintenance operations in Preventive Maintenance and Modernization and addition of a downtime indicator to assess the effects of maintenance and parts replacement on a system's availability ;
- Rename 'Staircase' curves into 'Life Cycle Impact Curves' (LCICs), add graphs for planned and unplanned maintenance, end-of-life, and downtime, and improve LCA and LCIC output results Excel files ;
- Addition of PELCA Reliability Evaluator v1.0.0 to estimate fault parameters for fans, capacitor banks, inverter power modules and rectifiers ([PELCA Reliability Evaluator v1.0.0](./Plugins/PELCA_ReliabilityEvaluator/README.md)) ;
- Rename PELCA Device Designer to PELCA Manufacturing Evaluator v1.0.0, providing manufacturing impact assessments for power electronic semiconductors (see [PELCA Manufacturing Evaluator v1.0.0](./Plugins/PELCA_ManufacturingEvaluator/PELCAManufacturingEvaluator_Instructions.md)) ;
- Addition of a headless CLI alongside the GUI, reorganize the application into computation, file I/O and GUI layers, and strengthen input validation, automated tests and user documentation.

Please refer to [PELCA Instructions](documentations/PELCA_Instructions.md) and [Algorithm](documentations/Algorithm.md) for more details on PELCA 2.0.

---

All notable changes since commit `cd6d848` (2026-05-07).

---

## [v2.0.0a6] – 2026-07-08 → 2026-07-10

### Features

- **Downtime configuration** – Added modernization downtime configuration support in the Downtime sheet.
                             - Check for consistency between the configuration, the Faults sheet, and downtime
- **Inventory sheet validation** – An error is now raised when duplicate activity names are detected in inventory sheets.
- **PELCADeviceDesigner plugin** – Impact sorting now follows the same order as PELCA outputs.

### Bug Fixes

- **Curative faults handling** – Fixed the global flag used for curative faults.

### Refactoring

- **CDF plot styling** – Updated CDF plotting to use non-equal linestyles for improved readability.
- **CDF wording** – Updated replacement-unit naming in the Cumulative Distribution Function graph.
- **Code cleanup** – Cleaned remaining TODO markers in the code.

### Tests

- **Plot tests** – Fixed failing unit tests for plots.

### Documentation

- **Plugin and docs maintenance** – Applied small adjustments in documentation and the PELCADeviceDesigner plugin.

### Environment / Tooling

- **CI pipeline** – Fixed the GitHub CI workflow.

### Data

- **E-Fuse dataset** – Updated `PELCA_v2.0.0_Efuse.xlsm`.

## [v2.0.0a5] – 2026-07-08

### Bug Fixes

- **PELCADeviceDesigner plugin** – Simplified `requirements.txt` to top-level dependencies only (removed frozen transitive packages and unused `stats_arrays` import).

### Documentation

- **`PELCADeviceDesigner_Instructions.md`** – Updated image links to reflect the current file paths.

---

## [v2.0.0a4] – 2026-07-03 → 2026-07-07

### Bug Fixes

- **Mission profiles input robustness** – Reader no longer fails on malformed or incomplete mission profile data in the Excel input file.
- **Weibull CDF per profile** – Weibull CDF is now computed per mission profile instead of using weighted averages of parameters across profiles.
- **Fault tab validation** – An exception is now raised when only one of the two required parameters for a failure mode is provided (instead of silently continuing).
- **Planned Maint. tab validation** – Unspecified maintenance activities now default to `0.0` before processing; `0`-valued activities are handled consistently with the specification.
- **Mission profile percentages** – Added a check that the sum of mission profile percentages equals 100 %.
- **RU count consistency** – Added a cross-tab check that the number of replacement units is consistent across all relevant input sheets.

### Refactoring

- **`simulation.py` naming** – Variable and function names harmonised throughout the module for consistency with the rest of the codebase.

### Documentation

- Completed and updated the various `.md` documentation files.

---

## [v2.0.0a3] – 2026-06-22 → 2026-07-06

### Features

- **Downtime per RU** – Downtime is now computed per replacement unit; its impact is included in the planned and curative maintenance export sheets. Export and plot of planned maintenance can be skipped when the corresponding flag is set to `False`.
- **Modernization** – `planned_maintenance` split into `preventive` and `modernization` sub-categories; modernization activities are now read from the input Excel file, computed in the simulation, and exported separately.
- **Custom failure mode** – Added support for a user-defined failure mode alongside the built-in Weibull model; reader, config, simulation, and tests updated accordingly.
- **Selectable traced environmental impact** – The user can now choose a specific environmental indicator from a list to trace individually in the output plots and exports.
- **ECO terminology in plots** – Plot axis and legend labels renamed from "Cost/Price" to "ECO" for consistency with the rest of the pipeline.
- **End-of-life unlabelled tray** – An unlabelled end-of-life bar segment is now appended to the relevant stacked-bar figures.

### Bug Fixes

- **Empty cells in Faults sheet** – Reader no longer raises an error when the Faults input sheet contains empty cells.
- **`cost_use_per_ru` allocation** – Fixed division by `nb_ru` instead of `nb_act_use` in `simulation.py`.

### Refactoring

- **Code simplification** – Reduced redundancy in `simulation.py` and `config.py` across two passes; logic for preventive and modernization maintenance handled as distinct activities throughout the pipeline.
- **`ei` variable naming** – Environmental impact loop variable renamed from `EI` to `ei` in `simulation.py` for PEP 8 compliance.
- **Entry points renamed** – `pelca_cli.py` → `main_cli.py`; `pelca_gui.py` → `main_gui.py`.

### Tests

- Unified fixture construction in `fixtures.py` (single canonical way to build config and result objects).
- Fixed and improved unit tests across `test_reader.py` and others following the new reader features.

---

## [v2.0.0a2] – 2026-06-12 → 2026-06-17

### Features

- **Downtime sheet** – Added a downtime sheet in the input Excel file; downtime data is now read and propagated through the pipeline.
- **Downtime plot** – New Downtime figure added to the results output.
- **DWT impact on all-impacts figure** – Downtime impact is now included in the all-impacts figure and in the LCIC output.
- **LCIC output split by lifecycle stage** – Five new sheets added to `LCIC output.xlsx`, one per lifecycle stage with activity splitting.
- **Cost terminology** – `raw_cost` and `eol_cost` renamed for consistency.
- **CLI default to help** – `main_cli.py` now displays the help message when called without arguments (equivalent to `--help`).
- **Splash screen improvements** – Opaque background added to the splash screen, logo resized to half its original size, and "Please wait" message made more prominent (larger bold font, highlighted colour).

### Refactoring

- **Image folder renamed** – `documentations/images/Design/` renamed to `documentations/images/Architecture/`; PlantUML diagrams updated accordingly.
- **Requirements files unified** – `requirements.txt` and `requirements_dev.txt` overhauled and unified for consistency.

### Tests

- Fixed failing unit tests introduced by the downtime and LCIC-output changes.

---

## [v2.0.0a1] – 2026-05-27 → 2026-06-11

### Features

- **Maintenance impact modelling** – Added planned/curative maintenance sheets in the input Excel file; environmental and economic impacts of maintenance are now computed and included in the LCA pipeline.
- **Simulation results split by activity/RU** – Simulation results are now broken down per activity and replacement unit, with dedicated plots.
- **Eco dataclass** – Improved `Eco` dataclass and its computation logic for better maintainability.
- **LCA generator** – Added `lca_generator` module with associated unit tests.
- **Activity names in `LcaConfig`** – Activity names are now stored in `LcaConfig` and exposed through `lca_io`.
- **Splash screen** – A splash screen is displayed while the GUI is loading.
- **Last-used file memory** – The GUI now remembers the last opened input file across sessions.
- **New simulation engine and plot builder** – Added `simulation_engine` package and `PlotBuilder` class as the new computation back-end.
- **`PelcaRunner` orchestrator** – Introduced a Qt-free `PelcaRunner` orchestrator to drive the full pipeline independently of the GUI.

### Bug Fixes

- Replaced built-in `sum()` with `numpy.sum()` in `lca_generator.py` to avoid type-mismatch issues.
- Fixed Qt object method overrides being silently replaced by custom attributes.
- Fixed stack-trace display in the GUI console.
- Fixed auto-adjust column-width function for Excel exports.
- Various corrections addressing PyLance static-analysis warnings.
- Fixed code organisation so that `dev_run.py` and `runner.py` were runnable.
- Updated input Excel file so that a complete analysis can be executed end-to-end.

### Refactoring

- **Package restructuring** – All Qt-dependent code moved into the `app/gui/` package; GUI sub-package reorganised in three steps; `utils` package removed.
- **Module renaming** – `core.simulation_engine` → `core.simulation`; entry points renamed to `pelca_cli.py` / `pelca_gui.py`; package and module names simplified throughout.
- **CLI refactored** – `main_cli.py` now uses `PelcaRunner`; `dev_run.py` removed (logic merged into CLI with additional export options).
- **Exports** – Export logic moved to a dedicated module; archiving of previous exports reintroduced; configuration files (`dict_file.csv`, `dict_file.pkl`) re-added to exports; `export_lca_result` cleaned up.
- **Qt back-end** – Replaced deprecated `backend_qt5agg` with `backend_qtagg` in `plots.py`.
- **GUI clean-up** – Comments, PyLance warnings, and minor style issues addressed across `app/gui/` and `app/io/plots`.
- **Simulation type removed** – Obsolete "Type de simulation" parameter removed from the LCA input tab and from the reader.
- **Relative paths** – Paths in the PowerModule example made relative.

### Terminology / Wording

- **"staircase" → "LCIC"** – All variable names, file names, and UI labels renamed from "staircase" to "LCIC".
- **"Type de simulation" removed** – References to the removed simulation-type parameter cleaned up from labels and comments.

### Tests

- New tests added to improve code coverage across the core and I/O layers.

### Documentation

- `Architecture.md` updated and simplified.
- Architecture and pipeline diagrams moved to `documentations/images/Design/` and regenerated as PNG.
- Comments in `app/core/` modules updated.
- Copilot instructions updated to reflect structural changes.

### Environment / Tooling

- Pre-commit hooks added to prevent formatting errors before commits.
- Excel relative paths updated in the PowerModule dataset example.
