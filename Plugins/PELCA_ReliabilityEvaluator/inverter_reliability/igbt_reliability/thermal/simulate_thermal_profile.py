# -*- coding: utf-8 -*-
"""\brief Simulate thermal response to periodic power profiles.

This module is part of the PELCA reliability evaluator.
"""
import numpy as np
import matplotlib.pyplot as plt

# for a given case temperature (derived from heatsink temperature), simulates the junction temperature of a particular device (diode or IGBT)
# time resolution for the simulation is given by dt
def simulate_thermal_profile(Rth, Cth, P_on, P_off, freq, T_case=40.0, sim_time=1.0, dt=1e-4, display_sim=True):
    """
        Simulates junction temperature using a configurable Foster model.

        Parameters:
        - Rth: list of thermal resistances [K/W]
        - Cth: list of thermal capacitances [J/K]
        - P_on: ON power (W)
        - P_off: OFF power (W)
        - freq: periodic profile frequency (Hz)
        - T_case: case temperature (degC)
        - sim_time: simulation duration (s)
        - dt: time step (s)

        Returns:
        - time: time vector
        - Tj: junction temperature (degC)
        - metrics: dictionary with Tmean, Tmax, Tmin, DeltaT
    """


    Rth = np.array(Rth)
    Cth = np.array(Cth)
    Tau = Rth * Cth
    period = 1.0 / freq


    time = np.arange(0, sim_time, dt)
    # generation of power profile:
    power = np.where((time % period) < (period / 2), P_on, P_off)
    # <could generate a more complicated profile in a dataframe
    # if a thermal model with coupling is considered>

    # -----------------------------
    # thermal simulation (Foster)
    # -----------------------------
    T_rc = np.zeros((len(time), len(Rth)))  # RC contributions
    Tj = np.zeros(len(time))                # junction temperature

    for k in range(1, len(time)):
        P_in = power[k]
        for i in range(len(Rth)):
            R = Rth[i]
            Tau_i = Tau[i]
            T_prev = T_rc[k-1, i]
            T_ss = P_in * R
            T_rc[k, i] = T_ss + (T_prev - T_ss) * np.exp(-dt / Tau_i)
        Tj[k] = T_case + T_rc[k].sum()


    # -----------------------------
    # steady state analysis
    # -----------------------------
    # here we take the last period to calcuate Tmax, Tmin, DeltaT and mean
    # <under assumption that simulation time is large enough; Otherwise preferable to consider the Rth to determine avg temp>
    last_period_start = int(len(time) - period/dt)
    Tj_last_period = Tj[last_period_start:]
    Tmax   = Tj_last_period.max()
    Tmin   = Tj_last_period.min()
    DeltaT = Tmax - Tmin
    Tmean  = Tj_last_period.mean()


    metrics = {
        "Tmean (degC)": Tmean,
        "Tmax (degC)": Tmax,
        "Tmin (degC)": Tmin,
        "DeltaT (K)": DeltaT
    }

    # debug
    #print(f"simulate_thermal_profile: TAvg temperature (steady state): {Tmean:.2f} degC")
    #print(f"simulate_thermal_profile: Tmax: {Tmax:.2f} degC")
    #print(f"simulate_thermal_profile: Tmin: {Tmin:.2f} degC")
    #print(f"simulate_thermal_profile: DeltaT (cycle): {DeltaT:.2f} K")

    # could add identification of segment of mission profile

    if display_sim:
        # -----------------------------
        # Affichage
        # -----------------------------
        plt.figure(figsize=(10, 5))
        plt.plot(time, Tj, label='Tj (degC)')
        plt.xlabel('Time (s)')
        plt.ylabel('Junction temperature (degC)')
        plt.title('Thermal variation of semiconductor')
        plt.grid(True)
        plt.legend()
        plt.show()

    return time, Tj, metrics
