# Capacitor Bank Reliability

This folder contains the DC-link capacitor bank reliability evaluator. The evaluator estimates random failure and wear-out behavior for a capacitor bank replacement unit, then writes PELCA-ready parameters into the workbook.

The capacitor model is sensitive to electrical load, ripple current, temperature, bank topology and lifetime assumptions. The tool is intended for consistent comparison of scenarios.

## Folder Contents

- `evaluate_capacitor_bank_reliability.py`: main evaluator.
- `data/PELCA_Reliability_v1.0.0_CapacitorBank.xlsx`: default input/output workbook.
- `calculations/`: ripple-current and electrical-stress calculations.
- `models/`: FIDES capacitor model and Weibull/bathtub helpers.
- `utils/`: Excel extraction, interpolation and mission-profile helpers.

## Replacement-Unit Boundary

The replacement unit is the capacitor bank replaced as a whole. The workbook describes the bank topology, including the number of parallel strings and the number of capacitors in series.

Reliability parameters are reported for the bank-level replacement unit.

## Model Overview

The evaluator:

1. reads capacitor, topology and mission-profile inputs from Excel;
2. estimates electrical stress and capacitor-bank losses;
3. estimates random failure with a FIDES-based model or interpolation mode;
4. estimates wear-out lifetime using capacitor lifetime relationships;
5. converts the results into Weibull parameters for PELCA;
6. writes result, thermal and replacement data back to the workbook.

## Run From Project Root

```bash
python run_reliability_evaluation.py
```

The project-level orchestrator runs this subsystem with:

```text
capacitor_bank_reliability/data/PELCA_Reliability_v1.0.0_CapacitorBank.xlsx
```

## Run This Evaluator Only

```bash
python -m capacitor_bank_reliability.evaluate_capacitor_bank_reliability capacitor_bank_reliability/data/PELCA_Reliability_v1.0.0_CapacitorBank.xlsx
```

To run on another workbook:

```bash
python -m capacitor_bank_reliability.evaluate_capacitor_bank_reliability path/to/your_cap_workbook.xlsx
```

## Workbook Structure

The default workbook is `data/PELCA_Reliability_v1.0.0_CapacitorBank.xlsx`.

| Sheet | Role |
| --- | --- |
| `comment` | Human-readable workbook description. |
| `parameters` | Electrical ratings, capacitor data, topology, cost and model constants. |
| `options` | Plot and execution options. |
| `mission_profile` | Operating phases for each mission profile. |
| `tables` | Lookup or mode-selection tables used by the model. |
| `results` | PELCA-ready reliability parameters. |
| `thermal_data` | Intermediate thermal and stress data written by the evaluator. |
| `Replacement` | Replacement cost and maintenance information. |

## Main Input Data

The `parameters` sheet contains values such as:

- nominal power and voltage data;
- capacitor-bank structure;
- capacitor electrical and thermal characteristics;
- reliability model constants;
- replacement cost and maintenance assumptions.

The `mission_profile` sheet typically contains:

- mission-profile identifier;
- operating-phase flag;
- relative speed;
- relative torque or load;
- ambient or local temperature;
- thermal cycling amplitude;
- maximum cycling temperature;
- operating hours per year;
- number of cycles;
- cycle duration or weighting;
- environment/application factors.

## Outputs

The `results` sheet contains:

- capacitor lifetime summary;
- early-failure Weibull parameters;
- random-failure Weibull parameters;
- wear-out Weibull parameters.

The `thermal_data` sheet stores intermediate values useful for review and debugging, such as calculated losses and thermal stresses per operating phase.

## Usage Notes

- Verify the capacitor-bank topology before interpreting results.
- Use consistent mission-profile definitions across subsystems when comparing complete converter scenarios.
- Review the `tables` sheet when switching between calculation modes.
- If you replace the default workbook, keep the expected sheet names and column names unless you also update the code.
