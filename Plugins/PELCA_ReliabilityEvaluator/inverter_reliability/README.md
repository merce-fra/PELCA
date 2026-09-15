# Inverter Reliability

This folder contains the inverter power-module reliability evaluator. The evaluator estimates reliability parameters for the inverter replacement unit from electrical loading, thermal stress, random failure models and ageing models.

The model is designed for comparative reliability studies. It should be used with care when changing semiconductor technology, topology or cooling assumptions.

## Folder Contents

- `evaluate_inverter_reliability.py`: main evaluator.
- `data/PELCA_Reliability_v1.0.0_Inverter.xlsx`: default input/output workbook.
- `thermal_results.xlsx`: workbook used for thermal calculation review.
- `igbt_reliability/`: supporting package for operating-point calculations, losses, thermal simulation, device models, ageing and result writing.

## Replacement-Unit Boundary

The replacement unit is the inverter power-module set replaced together during maintenance. The evaluator reports reliability parameters at this aggregate replacement-unit level.

Subsystem-specific constants such as parallel module count and device parameters are provided through the workbook and supporting code.

## Model Overview

The evaluator:

1. reads electrical, thermal and mission-profile inputs from Excel;
2. converts each mission-profile phase into inverter operating points;
3. estimates conduction and switching losses;
4. estimates junction-temperature stress with thermal models;
5. calculates random failure rates with a FIDES-based approach;
6. estimates wear-out from thermal cycling and ageing models;
7. converts the results into PELCA Weibull parameters;
8. writes result and thermal data back to the workbook.

## Run From Project Root

```bash
python run_reliability_evaluation.py
```

The project-level orchestrator runs this subsystem with:

```text
inverter_reliability/data/PELCA_Reliability_v1.0.0_Inverter.xlsx
```

## Run This Evaluator Only

```bash
python -m inverter_reliability.evaluate_inverter_reliability inverter_reliability/data/PELCA_Reliability_v1.0.0_Inverter.xlsx
```

To run on another workbook:

```bash
python -m inverter_reliability.evaluate_inverter_reliability path/to/your_inv_workbook.xlsx
```

## Workbook Structure

The default workbook is `data/PELCA_Reliability_v1.0.0_Inverter.xlsx`.

| Sheet | Role |
| --- | --- |
| `comment` | Human-readable workbook description. |
| `parameters` | Electrical ratings, thermal settings, topology parameters and model constants. |
| `options` | Plot, debug and calculation options. |
| `mission_profile` | Operating phases for each mission profile. |
| `Replacement` | Replacement cost and maintenance information. |
| `thermal_data` | Intermediate thermal and stress results written by the evaluator. |
| `comparison_pwm_iec` | Optional comparison between calculation approaches. |
| `results` | PELCA-ready reliability parameters. |

## Main Input Data

The `parameters` sheet contains values such as:

- rated apparent and active power;
- input and output electrical ratings;
- topology parameters;
- thermal model parameters;
- reliability model factors;
- replacement-unit cost and maintenance assumptions.

The `mission_profile` sheet typically contains:

- mission-profile identifier;
- operating-phase flag;
- relative speed;
- relative torque;
- ambient or local temperature;
- thermal cycling amplitude;
- maximum cycling temperature;
- operating hours per year;
- number of cycles;
- cycle duration or weighting;
- humidity and vibration factors when used.

## Outputs

The `results` sheet contains:

- limiting device lifetime summary;
- early-failure Weibull parameters;
- random-failure Weibull parameters;
- wear-out Weibull parameters.

The `thermal_data` sheet contains intermediate results that help review losses, temperatures and stress assumptions for each operating phase.

## Internal Package Structure

`igbt_reliability/` contains the lower-level implementation:

- `calculations/`: operating-point, loss and junction-temperature calculations.
- `components/`: semiconductor device abstractions and parameter functions.
- `converter/`: converter-level helper classes.
- `lifetime/`: ageing and thermal-cycling lifetime models.
- `thermal/`: transient and steady thermal simulation helpers.
- `utils/`: plotting, mission-profile extraction and result writing.

## Usage Notes

- Keep mission-profile units consistent across all phases.
- Review thermal assumptions before comparing designs with different cooling concepts.
- Random failure and wear-out are separate mechanisms; both should be reviewed when interpreting the final Weibull parameters.
- The aggregate replacement-unit result may be more relevant for PELCA than the lifetime of an individual device.
