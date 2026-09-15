# -*- coding: utf-8 -*-
"""\brief Calculate semiconductor junction temperatures from thermal models.

This module is part of the PELCA reliability evaluator.
"""
from inverter_reliability.igbt_reliability.components.DeviceParameters import DeviceParameters
from inverter_reliability.igbt_reliability.calculations.LossModel import LossModel

import numpy as np
import pandas as pd
#from plot_dataframe import plot_P_avg_semicond
import matplotlib.pyplot as plt

class HeatsinkParameters:
    """Stores parameters for the Case-to-Ambient thermal model (Rth and Cth)."""
    def __init__(self):
        # T_ambient is now defined in the mission profile segments

        # # according to calculation performed by PY (considering individual "heatsink" for each power module  - no thermal coupling)
        """Initialize the object with the provided configuration."""
        self.Rth_ca = 0.2085    # Rth_heatsink      # K/W, Thermal resistance Case-to-Ambient <calculated by PY>
        self.Cth_ca = 9360/6    # J/K, Thermal capacitance of the heatsink

        # Check whether the thermal mass is realistic: m = 10.4 kg (aluminum), Cth=m*c_p, c_p in J/(kg*K).
        # c_p =  900 J/kg.K
        # => Cth_ca = 900 x 10.4 = 9360

        # Note: at present heatsink temperature considered in steady state : only need for Rth_ca

class ThermalModel:
    """
    Handles thermal integration for case-to-ambient (heatsink) and
    junction-to-case (4th-order Foster network).
    """
    def __init__(self, device_params: DeviceParameters, hs_params: HeatsinkParameters):
        """Initialize the object with the provided configuration."""
        self.DP = device_params # Device Parameters
        self.HP = hs_params     # Heatsink Parameters
        self.device_map = LossModel(device_params)._define_device_map()

    # heatsink thermal model
    def update_case_temp(self, current_T_case: float, P_module_avg: float, T_ambient: float, time_step: float) -> float:
        """
        Calculates the new heatsink temperature (T_case) using an ANALYTICAL solution.
        T_ambient is an input.
        """
        Rth_ca = self.HP.Rth_ca
        Cth_ca = self.HP.Cth_ca
        Tau_ca = Rth_ca * Cth_ca # Heatsink time constant

        if Tau_ca == 0:
            return T_ambient + P_module_avg * Rth_ca

        # Steady-state temperature (Tss) for the current power level relative to T_ambient
        T_ss = T_ambient + P_module_avg * Rth_ca

        # Analytical solution (simple RC network)
        T_case_new = T_ss + (current_T_case - T_ss) * np.exp(-time_step / Tau_ca)

        return T_case_new

    # thermal model of diodes / IGBTs
    # <6 IGBTs + 6 diodes considered in device_map>

    # note: here T_case_diode & igbt distinguished but actually the Tcase of module
    # thermal model of heatsink of module fed with avg losses of module
    # => a single Tcase temperature can be derived (supposed to be in steady state)

    def calculate_junction_temps(self, data: pd.DataFrame, T_case_igbt: float, T_case_diode: float, debug_flag: bool = True) -> pd.DataFrame:
        """
        Calculates T_j average and transient ripple using a 4th-order Foster network.
        """
        dt = data['time (s)'].iloc[1] - data['time (s)'].iloc[0] # time resolution of data

        max_swing_tracker = 0
        max_Tj_avg_tracker_igbt = T_case_igbt
        max_Tj_avg_tracker_diode = T_case_diode
        max_swing_device = 'None'

        for prefix, d_type, _, _ in self.device_map:
            # for each device (IGBT, diode) evaluates its thermal model (at package level)
            # in order to determine the temperature ripple of the component during one cycle Fout

            if d_type == 'IGBT':
                Rth = self.DP.Rth_IGBT
                Cth = self.DP.Cth_IGBT
                Rth_total = self.DP.Rth_jc_IGBT_avg
            else:
                Rth = self.DP.Rth_Diode
                Cth = self.DP.Cth_Diode
                Rth_total = self.DP.Rth_jc_Diode_avg

            P_total = data[f'P_total_{prefix} (W)']
            P_avg = P_total.mean()
            data[f'P_avg_{prefix} (W)'] = P_avg

            if d_type == 'IGBT':
                T_case_baseline = T_case_igbt
            else:
                T_case_baseline = T_case_diode

            # Average temperature rise (steady-state component)
            Delta_Tj_avg = P_avg * Rth_total
            Tj_avg_device = Delta_Tj_avg + T_case_baseline


            # --- Transient Ripple Calculation (Analytical Foster Network Integration) ---
            T_rc = np.zeros((len(data), len(Rth)))

            for i in range(len(Rth)):
                T_rc[0, i] = P_avg * Rth[i]

            for k in range(1, len(data)):
                P_in = P_total.iloc[k]

                for i in range(len(Rth)):
                    R = Rth[i]
                    C = Cth[i]
                    Tau = R * C
                    T_prev = T_rc[k-1, i]
                    T_ss_rc = P_in * R
                    T_rc[k, i] = T_ss_rc + (T_prev - T_ss_rc) * np.exp(-dt / Tau)

            Delta_Tj_jc_instantaneous = T_rc.sum(axis=1)
            Tj_instantaneous = Delta_Tj_jc_instantaneous + T_case_baseline # numpy.ndarray of same size as data
            Delta_Tj_swing = Tj_instantaneous.max() - Tj_instantaneous.min()

            # --- Store Results ---
            data[f'Delta_Tj_{prefix} (K)'] = Delta_Tj_swing
            data[f'Tj_avg_{prefix} (C)'] = Tj_avg_device

            if d_type == 'IGBT':
                if Tj_avg_device > max_Tj_avg_tracker_igbt:
                    max_Tj_avg_tracker_igbt = Tj_avg_device
                    max_swing_device = prefix
            else:
                if Tj_avg_device > max_Tj_avg_tracker_diode:
                    max_Tj_avg_tracker_diode = Tj_avg_device
                    max_swing_device = prefix

            if Delta_Tj_swing > max_swing_tracker:
                 max_swing_tracker = Delta_Tj_swing

            if debug_flag:
                # should display only once in a while
                plt.plot(Tj_instantaneous)

        if debug_flag:
            plt.show()

        # to place in the loop?
        data['Max_Delta_Tj_Swing (K)'] = max_swing_tracker
        data['Max_Delta_Tj_Device'] = max_swing_device
        if d_type == 'IGBT':
            data['Max_Tj_avg (C)'] = max_Tj_avg_tracker_igbt
        else:
            data['Max_Tj_avg (C)'] = max_Tj_avg_tracker_diode



        return data




