# -*- coding: utf-8 -*-
"""\brief Generate modulation signals and phase currents.

This module is part of the PELCA reliability evaluator.
"""
import pandas as pd
import numpy as np
import math

class ModulationStrategy:
    """Base class for generating modulation signals and phase currents."""
    # =======================================
    # here it implement SPWM strategy
    # could be replaced by SVPWM for instance
    # =======================================

    def __init__(self, M: float = 0.8):
        """Initialize the object with the provided configuration."""
        self.M = M # Modulation Index

    # returns a dataframe containing NB_PERIODS (min=1) period(s) of modulation signals and output currents
    def generate_waveforms(self, I_out_rms: float, cos_phi: float, f_out: float, f_sw: float, NB_PERIODS = 1) -> pd.DataFrame:
        """Generates instantaneous current and duty cycle waveforms over one f_out cycle."""

        if f_out<0.5:
            f_out=0.5   # limited to 1% of fout (maybe already quite low...)

        T_out = NB_PERIODS / f_out
        T_sw = 1.0 / f_sw

        # what is the right resolution for the reference signals?
        points_per_cycle = max(100, int(T_out / T_sw) * 1) # no significant change (1 .. 100) - 10 initially
        time = np.linspace(0, T_out, points_per_cycle, endpoint=False)

        # CURRENT GENERATION (Assuming inverter with balanced, sinusoidal load current)
        I_peak = I_out_rms * np.sqrt(2)
        phi_rad = math.acos(max(-1.0, min(1.0, cos_phi)))
        omega_t = 2 * np.pi * f_out * time

        i_a = I_peak * np.cos(omega_t - phi_rad)
        i_b = I_peak * np.cos(omega_t - phi_rad - 2 * np.pi / 3)
        i_c = I_peak * np.cos(omega_t - phi_rad + 2 * np.pi / 3)

        # duty cycles applied to the top switches of legs
        # SPWM (sinusoidal) modulation
        D_a = self.M / 2 * np.cos(omega_t) + 0.5                  # U
        D_b = self.M / 2 * np.cos(omega_t - 2 * np.pi / 3) + 0.5  # V
        D_c = self.M / 2 * np.cos(omega_t + 2 * np.pi / 3) + 0.5  # W

        results = pd.DataFrame({
            'time (s)': time,
            'i_a (A)': i_a, 'i_b (A)': i_b, 'i_c (A)': i_c,
            'Duty_a (0-1)': D_a, 'Duty_b (0-1)': D_b, 'Duty_c (0-1)': D_c,
        })
        return results

if __name__ == '__main__':
    # check
    import matplotlib.pyplot as plt
    from inverter_reliability.igbt_reliability.utils.plot_dataframe import plot_current_and_modulation_functions

    M = ModulationStrategy()
    results = M.generate_waveforms(I_out_rms=300, cos_phi=0.8, f_out=50, f_sw=4000, NB_PERIODS = 2)
    plot_current_and_modulation_functions(results)
