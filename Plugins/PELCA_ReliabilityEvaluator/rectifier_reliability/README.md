# Rectifier Reliability

This folder contains the rectifier reliability evaluator. The evaluator estimates random failure and wear-out parameters for a rectifier replacement unit and writes PELCA-ready values into the workbook.

The model focuses on the rectifier diode stage and its thermal stress under the provided mission profiles.

## Folder Contents

- `evaluate_rectifier_reliability.py`: main evaluator.
- `data/PELCA_Reliability_v1.0.0_Rectifier.xlsx`: default input/output workbook.
- `README.md`: this documentation.

## Replacement-Unit Boundary

The replacement unit is the rectifier stage replaced together during maintenance. The workbook defines topology parameters such as the number of parallel devices used by the calculation.

The result is expressed at replacement-unit level.

## Model Overview

The evaluator:

1. reads rectifier, topology and mission-profile inputs from Excel;
2. derives electrical operating points from the mission profile;
3. estimates diode conduction losses;
4. converts losses into thermal stress using thermal response models;
5. evaluates random failure with a FIDES-based model;
6. evaluates wear-out with an ageing model;
7. converts results into Weibull parameters for PELCA;
8. writes result and thermal data back to the workbook.

## Run From Project Root

```bash
python run_reliability_evaluation.py
```

The project-level orchestrator runs this subsystem with:

```text
rectifier_reliability/data/PELCA_Reliability_v1.0.0_Rectifier.xlsx
```

## Run This Evaluator Only

```bash
python -m rectifier_reliability.evaluate_rectifier_reliability rectifier_reliability/data/PELCA_Reliability_v1.0.0_Rectifier.xlsx
```

To run on another workbook:

```bash
python -m rectifier_reliability.evaluate_rectifier_reliability path/to/your_rect_workbook.xlsx
```

## Workbook Structure

The default workbook is `data/PELCA_Reliability_v1.0.0_Rectifier.xlsx`.

| Sheet | Role |
| --- | --- |
| `comments` | Human-readable workbook description. |
| `Parameters` | Rectifier topology, process factors and model constants. |
| `options` | Plot and execution options. |
| `Inputs` | Mission-profile operating phases. |
| `Feuil1` | Intermediate operating-point data. |
| `Analysis_Results` | PELCA-ready reliability parameters. |
| `Replacement` | Replacement cost and maintenance information. |
| `thermal_data` | Intermediate thermal and stress results. |

## Main Input Data

The `Parameters` sheet contains values such as:

- number of parallel rectifier paths;
- process and reliability factors;
- thermal-model constants;
- ageing-model constants.

The `Inputs` sheet typically contains:

- mission-profile identifier;
- operating-phase flag;
- relative speed;
- relative torque;
- applied voltage;
- local board or ambient temperature;
- thermal cycling amplitude;
- maximum cycling temperature;
- operating hours per year;
- number of cycles;
- cycle duration or weighting;
- humidity factor.

## Outputs

The `Analysis_Results` sheet contains:

- random-failure Weibull parameters;
- wear-out Weibull parameters.

The `thermal_data` sheet stores intermediate electrical and thermal stress calculations for review.

## Usage Notes

- Check the topology parameters before comparing designs.
- The loss model uses simplifying assumptions suitable for thermal-stress estimation.
- The rectifier evaluator reuses inverter operating-point helpers where appropriate.
- Use the same mission-profile philosophy as the other subsystems when preparing a complete PELCA scenario.
