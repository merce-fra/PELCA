# PELCA – Test Coverage Detail

All tests are in `app/tests/`. Run with:

```bash
python -m pytest app/tests/ -v
```

---

## `app/tests/fixtures.py`

Builds a `PelcaConfig` entirely in Python — no Excel file required.

Shared constants: `NB_RU = 2`, `NB_EI = 3`, `SERVICE_LIFE = 5`, `TIME_STEP = 1`, `MC_ITERATIONS = 10`, `NB_PROFILES = 1`.

Factory functions: `make_failure_config()`, `make_maintenance_config()`, `make_cost_config()`, `make_simulation_config()`, `make_config()`.

---

## `app/tests/test_reader.py`

Tests `ExcelInputReader.from_excel()` against the real sample file
`PELCA datasets/PowerModuleAndCapacitor/PELCA_v2.0.0_PowerModuleAndCapacitor.xlsx`,
plus unit tests for `_parse_profile_values` and in-memory multi-profile integration tests
that require no Excel file.

| Test | What it checks |
|---|---|
| `test_read_valid_returns_pelca_config` | Full read returns a `PelcaConfig` |
| `test_read_valid_lcia_names_non_empty` | `lcia.names` is populated |
| `test_read_valid_service_life_positive` | `simulation.service_life > 0` |
| `test_read_valid_failure_config_shapes_match` | Weibull arrays have shape `(nb_ru, nb_profiles)` |
| `test_read_valid_cost_shape_matches_faults` | Cost arrays length matches nb_ru |
| `test_read_valid_selected_ei_name_in_lcia_names` | `selected_ei_name` is in `lcia.names` |
| `test_read_valid_mission_profile_probs_sum` | Profile probabilities sum to `1.0` |
| `test_read_valid_energy_amounts_non_empty` | `energy_amounts` dict is not empty |
| `test_read_missing_file_raises_file_not_found` | `FileNotFoundError` on missing path |
| `test_read_valid_roundtrip_lca_config_project_name` | `lca.project_name` is a non-empty string |
| `test_exceed_max_annual_usage_time` | `ValueError` when `hours_per_year > 8784` |
| `test_parse_profile_values_nan_returns_zeros` | Empty (NaN) cell → `[0.0, …]` for every profile |
| `test_parse_profile_values_scalar_repeated` | Scalar cell value is broadcast to all profiles |
| `test_parse_profile_values_hash_separated_exact` | `"20#30"` with 2 profiles → `[20.0, 30.0]` |
| `test_parse_profile_values_fewer_values_pad_last` | Fewer `#`-separated values than profiles → last value repeated |
| `test_parse_profile_values_comma_decimal` | Comma decimal separator is accepted |
| `test_parse_profile_values_numeric_input` | Integer input is handled like a string scalar |
| `test_from_sheets_data_two_profiles_nb_mission_profiles` | `"80#20"` in `Mission profile (%)` → `nb_mission_profiles == 2` |
| `test_from_sheets_data_two_profiles_probs_sum` | Profile probabilities sum to `1.0` with 2 profiles |
| `test_from_sheets_data_two_profiles_weibull_shape` | Weibull arrays have shape `(nb_ru, 2)` with 2 profiles |
| `test_from_sheets_data_two_profiles_scalar_faults_expanded` | Scalar Weibull cell is expanded to all profiles |
| `test_fault_mode_mask_disables_when_both_parameters_absent` | Both sigma and beta absent → mode silently disabled |
| `test_fault_mode_mask_raises_when_only_sigma_present` | sigma set, beta missing → `ValueError` |
| `test_fault_mode_mask_raises_when_only_beta_present` | beta set, sigma missing → `ValueError` |
| `test_mission_profile_not_summing_to_100_raises` | Mission profile percentages ≠ 100 % → `ValueError` |

---

## `app/tests/test_lca.py`

Requires a real brightway database and a local copy of the sample Excel file.
Marked `@pytest.mark.slow` — **excluded from the default test run**.
Run explicitly with:

```bash
python -m pytest app/tests/test_lca.py -m slow
```

| Test | What it checks |
|---|---|
| `test_lca_generator_runs_without_error` | `lca_generator()` completes and returns a `LcaResult` with non-empty arrays |

---

## `app/tests/test_lca_io.py`

| Test | What it checks |
|---|---|
| `test_export_and_read_roundtrip_single_profile` | `export_lca_result` → `read_lca_output` returns equal arrays (single profile) |
| `test_export_and_read_roundtrip_multi_profile` | Same for a multi-profile `LcaResult` |
| `test_read_missing_sheets_raises` | `ValueError` when a required sheet is absent from `LCA output.xlsx` |

---

## `app/tests/test_simulation.py`

Synthetic data only — no Excel file required.

| Test | What it checks |
|---|---|
| `test_simulation_output_shapes` | All result array shapes match `(usage_time, MC_ITERATIONS, …)` |
| `test_env_total_is_nondecreasing` | `env.total` never decreases along the time axis |
| `test_eco_fields_are_non_negative` | All `EconomicResult` cost arrays contain only non-negative values |

---

## `app/tests/test_export.py`

Synthetic data only.

| Test | What it checks |
|---|---|
| `test_unique_path_returns_base_when_free` | `_unique_path` returns base name when no collision |
| `test_unique_path_increments_on_collision` | Appends `_1`, `_2`, … on successive collisions |
| `test_export_numpy_roundtrip` | `export_numpy` writes a `.npy` file loadable with `np.load` |
| `test_export_excel_2d_array` | `export_excel` writes a valid `.xlsx` with correct shape |
| `test_export_excel_flattens_3d_array` | 3-D arrays are flattened to 2-D before writing |
| `test_export_config_creates_csv_and_pkl` | `export_config` produces both `dict_file.csv` and `dict_file.pkl` |
| `test_export_config_pickle_roundtrip` | Pickled config survives a load/reload cycle |
| `test_export_lcic_summary_creates_file` | `export_lcic_summary` creates `LCIC output.xlsx` |
| `test_export_lcic_summary_columns` | Output sheet contains the expected column headers |
| `test_export_lcic_summary_row_count` | One row per LCIA method plus one ECO row |
| `test_export_lcic_summary_eco_row` | ECO row label and cost values are correct |

---

## `app/tests/test_plots.py`

Synthetic data only.

| Test | What it checks |
|---|---|
| `test_run_returns_correct_count` | `PlotBuilder.run()` returns 11 figures |
| `test_run_returns_expected_titles` | Figure titles match the expected list in order |
| `test_run_each_entry_has_required_keys` | Every entry has `"title"` and `"plot"` keys |
| `test_all_figures_are_plotly_figures` | Every `"plot"` value is a `go.Figure` |
| `test_all_figures_have_at_least_one_trace` | No figure is empty |
| `test_cdf_values_are_in_unit_interval` | CDF trace values are in `[0, 1]` |

---

## `app/tests/test_main.py`

| Test | What it checks |
|---|---|
| `test_main_window_initialization` | Window title, geometry, and initial state flags |
| `test_main_window_ui_setup` | Central widget, header, and run panel are instantiated |
