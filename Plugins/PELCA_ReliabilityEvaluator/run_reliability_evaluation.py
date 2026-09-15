# -*- coding: utf-8 -*-
"""\brief Run the complete reliability evaluation workflow for all subsystems.

This module is part of the PELCA reliability evaluator.
"""

# TO DO: add construction of mission profile starting from system profile
# Each calculation module returns the losses during operations to enable calculation of increase of air temperature
# entering the next stage => this in turn enable to recalculate some parameters of component level mission profile

from common import __version__
from fan_reliability.evaluate_fan_reliability import evaluate_fan_reliability
from capacitor_bank_reliability.evaluate_capacitor_bank_reliability import evaluate_capacitor_bank_reliability
from inverter_reliability.evaluate_inverter_reliability import evaluate_inverter_reliability
from rectifier_reliability.evaluate_rectifier_reliability import evaluate_rectifier_reliability

# The tool version is also embedded in the default data-workbook file names.
VERSION = __version__

# <the tools must be available as python script (some matlab scripts have to be converted in python first)>
# the different Excel files must be available at top level (in same directory as this file)


def main():
    """Evaluate all reliability models."""

    print(f"PELCA Reliability Evaluator v{VERSION}: starting full evaluation workflow.", flush=True)

    # By default every subsystem is evaluated with its default versioned workbook.
    # Comment out a line to skip a subsystem.
    evaluate_fan_reliability(f"fan_reliability/data/PELCA_Reliability_v{VERSION}_Fan.xlsx")
    evaluate_capacitor_bank_reliability(f"capacitor_bank_reliability/data/PELCA_Reliability_v{VERSION}_CapacitorBank.xlsx")
    evaluate_inverter_reliability(f"inverter_reliability/data/PELCA_Reliability_v{VERSION}_Inverter.xlsx")
    evaluate_rectifier_reliability(f"rectifier_reliability/data/PELCA_Reliability_v{VERSION}_Rectifier.xlsx")

    print("\nPELCA Reliability Evaluator: full evaluation workflow finished.", flush=True)


if __name__ == "__main__":
    main()

# ============================================ END OF CODE ====================================================================
