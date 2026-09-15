# PELCA Reliability Evaluator

**Current version: v1.0.0**

PELCA Reliability Evaluator is a Python toolkit that estimates reliability parameters for the main replaceable units of a power converter. The generated parameters are intended to feed a PELCA life-cycle analysis workflow, where maintenance strategies, replacement events, downtime and cost impact can be compared.

The version number is defined once in `common/__init__.py` (`__version__`) and is embedded in the default data-workbook file names, e.g. `PELCA_Reliability_v1.0.0_Fan.xlsx`, following the same convention as the other PELCA tools (`PELCA_v2.0.0_PowerModuleAndCapacitor.xlsx`).

The goal of the project is not to claim absolute field reliability. The models provide a consistent engineering basis for comparing design options, mission profiles, modularity choices and maintenance strategies.

## What The Tool Evaluates

The repository contains four subsystem evaluators:

- `fan_reliability/`: cooling fan reliability.
- `capacitor_bank_reliability/`: DC-link capacitor bank reliability.
- `inverter_reliability/`: inverter semiconductor power-module reliability.
- `rectifier_reliability/`: rectifier diode-stage reliability.

Shared helpers are kept in `common/`.

Each subsystem reads a dedicated Excel workbook, computes reliability and replacement-unit parameters, then writes the results back to the workbook in a format that can be transferred to a PELCA input file.

## Reliability Approach

The workflow follows the same logic for every subsystem:

1. Describe the subsystem design and replacement-unit boundary.
2. Define one or more mission profiles.
3. Convert each mission-profile segment into electrical, thermal and environmental stresses.
4. Estimate random failure behavior, generally with a FIDES-based model.
5. Estimate wear-out behavior when relevant, using lifetime or thermal-cycling models.
6. Convert the outputs into Weibull parameters used by PELCA.
7. Write reliability and replacement-cost data into the Excel workbook.

The output typically contains:

- early-failure Weibull parameters when available;
- random-failure Weibull parameters, usually with beta equal to `1`;
- wear-out Weibull parameters when ageing is modelled;
- replacement-unit cost and maintenance inputs;
- optional thermal or intermediate calculation data.

## Documentation

| Document | Content |
| --- | --- |
| [`documentations/Algorithm.md`](documentations/Algorithm.md) | Reliability methodology: bathtub / three-Weibull fault model, FIDES random-failure model, wear-out lifetime models, conversion to Weibull parameters, replacement-unit aggregation. |
| [`documentations/Instructions.md`](documentations/Instructions.md) | How to run the tool on the bundled variable-speed-drive examples, workbook structure reference, and how to transfer the results into a PELCA input file. |
| `<subsystem>/README.md` | Per-subsystem workbook structure, expected inputs, model notes and outputs. |

## Repository Layout

```text
PELCA/
├── run_reliability_evaluation.py   # orchestrator: runs every subsystem
├── requirements.txt                # pinned dependencies
├── README.md
│
├── documentations/                 # technical documentation
│   ├── Algorithm.md                # reliability methodology
│   └── Instructions.md             # usage + worked drive example
│
├── common/                         # shared helpers
│   ├── __init__.py                 # single source of truth for the version (__version__)
│   ├── excel_parameters.py         # generic workbook reader
│   └── README.md
│
├── fan_reliability/
│   ├── evaluate_fan_reliability.py
│   ├── data/
│   │   └── PELCA_Reliability_v1.0.0_Fan.xlsx
│   └── README.md
│
├── capacitor_bank_reliability/
│   ├── evaluate_capacitor_bank_reliability.py
│   ├── data/
│   │   └── PELCA_Reliability_v1.0.0_CapacitorBank.xlsx
│   ├── models/                     # FIDES and bathtub-curve models
│   ├── calculations/               # ripple-current calculation
│   ├── utils/                      # mission-profile and interpolation helpers
│   └── README.md
│
├── inverter_reliability/
│   ├── evaluate_inverter_reliability.py
│   ├── data/
│   │   └── PELCA_Reliability_v1.0.0_Inverter.xlsx
│   ├── igbt_reliability/           # power-module thermal + lifetime models
│   └── README.md
│
└── rectifier_reliability/
    ├── evaluate_rectifier_reliability.py
    ├── data/
    │   └── PELCA_Reliability_v1.0.0_Rectifier.xlsx
    └── README.md
```

Every subsystem folder follows the same pattern:

| Item | Role |
| --- | --- |
| `evaluate_<subsystem>_reliability.py` | Single entry point, runnable alone or from the orchestrator. |
| `data/PELCA_Reliability_v<version>_<Subsystem>.xlsx` | Default workbook, used both as input and as output. |
| `README.md` | Workbook structure, expected inputs, model notes and outputs. |
| `models/`, `calculations/`, `utils/`, `igbt_reliability/` | Optional subsystem-specific logic. |

## Installation

The tool runs on **Windows**, **Linux** and **macOS** and requires **Python 3.12**.
The procedure below follows the same logic as the main
[PELCA installation guide](../../README.md#installation-guide), so all PELCA tools
are installed and launched the same way.

### Windows

1. Download and install Python 3.12 from the official website:
   [Download Python 3.12](https://www.python.org/downloads/release/python-3129/).
2. Navigate to the folder where you want to place the project, right-click in the
   file explorer and select **Open in Terminal**, then run:

```powershell
# Clone the repository
git clone https://github.com/merce-fra/PELCA.git

# Navigate to the project directory
cd PELCA

# Create a virtual environment using Python 3.12
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv

# Allow activation of the virtual environment for this terminal session
Set-ExecutionPolicy Unrestricted -Scope Process

# Activate the virtual environment
.\.venv\Scripts\activate

# Upgrade pip to avoid compatibility issues
python -m pip install --upgrade pip

# Install the project dependencies
pip install -r requirements.txt
```

### Linux

```bash
# Clone the repository
git clone https://github.com/merce-fra/PELCA.git
cd PELCA

# Install the Python 3.12 venv module if needed
sudo apt install python3.12-venv

# Create and activate the virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install the dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS

```bash
# Clone the repository
git clone https://github.com/merce-fra/PELCA.git
cd PELCA

# Install Python 3.12 if needed
brew install python@3.12

# Create and activate the virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install the dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run All Evaluations

Activate the virtual environment, then run the orchestrator from the repository root.

**Windows**

```powershell
Set-ExecutionPolicy Unrestricted -Scope Process
.\.venv\Scripts\activate
python run_reliability_evaluation.py
```

**Linux & macOS**

```bash
source .venv/bin/activate
python run_reliability_evaluation.py
```

This executes the four subsystem evaluators with their default workbooks:

- `fan_reliability/data/PELCA_Reliability_v1.0.0_Fan.xlsx`
- `capacitor_bank_reliability/data/PELCA_Reliability_v1.0.0_CapacitorBank.xlsx`
- `inverter_reliability/data/PELCA_Reliability_v1.0.0_Inverter.xlsx`
- `rectifier_reliability/data/PELCA_Reliability_v1.0.0_Rectifier.xlsx`

The workbooks are both inputs and outputs. Results are written back into the relevant result sheets.

## Run One Subsystem

Each evaluator can also be run as a Python module (use `python` on Windows and
inside the activated virtual environment):

```bash
python -m fan_reliability.evaluate_fan_reliability fan_reliability/data/PELCA_Reliability_v1.0.0_Fan.xlsx
python -m capacitor_bank_reliability.evaluate_capacitor_bank_reliability capacitor_bank_reliability/data/PELCA_Reliability_v1.0.0_CapacitorBank.xlsx
python -m inverter_reliability.evaluate_inverter_reliability inverter_reliability/data/PELCA_Reliability_v1.0.0_Inverter.xlsx
python -m rectifier_reliability.evaluate_rectifier_reliability rectifier_reliability/data/PELCA_Reliability_v1.0.0_Rectifier.xlsx
```

If no path is given, each evaluator falls back to its default versioned workbook in
`<subsystem>/data/`. To work on another dataset, pass another workbook path to the
selected evaluator.

## Workbook Data Model

The project uses Excel workbooks because they are convenient for engineering review, scenario editing and result transfer to PELCA. The exact sheet names differ slightly by subsystem, but the same categories are used throughout the project.

### Typical Input Sheets

- `parameters` or `Parameters`: design constants, reliability factors, electrical ratings, thermal parameters, topology settings and replacement-unit information.
- `options`: plotting and debug flags.
- `mission_profile`, `Inputs` or equivalent: operating phases used for reliability assessment.
- `Replacement`: cost, labor time and maintenance data for the replacement unit.
- subsystem-specific tables: interpolation tables, thermal data or model coefficients.

### Typical Mission-Profile Columns

Mission-profile sheets usually describe several operating phases. A mission profile may contain one or more phases, and a workbook may contain several mission profiles.

Common fields include:

- mission-profile identifier;
- operating-phase flag;
- relative speed;
- relative torque or load;
- ambient or board temperature;
- thermal cycling amplitude;
- maximum cycling temperature;
- operating hours per year;
- number of cycles;
- cycle duration or weighting;
- humidity or environment factors when used by the model.

### Typical Output Sheets

- `results` or `Analysis_Results`: Weibull parameters and lifetime summary.
- `thermal_data`: intermediate thermal and stress calculations.
- `Replacement`: replacement-unit cost and maintenance information.
- comparison or debug sheets when a subsystem supports several calculation methods.

## Default Data Resources

The repository includes one default workbook per subsystem. These workbooks are intended to serve both as executable examples and as templates for new scenarios.

| Subsystem | Workbook | Main Input Sheets | Main Output Sheets |
| --- | --- | --- | --- |
| Fan | `fan_reliability/data/PELCA_Reliability_v1.0.0_Fan.xlsx` | `Parameters`, `options`, `mission_profile`, `Replacement` | `results`, `Replacement` |
| Capacitor bank | `capacitor_bank_reliability/data/PELCA_Reliability_v1.0.0_CapacitorBank.xlsx` | `parameters`, `options`, `mission_profile`, `tables`, `Replacement` | `results`, `thermal_data`, `Replacement` |
| Inverter | `inverter_reliability/data/PELCA_Reliability_v1.0.0_Inverter.xlsx` | `parameters`, `options`, `mission_profile`, `Replacement` | `results`, `thermal_data`, `comparison_pwm_iec` |
| Rectifier | `rectifier_reliability/data/PELCA_Reliability_v1.0.0_Rectifier.xlsx` | `Parameters`, `options`, `Inputs`, `Replacement` | `Analysis_Results`, `thermal_data` |

Before publishing a fork or dataset publicly, check that workbook values, comments, formulas and metadata are anonymized and suitable for redistribution.

## Interpreting Results

The calculated values are intended for comparative reliability and maintenance analysis. They depend strongly on:

- mission-profile quality;
- thermal assumptions;
- selected model parameters;
- topology assumptions;
- replacement-unit boundaries;
- cost and repair-time assumptions.

Use the outputs to compare scenarios under a consistent set of assumptions. Avoid interpreting the numbers as guaranteed field failure rates without additional validation.

## Development Notes

The current architecture keeps each subsystem independent while using a common structure:

- one main `evaluate_*_reliability.py` entry point;
- one `data/` folder for the default workbook;
- optional `models/`, `calculations/` and `utils/` packages for subsystem-specific logic;
- one README per subsystem.

When adding a new subsystem, follow the same pattern and document:

- replacement-unit boundary;
- workbook input sheets;
- model assumptions;
- output sheets;
- how to run the evaluator alone and from the global orchestrator.

## Public Release Checklist

Before publishing on GitHub, review:

- workbook content and metadata;
- license file;
- dependency versions;
- sensitive comments or internal references;
- sample datasets;
- automated tests;
- continuous-integration workflow;
- generated documentation configuration.

---
### Authors
PELCA Reliability Evaluator was developed by:
- Laurent Foube
- Tarak Ghersi
- Thomas Lesaulnier
