# -*- coding: utf-8 -*-
"""\brief Generate space-vector PWM modulation waveforms.

This module is part of the PELCA reliability evaluator.
"""
import numpy as np
import pandas as pd
import math

class ModulationSVPWM:
    """Base class for generating modulation signals and phase currents."""
    def __init__(self, M: float = 0.8, V_dc: float = 540):
        """Initialize the object with the provided configuration."""
        self.M = M # Modulation Index
        self.num_cycles: int = 1    # Number of output cycles to simulate
        self.V_dc = V_dc            # DC Bus Voltage (Volts)
        self.num_cycles: int = 1    # Number of output cycles to simulate


    def generate_waveforms(self, I_out_rms: float, cos_phi: float, f_out: float, f_sw: float) -> pd.DataFrame:
        """Generates instantaneous current and duty cycle waveforms over one f_out cycle."""

        # 1. TIME BASE SETUP
        T_out = 1.0 / f_out
        T_sw = 1.0 / f_sw

        # what is the right resolution for the reference signals?
        points_per_cycle = max(100, int(T_out / T_sw) * 10)
        total_points = points_per_cycle * self.num_cycles

        time = np.linspace(0, self.num_cycles * T_out, total_points, endpoint=False)


        #time = np.linspace(0, T_out, points_per_cycle, endpoint=False)

        # 2. CURRENT GENERATION (Assuming balanced, sinusoidal load current)
        I_peak = I_out_rms * np.sqrt(2)
        phi_rad = math.acos(cos_phi)
        omega_t = 2 * np.pi * f_out * time

        i_a = I_peak * np.cos(omega_t - phi_rad)
        i_b = I_peak * np.cos(omega_t - phi_rad - 2 * np.pi / 3)
        i_c = I_peak * np.cos(omega_t - phi_rad + 2 * np.pi / 3)

        # i_a = I_peak * np.cos(omega_t - phi_rad)
        # i_b = I_peak * np.cos(omega_t - phi_rad - 2 * np.pi / 3)
        # i_c = I_peak * np.cos(omega_t - phi_rad + 2 * np.pi / 3)


        # 3. VOLTAGE REFERENCE GENERATION (Simplified sinusoidal reference)
        M = self.M # 0.8
        V_ref_peak = M * self.V_dc / (np.sqrt(3))

        v_a_ref = V_ref_peak * np.cos(omega_t)
        v_b_ref = V_ref_peak * np.cos(omega_t - 2 * np.pi / 3)
        v_c_ref = V_ref_peak * np.cos(omega_t + 2 * np.pi / 3)

        # Convert to alpha-beta plane (for SVPWM sector determination)
        v_alpha = (2/3) * (v_a_ref - 0.5 * v_b_ref - 0.5 * v_c_ref)
        v_beta  = (2/3) * (0.866 * v_b_ref - 0.866 * v_c_ref)

        # 4. SVPWM IMPLEMENTATION (Sector & Dwell Time Calculation)
        S_a, S_b, S_c = np.zeros(total_points), np.zeros(total_points), np.zeros(total_points)
        V_ref_mag   = np.sqrt(v_alpha**2 + v_beta**2) # almost constant
        V_ref_angle = np.arctan2(v_beta, v_alpha)
        V_ref_angle[V_ref_angle < 0] += 2 * np.pi
        V_base = 2/3 * self.V_dc

        np_D_a = np.array([])
        np_D_b = np.array([])
        np_D_c = np.array([])
        for k in range(total_points):
            angle  = V_ref_angle[k]
            mag    = V_ref_mag[k]
            sector = int(angle // (np.pi/3)) + 1
            angle_sector = angle - (sector - 1) * (np.pi/3)
            T1 = (np.sqrt(3) * mag / V_base) * np.sin(np.pi/3 - angle_sector) * T_sw
            T2 = (np.sqrt(3) * mag / V_base) * np.sin(angle_sector) * T_sw
            T0 = T_sw - T1 - T2

            if T0 < 0:
                T0 = 0.0
                T1_new = T1 * T_sw / (T1 + T2)
                T2_new = T2 * T_sw / (T1 + T2)
                T1, T2 = T1_new, T2_new

            if sector == 1:
                T_a, T_b, T_c = (T_sw - T0)/2 + T1 + T2, (T_sw - T0)/2 + T2, (T_sw - T0)/2
            elif sector == 2:
                T_a, T_b, T_c = (T_sw - T0)/2 + T1, (T_sw - T0)/2 + T1 + T2, (T_sw - T0)/2
            elif sector == 3:
                T_a, T_b, T_c = (T_sw - T0)/2, (T_sw - T0)/2 + T1 + T2, (T_sw - T0)/2 + T2
            elif sector == 4:
                T_a, T_b, T_c = (T_sw - T0)/2, (T_sw - T0)/2 + T1, (T_sw - T0)/2 + T1 + T2
            elif sector == 5:
                T_a, T_b, T_c = (T_sw - T0)/2 + T2, (T_sw - T0)/2, (T_sw - T0)/2 + T1 + T2
            elif sector == 6:
                T_a, T_b, T_c = (T_sw - T0)/2 + T1 + T2, (T_sw - T0)/2, (T_sw - T0)/2 + T1

            # duty cycles applied to the top switches of legs
            D_a, D_b, D_c = T_a / T_sw, T_b / T_sw, T_c / T_sw
            np_D_a = np.append(np_D_a, [D_a])
            np_D_b = np.append(np_D_b, [D_b])
            np_D_c = np.append(np_D_c, [D_c])
            S_a[k], S_b[k], S_c[k] = D_a, D_b, D_c


        # 5. CONSOLIDATE RESULTS

        results = pd.DataFrame({
            'time (s)': time,
            'i_a (A)': i_a, 'i_b (A)': i_b, 'i_c (A)': i_c,
            'Duty_a (0-1)': np_D_a, 'Duty_b (0-1)': np_D_b, 'Duty_c (0-1)': np_D_c,
        })
        return results
