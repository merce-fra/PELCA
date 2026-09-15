# Fan Reliability

This folder contains the cooling fan reliability evaluator. The evaluator estimates the reliability parameters of a fan replacement unit and writes PELCA-ready values into the workbook.

The model is intended for scenario comparison. Results depend on the selected mission profile, fan count, environmental factors and replacement-unit assumptions.

## Folder Contents

- `evaluate_fan_reliability.py`: main evaluator.
- `data/PELCA_Reliability_v1.0.0_Fan.xlsx`: default input/output workbook.
- `README.md`: this documentation.

## Replacement-Unit Boundary

The replacement unit is the set of fans replaced together during maintenance. The workbook defines the number of identical fans and the relevant fan parameters.

The result is expressed at replacement-unit level, not only at single-fan level.

## Model Overview

The evaluator:

1. reads fan parameters and mission profiles from Excel;
2. evaluates random failure behavior with a FIDES-based approach;
3. evaluates ageing behavior for operating conditions that drive fan wear;
4. combines the fan-level behavior into replacement-unit parameters;
5. writes Weibull parameters and replacement data back to the workbook.

## Run From Project Root

```bash
python run_reliability_evaluation.py
```

The project-level orchestrator runs this subsystem with:

```text
fan_reliability/data/PELCA_Reliability_v1.0.0_Fan.xlsx
```

## Run This Evaluator Only

```bash
python -m fan_reliability.evaluate_fan_reliability fan_reliability/data/PELCA_Reliability_v1.0.0_Fan.xlsx
```

To run on another workbook:

```bash
python -m fan_reliability.evaluate_fan_reliability path/to/your_fan_workbook.xlsx
```

## Workbook Structure

The default workbook is `data/PELCA_Reliability_v1.0.0_Fan.xlsx`.

| Sheet | Role |
| --- | --- |
| `comments` | Human-readable description of the workbook. |
| `Parameters` | Fan count, fan power and component-level inputs. |
| `options` | Plot and execution options. |
| `mission_profile` | Operating phases for each mission profile. |
| `results` | Weibull parameters written by the evaluator. |
| `Replacement` | Replacement cost and maintenance information. |

## Main Input Data

The `Parameters` sheet contains values such as:

- number of identical fans in the replacement unit;
- fan power or rating information;
- model constants used by the reliability calculation.

The `mission_profile` sheet describes operating conditions. Typical columns include:

- mission-profile identifier;
- operating-phase flag;
- ambient temperature;
- thermal cycling amplitude;
- maximum cycling temperature;
- operating hours per year;
- number of cycles;
- cycle duration or weighting;
- humidity and environment factors.

## Outputs

The `results` sheet contains PELCA-ready Weibull parameters:

- early-failure scale and shape;
- random-failure scale and shape;
- wear-out scale and shape.

The `Replacement` sheet contains maintenance and cost data for the fan replacement unit.

## Usage Notes

- Keep one row per operating phase in the mission profile.
- Use separate mission-profile identifiers when comparing different use cases.
- Check that operating hours and phase weights represent a complete yearly usage scenario.
- Treat the calculated values as comparative engineering estimates, not absolute field guarantees.
