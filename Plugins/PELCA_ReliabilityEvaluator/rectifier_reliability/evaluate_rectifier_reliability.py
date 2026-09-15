# -*- coding: utf-8 -*-
"""\brief Evaluate rectifier diode reliability and write PELCA-ready results to Excel.

This module is part of the PELCA reliability evaluator.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math

from openpyxl.styles import Alignment

from inverter_reliability.igbt_reliability.calculations.calc_op_point import calc_active_power

# ===============================
# Switches / Options
# ===============================
# do not change!
USING_MCM = 0                      # 0 => packaged diode, 1 => MCM  (no validated yet! much shorter MTBF...)                   [impact on MTBF]

USE_ENHANCED_AGING_MODEL = 1       # 1 => ageing model (C, Ea, alpha, Kb, dependency Tj), 0 => legacy (DeltaT^-5 * 10^15.15)
SHOW_THERMAL_DEBUG = 0             # 1 => show the detailed thermal response of a phase of mission profile (via plot_thermal_cycle)
debug_FIDES = 0                    # to display debug info related to calculation of FIDES parameters
debug_thermal = 0                  # to display debug info related to thermal calculation
# ===============================
# Utilities / Helpers
# ===============================
def load_parameters(excel_filename, sheet_name="Parameters"):
    """
    read all constants Key/Value from Parameters sheet.
    Return a dictionary mapping parameter names to values.
    """
    params_df = pd.read_excel(excel_filename, sheet_name=sheet_name, engine="openpyxl")

    params = {}

    # 2 possibilities :
    # - columns named "Parameter" / "Value"
    # - any two columns -> we take the first as the key, the second as the value
    if "Parameter" in params_df.columns and "Value" in params_df.columns:
        key_col = "Parameter"
        val_col = "Value"
    else:
        key_col = params_df.columns[0]
        val_col = params_df.columns[1]

    for k, v in zip(params_df[key_col], params_df[val_col]):
        if pd.isna(k):
            continue
        key = str(k).strip()

        # automatic type conversion :
        # boolean ?
        if isinstance(v, str) and v.lower() in ["true", "false"]:
            value = v.lower() == "true"
        else:
            try:
                value = float(v)
            except:
                value = v

        params[key] = value

    return params

def fitFosterModel(time_data, Zth_data):
    # (not a real fit: pre-adjusted parameters)
    """Run fit foster model."""
    R_fit   = np.array([0.02936311, 0.00772832, 0.14365646])
    tau_fit = np.array([0.0197093, 0.00175757, 0.23590374])
    C_fit = tau_fit / R_fit
    return R_fit, tau_fit, C_fit


def plot_thermal_cycle(t_sim, P_waveform, T_junction, t_on, t_off, title="thermal response to the power steps"):
    """
    Plot the temperature (response) as function of power losses & the power losses (stimulus) vs time (on twin axes)
    """
    fig, ax1 = plt.subplots(figsize=(10, 5))

    # Axe Power losses
    color_p = "#1f77b4"
    ax1.plot(t_sim, P_waveform, color=color_p, label="losses (W)", linewidth=1.5)
    ax1.set_xlabel("time (s)", fontsize=12)
    ax1.set_ylabel("power losses (W)", color=color_p, fontsize=12)
    ax1.tick_params(axis='y', labelcolor=color_p)

    # Temperature axis
    ax2 = ax1.twinx()
    color_t = "#d62728"
    ax2.plot(t_sim, T_junction, color=color_t, label="junction temperature DeltaT (K)", linewidth=1.5)
    ax2.set_ylabel("temperature (K, relative)", color=color_t, fontsize=12)
    ax2.tick_params(axis='y', labelcolor=color_t)

    # Visual marking of a cycle
    if t_on > 0 or t_off > 0:
        T_cycle = t_on + t_off
        if T_cycle > 0:
            # Draw a light band across a cycle in the middle of the simulation
            t0 = (t_sim[-1] / 2.0) - T_cycle
            t1 = t0 + t_on
            ax1.axvspan(t0, t1, color=color_p, alpha=0.06, label="Phase ON")
            ax1.axvspan(t1, t0 + T_cycle, color=color_p, alpha=0.03, label="Phase OFF")

    # Combined legends
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper right")

    ax1.set_title(title, fontsize=13)
    ax1.grid(True, which="both", linestyle="--", alpha=0.3)
    fig.tight_layout()
    plt.show()


def simulateDynamicThermalResponse(R_fit, tau_fit, P_on, P_off, t_on, t_off, n_cycles=100, points_per_on=50):
    """
    Simulates the dynamic thermal response of an equivalent RC network (R_fit, tau_fit)
    subjected to a periodic power cycle P_on/P_off.
    Returns delta_T (K), T_rise_mean (K), t_sim, P_waveform, T_junction.
    """
    # time step based on resolution during the phase ON
    delta_t = t_on / points_per_on if t_on > 0 else max(t_off / max(points_per_on, 1), 1e-6)
    N_on = int(np.round(t_on / delta_t)) if t_on > 0 else 0
    N_off = int(np.round(t_off / delta_t)) if t_off > 0 else 0

    # security if t_on or t_off ~ 0
    N_on = max(N_on, 1) if t_on > 0 else 0
    N_off = max(N_off, 1) if t_off > 0 else 0

    # One cycle ON/OFF
    if (N_on + N_off) > 0:
        P_cycle = np.concatenate([P_on * np.ones(N_on), P_off * np.ones(N_off)])
    else:
        P_cycle = np.array([P_off])

    # repeat the cycle
    P_waveform = np.tile(P_cycle, n_cycles)
    t_sim = np.arange(len(P_waveform)) * delta_t

    # thermal response to a step: Z_step(t) = sum R_i (1 - exp(-t/tau_i))
    Z_step = np.zeros_like(t_sim, dtype=float)
    for R, tau in zip(np.atleast_1d(R_fit), np.atleast_1d(tau_fit)):
        if tau <= 0:
            continue
        Z_step += R * (1.0 - np.exp(-t_sim / tau))

    # dZ/dt (impulse) then convolution T = P * dZ/dt
    dZ_dt = np.diff(np.concatenate([[0.0], Z_step])) / delta_t
    T_junction = np.convolve(P_waveform, dZ_dt, mode='full') * delta_t
    T_junction = T_junction[:len(t_sim)]  # limited to the length of simulation

    # ment over the last cycle
    T_last = T_junction[-len(P_cycle):] if len(P_cycle) > 0 else T_junction.copy()
    delta_T = float(np.max(T_last) - np.min(T_last))
    T_rise_mean = float(np.mean(T_last))

    return delta_T, T_rise_mean, t_sim, P_waveform, T_junction


def Plot_CDFs(profile_names, time_years, all_cdf_results_system, max_time=30):
    # Plot CDFs
    """Run plot c d fs."""
    plt.figure()
    for i, name in enumerate(profile_names):
        plt.plot(time_years, all_cdf_results_system[i], label=name)
    plt.suptitle('CDFs')
    plt.xlabel("Time (years)")
    plt.ylabel("Cumulative Failure Probability")
    plt.xlim(0, max_time)
    plt.grid(True)
    plt.legend()
    plt.show()


def to_bool_excel(v):
    """
    Converts correctly 'true'/'false' (str), True/False, 1/0, NaN in bool.
    """
    if isinstance(v, bool):
        return v
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return False
    s = str(v).strip().lower()
    if s in ('true', '1', 'yes', 'y'):
        return True
    if s in ('false', '0', 'no', 'n'):
        return False
    return False


# =====================================
# Core FIDES factors ("packaged" diode)
# =====================================
def packaged_diode_phase_lambda(
    T_J_composant_C, T_heatsink_C,
    Operating_Hours_per_Year, V_applied, N_Cy, Theta_cy, G_RMS_val,
    RH_ambient, T_ambient_board_C, Pi_application_i,
    Operating_Phase_bool, Is_Signal_Diode_under_1A_bool,
    Delta_T_Heatsink_C, T_max_cycling_C,
    # constants:
    lambda_0TH_rectifier, lambda_0TCycase_rectifier, lambda_0TCysolder_joints_rectifier, lambda_0RH_rectifier, lambda_0Meca_rectifier,
    V_nominal, Pi_placement, Pi_hardening, C_sensitivity, t_total
):
    """
    Returns the time-weighted contribution (FIT) for ONE phase of mission profile (packaged diode).
    """
    T_ref_K = T_heatsink_C + 273.15  # reference temperature for composant (baseplate temperature), in Kelvin

    T_J_comp_K = T_J_composant_C + 273.15 # K
    T_max_cycling_K = (T_max_cycling_C if np.isfinite(T_max_cycling_C) else T_ambient_board_C) + 273.15 # T_max_J_K

    # TCy case & solder joints (formules MATLAB)
    denom_hours = max(Operating_Hours_per_Year, 1e-12)
    Pi_TCycase = (12.0 * N_Cy / denom_hours) * (Delta_T_Heatsink_C / 20.0)**4 * np.exp(1414.0 * (1.0 / 313.0 - 1.0 / T_max_cycling_K))

    # Pi_TCysolder_joints  ... problem if Delta_T_Heatsink_C < 0 : (Delta_T_Heatsink_C / 20.0)**1.9 => nan
    Pi_TCysolder = (12.0 * N_Cy / denom_hours) * (min(Theta_cy, 2.0) / 2.0) * (Delta_T_Heatsink_C / 20.0)**1.9 * np.exp(1414.0 * (1.0 / 313.0 - 1.0 / T_max_cycling_K))

    Pi_Meca = (G_RMS_val / 0.5)**1.5 if G_RMS_val > 0 else 0.0
    Pi_Induit_i = (Pi_placement * Pi_application_i * Pi_hardening) ** (0.511 * np.log(C_sensitivity))

    # Pi_El (not useful here : "signal diode" not used => 1.0)
    if Is_Signal_Diode_under_1A_bool:
        V_ratio = (V_applied * np.sqrt(2.0)) / V_nominal if V_nominal > 0 else 0.0
        Pi_El = (V_ratio ** 2.4) if V_ratio > 0.3 else 0.056
    else:
        Pi_El = 1.0

    # Pi therm & RH
    if Operating_Phase_bool:
        #Pi_Thermal = Pi_El * np.exp(11604.0 * 0.7 * ((1.0 / (60.0 + 273.0)) - (1.0 / T_J_comp_K)))
        Pi_Thermal = Pi_El * np.exp(11604.0 * 0.7 * ((1.0 / 293.0) - (1.0 / T_J_comp_K)))  # p 137 FIDES 2022
        Pi_RH = 0.0
    else:
        Pi_Thermal = 0.0
        Pi_RH = (RH_ambient / 70.0) ** 4.4 * np.exp(11604.0 * 0.9 * ((1.0 / 293.0) - (1.0 / T_ref_K))) # T_J_comp_K

    # debug
    if debug_FIDES:
        print("Pi_Thermal:", Pi_Thermal)     #
        print("Pi_TCycase:", Pi_TCycase)     #
        print("Pi_TCysolder:", Pi_TCysolder) #
        print("Pi_RH:", Pi_RH)               #
        print("Pi_Meca:", Pi_Meca)           #

    sum_lambda0_Pi = (
        lambda_0TH_rectifier * Pi_Thermal
        + lambda_0TCycase_rectifier * Pi_TCycase
        + lambda_0TCysolder_joints_rectifier * Pi_TCysolder
        + lambda_0RH_rectifier * Pi_RH
        + lambda_0Meca_rectifier * Pi_Meca
    )
    weighted = sum_lambda0_Pi * Pi_Induit_i * (Operating_Hours_per_Year / t_total)
    return float(weighted)


# ===============================================
# MCM (optional, direct translation from MATLAB)
# ===============================================
def MCM_diode_phase_lambda(
    T_J_comp_C, T_heatsink_C,
    Operating_Hours_per_Year, V_applied, N_Cy, G_RMS_val,
    RH_ambient, Pi_application_i,
    Operating_Phase_bool, Is_Signal_Diode_under_1A_bool,
    Delta_T_cycling_C, T_max_cycling_C,
    # constants (locales et globales):
    V_nominal, Pi_placement, Pi_hardening, t_total
):
    # local constants (from MATLAB)
    # ============ not used ===============
    """Run m c m diode phase lambda."""
    Pi_MCM_process = 1.35       # PI_H&M_process
    Pi_process_rectifier = 4    # Pi_process
    Pi_PM_ucomponent = 1.25
    Pi_placement_local = 1.8    # Analogue power interface (1.8) or non-interface function (1.6)
    Pi_application_const = 1.0  # normally comes from mission profile (specified for each phase)
    Pi_ruggedising = 1.7        # default value
    # =====================================
    Csensitivity = 5.5    #

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # specific to diode power module
    # constants related to considered MCM (equivalent to xxx power module)
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    Scase = 28.60         # cm2
    Nb_wires = 48         # number of aluminum wirebonds
    S_diode_mm2 = 342.25  # mm2 (per diode)
    Nb_diode = 2          # not used

    # Pi_TCy_case
    T_max_cycling_K = (T_max_cycling_C if np.isfinite(T_max_cycling_C) else T_heatsink_C) + 273.15 # conversion in K
    denom_hours = max(Operating_Hours_per_Year, 1e-12) # usage duration during one year
    Pi_TCy_case = (12.0 * N_Cy / denom_hours) * (Delta_T_cycling_C / 20.0)**4 * np.exp(1414.0 * ((1.0 / 313.0) - (1.0 / T_max_cycling_K)))

    # calculates the factor Pi_ME (mechanical) as function of vibrations.
    Pi_ME = (G_RMS_val / 0.5)**1.5 if G_RMS_val > 0 else 0.0

    # Pi_hardening <=> Pi_ruggedising
    Pi_Induit_i = (Pi_placement * Pi_application_i * Pi_hardening) ** (0.511 * np.log(Csensitivity)) # Pi_induced_i

    # Pi_El <not used>
    if Is_Signal_Diode_under_1A_bool:
        V_ratio = (V_applied * np.sqrt(2.0)) / V_nominal if V_nominal > 0 else 0.0
        Pi_El = (V_ratio ** 2.4) if V_ratio > 0.3 else 0.056
    else:
        Pi_El = 1.0

    # Pi thermal / RH
    if Operating_Phase_bool:
        # calculates the factor Pi_thermal for given junction temperature
        Pi_thermal = np.exp(11604.0 * 0.7 * ((1.0 / 293.0) - (1.0 / (T_J_comp_C + 273.0)))) # thermal impact
        Pi_RH = 0.0   # no impact of humidity
    else:
        Pi_thermal = 0.0 # during non operating phase, negligible impact of thermal
        # calculates Pi_RH related to impact of humidity & temperature
        Pi_RH = (RH_ambient / 70.0)**4.4 * np.exp(11604.0 * 0.9 * ((1.0 / 293.0) - (1.0 / (T_heatsink_C + 273.0))))

    # 'chip' contribution
    lambda0_chip_TCy = 0.011
    C_moulding = 1.6 # 2 for epoxy moulding
    d = 0.1 # discrete circuit (IGBT or DIODE die)
    S = S_diode_mm2
    C_chip_surface = (1.0 + (S ** d))
    lambda0_th = 0.1574
    N = 1  # no diodes in parallel within module : 1 diode = 1 chip
    lambda_chip = (lambda0_th * np.sqrt(N) * Pi_thermal) + (lambda0_chip_TCy * C_moulding * C_chip_surface * Pi_TCy_case)

    # Bonding / wiring (impact of internal wiring)
    lambda0_wiring = 1.04e-4 * (Nb_wires ** 0.93)
    C_hermeticity = 1.0  # molded
    lamda0_CHIP_RH = 7.01e-7 * (Nb_wires ** 2.41)
    gamma_TCy = 0.65
    lambda_wiring = lambda0_wiring * (C_moulding * gamma_TCy * Pi_TCy_case + lamda0_CHIP_RH * C_hermeticity * Pi_RH)
    # note: no term c_particle * gamma_ME * Pi_ME,  since c_particle=0 (molded)

    # Substrate / circuit
    Pi_class = 1.0              # minimum conductor width (um) / minimum spacing between conductors or pads (um)
    Pi_techno_substrate = 0.25  # ceramic
    Nlayers = 1
    lambda0_substrate = 2.08e-4 # alumina substrate with moulding
    b = 0.93
    gamma_TCy = 0.6
    gamma_ME = 0.35
    gamma_RH = 0.04
    gamma_chemical = 0.01
    C_ME = 1.0 + 0.1 * np.sqrt(Scase) # Scase : surface of module in cm2
    Ntracks = 5                       # number of conductors on substrate
    Pi_chemical = 0.0

    lambda0_CS = lambda0_substrate * (Nlayers ** 0.5) * ((Ntracks ** b) / 2.0) * Pi_class * Pi_techno_substrate
    # calculates lambda_CS related to case & substrate
    lambda_CS = lambda0_CS * (gamma_TCy * Pi_TCy_case + C_ME * gamma_ME * Pi_ME + gamma_RH * Pi_RH + gamma_chemical * Pi_chemical)

    lambda_D1 = lambda_chip
    lambda_D2 = lambda_chip
    lambda_total_module = (lambda_D1 + lambda_D2 + lambda_wiring + lambda_CS)
    weighted = float(lambda_total_module * Pi_Induit_i * (Operating_Hours_per_Year / t_total))

    return weighted


# ===============================
# Main
# ===============================
def evaluate_rectifier_reliability(excel_filename):

    """Evaluate rectifier reliability."""
    print(f"Starting rectifier reliability evaluation with workbook: {excel_filename}", flush=True)
    print("\n*** Evaluation of rectifier reliability ***")

    # ===============================
    # CONFIG
    # ===============================
    input_sheet_name  = "Inputs"
    output_sheet_name = "Analysis_Results"
    parameter_sheet_name = "Parameters"  # LF _ 30/01/26
    option_sheet  = "options"                     # to enable / disable plots for instance
    thermal_sheet = "thermal_data"

    # ===============================
    # LOAD DATA
    # ===============================
    all_data = pd.read_excel(excel_filename, sheet_name=input_sheet_name, engine="openpyxl")
    num_rows = len(all_data)

    # Robust reading of the number of diodes in // (Parameters)
    try:
        params_df = pd.read_excel(excel_filename, sheet_name=parameter_sheet_name, engine="openpyxl")
        # Case 1: column named 'nb_parallel_diodes'
        if 'nb_parallel_diodes' in params_df.columns:
            nb_parallel_diodes = int(params_df['nb_parallel_diodes'].dropna().iloc[0])
        else:
            # Case 2: We take the first numerical value found
            vals = pd.to_numeric(params_df.select_dtypes(include=[np.number]).stack(), errors='coerce').dropna()
            nb_parallel_diodes = int(vals.iloc[0]) if len(vals) else 2
    except Exception:
        print("considered: nb_parallel_diodes =2")
        nb_parallel_diodes = 2  # default

    # ===============================
    # CONSTANTS
    # ===============================
    # --- Load all parameters from Excel ---
    params = load_parameters(excel_filename)
    options = load_parameters(excel_filename, option_sheet)

    # Convenient helper: get parameter with fallback
    def P(name, default=None):
        """Run p."""
        return params[name] if name in params else default

    # selection of desired plots
    plot_CDF_enabled                      = options['plot_CDF_en']

    # Constants loaded from Parameters sheet
    nb_parallel_diodes = int(P("nb_parallel_diodes", 2))
    Pi_PM_rectifier = P("Pi_PM_rectifier", 1.25)
    Pi_MCM_process = P("Pi_MCM_process", 1.35)
    Pi_process_rectifier = P("Pi_process_rectifier", 4)

    lambda_0TH_rectifier = P("lambda_0TH_rectifier", 0.1574)  # rectifier diode p136
    # ISOTOP package p135
    lambda_0TCycase_rectifier = P("lambda_0TCycase_rectifier", 0.013371)
    lambda_0TCysolder_joints_rectifier = P("lambda_0TCysolder_joints_rectifier", 0.066853)
    lambda_0RH_rectifier = P("lambda_0RH_rectifier", 0.487813)
    lambda_0Meca_rectifier = P("lambda_0Meca_rectifier", 0.001479)

    # Induced stress factors
    C_sensitivity = P("C_sensitivity", 6.3)
    Pi_placement = P("Pi_placement", 2.5)
    Pi_hardening = P("Pi_hardening", 1)

    # diode, conduction losses paramerters
    U_D_th_rectifier = P("U_D_th_rectifier", 0.85)
    R_D_rectifier = P("R_D_rectifier", 0.0013)
    R_JC = P("R_JC", 0.18) # Thermal resistance Junction-to-case (datasheet - per diode)
    # https://assets.danfoss.com/documents/latest/528120/AI498335341970en-000201.pdf

    R_th_heatsink = P("R_th_heatsink", 0.48)  # heatsink Rth calculated for one power module
    V_nominal = P("V_nominal", 1600)

    input_freq = P("input_freq", 50) # Hertz
    t_total = P("t_total", 8760)

    # Aging enhanced model parameters
    aging_C = P("aging_C", 302500)
    aging_Ea = P("aging_Ea", 9.89e-20)
    aging_alpha = P("aging_alpha", -5.03)
    aging_Kb = P("aging_Kb", 1.38e-23)
    beta_age = P("aging_beta", 2.5)

    # Topology
    num_identical_Modules = nb_parallel_diodes * 3   # NUMBER OF IDENTICAL DIODE MODULES IN THE SYSTEM
    total_diodes = 2 * num_identical_Modules

    # ===============================
    # THERMAL MODEL FITTING
    # ===============================
    time_data = np.array([
        0.0012, 0.0013, 0.0016, 0.002, 0.003, 0.004, 0.0053, 0.0063, 0.0082, 0.0091,
        0.0124, 0.0158, 0.0188, 0.0216, 0.0256, 0.0337, 0.042, 0.0504, 0.0641, 0.0773,
        0.0874, 0.0903, 0.1065, 0.1118, 0.1326, 0.1436, 0.1776, 0.2136, 0.2276, 0.2324,
        0.3273, 0.3553, 0.3707, 0.4789, 0.604, 0.686, 1.1566, 1.8568, 1.5231, 2.7746,
        3.8074, 4.3155, 6.1716, 9.0771, 14.728, 22.326, 34.381, 52.048, 80.046, 99.434
    ])
    Zth_data = np.array([
        0.0051, 0.0063, 0.0081, 0.0107, 0.0127, 0.0144, 0.0173, 0.0191, 0.0223, 0.0231,
        0.0283, 0.0328, 0.0358, 0.0446, 0.046, 0.0503, 0.0554, 0.0611, 0.0634, 0.0777,
        0.0824, 0.0832, 0.0909, 0.0924, 0.0995, 0.1038, 0.1143, 0.1238, 0.1255, 0.1277,
        0.1424, 0.1453, 0.1508, 0.1606, 0.1749, 0.1716, 0.1801, 0.1805, 0.1803, 0.1811,
        0.1803, 0.1805, 0.1803, 0.181, 0.1808, 0.1808, 0.1808, 0.1808, 0.1808, 0.1808
    ])
    R_fit, tau_fit, C_fit = fitFosterModel(time_data, Zth_data)

    # ===============================
    # FIND MISSION PROFILES
    # ===============================
    def is_num(x):
        """Run is num."""
        try:
            float(x)
            return True
        except:
            return False

    def calc_Lx_hours(degrad_level, calendar_time):
        """Calculate lx hours."""
        if Di == 0:
            lifetime_hours = np.inf
        else:
            lifetime_hours = (calendar_time / degrad_level)  # expected lifetime under these conditions: (ref duration)/degradation level
        return lifetime_hours

    # <might be factorized with other tools>
    def write_aggregated_thermal_sheet(
            df: pd.DataFrame,
            filepath: str,
            sheet_name: str = "thermal_data",
            include_index: bool = False,
    ):
        """
        Overwrite (replace) a specific sheet within an existing Excel file, or create it if the file doesn't exist.
        Other sheets are preserved. [error if Excel file does not exist]
        """
        # Open in append mode and replace only the target sheet
        # with pd.ExcelWriter(
        #         filepath,
        #         engine="openpyxl",
        #         mode="a",
        #         if_sheet_exists="replace",
        # ) as writer:
        #     df.to_excel(
        #         writer,
        #         sheet_name=sheet_name,
        #         index=include_index,
        #         header=True,
        #         startrow=0,
        #     )
        # Open in append mode and replace only the target sheet
        writer = pd.ExcelWriter(filepath, engine='openpyxl', mode="a", if_sheet_exists="replace", )

        # write dataframe
        df.to_excel(
            writer,
            sheet_name=sheet_name,
            index=include_index,
            header=True,
            startrow=0,
        )

        # get book and sheet
        wb = writer.book
        ws = wb[sheet_name]
        # --- automatic adjustment of columns width
        for col in ws.columns:
            max_length = 0
            col_letter = col[0].column_letter
            for cell in col:
                try:
                    cell_value = str(cell.value)
                except:
                    cell_value = ""
                if len(cell_value) > max_length:
                    max_length = len(cell_value)
            adjusted_width = max_length + 2  # marge pour respirer
            ws.column_dimensions[col_letter].width = adjusted_width
        # --- centering of contents
        for row in ws.iter_rows():
            for cell in row:
                cell.alignment = Alignment(horizontal="center", vertical="center")

        # final save
        writer.close()

    profile_start_indices = all_data.index[ all_data["MP"].notna() & all_data["MP"].apply(is_num) ].to_numpy()
    num_profiles = len(profile_start_indices)
    profile_names = []
    all_cdf_results_system = []
    profile_summary_rows = []

    list_of_df = []  # list of mission profiles calculated by thermal simulation

    # ===============================
    # MAIN LOOP ON PROFILES
    # ===============================
    for i in range(num_profiles):

        start_row = profile_start_indices[i]
        profile_id = int(all_data.loc[start_row, "MP"])
        current_profile_name = f"Mission Profile {profile_id}"
        profile_names.append(current_profile_name)

        if i < num_profiles - 1:
            end_row = profile_start_indices[i + 1] - 2
        else:
            end_row = num_rows - 1

        profile_data = all_data.iloc[start_row + 1 : end_row + 1].reset_index(drop=True)

        print("\nprocessing: ", current_profile_name)

        if profile_data.empty:
            continue

        # Accumulators /  Initialize arrays for this profile to store corresponding results
        weighted_stress_sum_profile = 0.0
        total_hours_in_profile = 0.0
        sum_of_inverse_aging_eta_profile = 0.0
        sum_of_inverse_aging_eta2_profile = 0.0
        losses_MP = []

        # ---------- first pass : thermal simulation --------
        num_phases = len(profile_data)
        T_heatsink_arr = np.zeros(num_phases)
        T_J_comp_arr = np.zeros(num_phases)
        delta_T_aging_arr = np.zeros(num_phases)

        P_out_arr = np.zeros(num_phases) # to log calculated P_out
        Pavg_module_arr = np.zeros(num_phases) # losses per module
        P_rect_arr = np.zeros(num_phases) # total losses of rectifier

        for idx, row in profile_data.iterrows():

            Operating_Hours_per_Year = float(row["Operating_Hours_per_Year"])
            #P_out                    = float(row["P_out"])
            V_applied                = float(row["V_applied"])
            T_ambient_heatsink       = float(row["T_ambient_board"])

            # LF _ 12/03/2026
            # P_out & I_out calculated now from Rel_Speed & Rel_Torque
            Rel_speed = float(row["Rel_speed"])
            Rel_torque = float(row["Rel_torque"])
            P_out = calc_active_power(Rel_torque, Rel_speed)
            P_out_arr[idx] = P_out
            # debug
            if debug_thermal:
                print("calculated P_out:", P_out)

            # electrical losses
            V_dc = (3 * np.sqrt(2) * V_applied) / np.pi
            I_dc = 0.0 if V_dc == 0 else (P_out / V_dc)
            I_cond_diode = I_dc / nb_parallel_diodes  # current shared between parallel diodes
            # during diode conduction (lasts 1/3 of period)
            P_L_Diode = U_D_th_rectifier * I_cond_diode + R_D_rectifier * I_cond_diode**2 # during conduction

            # avg losses of module (2 diodes) during one cycle (2/3 * Pd)
            Pavg_module = (2.0/3.0) * P_L_Diode
            T_heatsink = T_ambient_heatsink + R_th_heatsink * Pavg_module

            Pavg_module_arr[idx] = Pavg_module

            #  Foster model pour aging ("short" thermal cycles due to rectification)
            t_period = 1.0 / input_freq
            t_on  = t_period / 3.0
            t_off = 2.0 * t_period / 3.0

            delta_T_for_aging, T_rise_mean, t_sim, P_waveform, T_junction = simulateDynamicThermalResponse(
                R_fit, tau_fit, P_L_Diode, 0.0, t_on, t_off
            )
            T_J_composant = T_heatsink + T_rise_mean # average junction temperature

            if SHOW_THERMAL_DEBUG and idx == 0:
                plot_thermal_cycle(t_sim, P_waveform, T_junction, t_on, t_off)

            # debug
            # add switch to enable/disable log
            if debug_thermal:
                print("T_heatsink:", T_heatsink)
                print("delta_T_for_aging:", delta_T_for_aging)
                print("T_rise_mean:", T_rise_mean)
                print("=> T_J_composant:", T_J_composant)

            T_heatsink_arr[idx] = T_heatsink           # heatsink temperature for each phase of mission profile
            T_J_comp_arr[idx] = T_J_composant          # avg junction temperature of component (diode)
            delta_T_aging_arr[idx] = delta_T_for_aging # "short" thermal cycles for lifetime model

            # for information only (not used)
            # 2 diodes per module / each diode conduct 1/3rd of time
            P_L_rectifier = (2 * num_identical_Modules) * (P_L_Diode / 3.0)  # total diodes * avg power per diode
            losses_MP.append(P_L_rectifier) # not used
            P_rect_arr[idx] = P_L_rectifier

        # Deltas interphases for "aging 2" (thermal cycles due to change of operating points: "long" thermal cycles)
        Delta_T_Heatsink = np.zeros(num_phases)
        Delta_T_J_comp = np.zeros(num_phases)
        T_j_mean = np.zeros(num_phases)
        # note: some rules must be respected to construct the mission profile (cycles are between successives phases, etc)
        # <to avoid negative values in calculations...>
        for j in range(num_phases - 1):
            Delta_T_Heatsink[j] = T_heatsink_arr[j] - T_heatsink_arr[j+1] #
            Delta_T_J_comp[j] = T_J_comp_arr[j] - T_J_comp_arr[j+1]       #
            T_j_mean[j] = T_J_comp_arr[j] - Delta_T_J_comp[j] / 2.0       #
        Delta_T_Heatsink[-1] = T_heatsink_arr[-1] # last element of Delta_T_Heatsink = last element of T_heatsink_arr
        Delta_T_J_comp[-1] = T_J_comp_arr[-1]
        T_j_mean[-1] = T_J_comp_arr[-1]

        # Estimation T_max_cycling
        T_max_cycling_calc = T_heatsink_arr.copy()
        T_max_cycling_calc[-1] = T_heatsink_arr[-1] + Delta_T_Heatsink[-1] / 2.0 # differs only by its last element

        # should save "component level" mission profile in thermal_result sheet
        # copy mission profile as input file + add columns: T_heatsink_arr, T_J_comp_arr, delta_T_aging_arr
        # Delta_T_Heatsink, Delta_T_J_comp, T_j_mean, T_max_cycling_calc
        # all mission profiles with added thermal info
        df = profile_data.copy()
        df_first_idx = profile_data.iloc[0].name  # index (name) of first line of dataframe

        # add elements to columns of dataframe (to store in thermal_data)
        df["T_heatsink_arr"]     = T_heatsink_arr   # (array of) heatsink temperatures
        df["T_J_comp_arr"]       = T_J_comp_arr
        df["delta_T_aging_arr"]  = delta_T_aging_arr
        df["Delta_T_Heatsink"]   = Delta_T_Heatsink
        df["Delta_T_J_comp"]     = Delta_T_J_comp
        df["T_j_mean"]           = T_j_mean
        df["T_max_cycling_calc"] = T_max_cycling_calc

        # for debug
        df["P_out"] = P_out_arr
        df["Pavg_module"] = Pavg_module_arr
        df["P_rectifier"] = P_rect_arr

        # missing number of "short cycles" (at Fin frequency)

        list_of_df.append((i, df))

        # ---------- 2nd pass : FIDES & aging ----------
        DA = 0  # total damage accumulation
        #total_inverse_life = 0  # sum of (Operating_Hours_per_Year / Lx_hours) for all the segments

        for idx, row in profile_data.iterrows():
            Operating_Hours_per_Year = float(row["Operating_Hours_per_Year"])
            V_applied                = float(row["V_applied"])
            N_Cy                     = float(row["N_Cy"])
            Theta_cy                 = float(row["Theta_cy"])
            G_RMS_val                = float(row["G_RMS_val"])
            RH_ambient               = float(row["RH_ambient"])
            T_ambient_board          = float(row["T_ambient_board"])
            Pi_application_i         = float(row["Pi_application_i"])
            Operating_Phase          = to_bool_excel(row["Operating_Phase"])
            # NB: no usage of Is_Signal_Diode_under_1A in curent data: considered False
            Is_Signal_Diode_under_1A = False

            if USING_MCM == 0:
                # packaged diode path (MATLAB) - calculation of reliability of one diode (not the full power module)
                weighted_stress_sum_profile += packaged_diode_phase_lambda(
                    T_J_composant_C=T_J_comp_arr[idx], T_heatsink_C=T_heatsink_arr[idx],
                    Operating_Hours_per_Year=Operating_Hours_per_Year, V_applied=V_applied, N_Cy=N_Cy,
                    Theta_cy=Theta_cy, G_RMS_val=G_RMS_val, RH_ambient=RH_ambient,
                    T_ambient_board_C=T_ambient_board, Pi_application_i=Pi_application_i,
                    Operating_Phase_bool=Operating_Phase, Is_Signal_Diode_under_1A_bool=Is_Signal_Diode_under_1A,
                    Delta_T_Heatsink_C=Delta_T_Heatsink[idx], T_max_cycling_C=T_max_cycling_calc[idx],
                    lambda_0TH_rectifier=lambda_0TH_rectifier, lambda_0TCycase_rectifier=lambda_0TCycase_rectifier,
                    lambda_0TCysolder_joints_rectifier=lambda_0TCysolder_joints_rectifier,
                    lambda_0RH_rectifier=lambda_0RH_rectifier, lambda_0Meca_rectifier=lambda_0Meca_rectifier,
                    V_nominal=V_nominal, Pi_placement=Pi_placement, Pi_hardening=Pi_hardening,
                    C_sensitivity=C_sensitivity, t_total=t_total
                )
            else:
                # calculation of reliability of one power module described as MCM (multi-chip module)
                weighted_stress_sum_profile += MCM_diode_phase_lambda(
                    T_J_comp_C=T_J_comp_arr[idx], T_heatsink_C=T_heatsink_arr[idx],
                    Operating_Hours_per_Year=Operating_Hours_per_Year, V_applied=V_applied, N_Cy=N_Cy,
                    G_RMS_val=G_RMS_val, RH_ambient=RH_ambient, Pi_application_i=Pi_application_i,
                    Operating_Phase_bool=Operating_Phase, Is_Signal_Diode_under_1A_bool=Is_Signal_Diode_under_1A,
                    Delta_T_cycling_C=Delta_T_Heatsink[idx], T_max_cycling_C=T_max_cycling_calc[idx],
                    V_nominal=V_nominal, Pi_placement=Pi_placement, Pi_hardening=Pi_hardening, t_total=t_total
                )

            total_hours_in_profile += Operating_Hours_per_Year

            # Aging model
            # number of short cycles (input frequency)
            N_Cy_aging = input_freq * Operating_Hours_per_Year * 3600.0

            if USE_ENHANCED_AGING_MODEL:
                # Nf = C * exp(Ea/(Kb*(Tj+273.15))) * (DeltaT)^alpha
                def Nf(delta_T, Tj_C):
                    """Run nf."""
                    delta_T=max(delta_T, 1e-3) # clamp to a small value (0 not acceptable)
                    return aging_C * np.exp(aging_Ea / (aging_Kb * (Tj_C + 273.15))) * (delta_T ** aging_alpha)
                # considering "short cycles" - many cycles , short amplitude
                Nb_cycles_to_failure = Nf(delta_T_aging_arr[idx], T_j_mean[idx])

                # considering the (longer) cycles due to change of phase - less cycles, large amplitude
                Nb_cycles_to_failure_2 = Nf(Delta_T_J_comp[idx], T_j_mean[idx])
            else:
                # Legacy (previous version)
                # considering "short cycles"
                if delta_T_aging_arr[idx] <= 0:
                    Nb_cycles_to_failure = math.inf
                else:
                    Nb_cycles_to_failure = (delta_T_aging_arr[idx] ** -5.0) * 10.0 ** 15.15

                # considering the cycles due to change of phase (based on  Delta_T_J inter-phases )
                if Delta_T_J_comp[idx] <= 0:
                    Nb_cycles_to_failure_2 = math.inf
                else:
                    Nb_cycles_to_failure_2 = (Delta_T_J_comp[idx] ** -5.0) * 10.0 ** 15.15

            # damage calculation : contribution of short cycles
            Di = N_Cy_aging / Nb_cycles_to_failure  # N_i / Nfi : number of thermal cycles during ti (duration of segment i)

            # damage accumulation
            DA = DA + Di  # once DA=1 lifetime is supposed to be finished
            Lx1_hours = calc_Lx_hours(Di, Operating_Hours_per_Year) # expected lifetime under these conditions

            # damage calculation : contribution of change of phase
            Di = N_Cy / Nb_cycles_to_failure_2  # number of thermal cycles during ti (duration of segment i)

            # damage accumulation
            DA = DA + Di  # once DA=1 lifetime is supposed to be finished
            Lx2_hours = calc_Lx_hours(Di, Operating_Hours_per_Year)  # expected lifetime under these conditions


        # global lifetime calculation

        Lifetime_hours = 8760 * (1 / DA)
        Lifetime_years = Lifetime_hours / (365 * 24) # convert in years (considering 8760 h/year)

        # ===============================
        # PROFILE LEVEL RESULTS
        # ===============================
        # Random failure rate (lambda) + process
        if USING_MCM:
            lambda_constant_profile = weighted_stress_sum_profile * Pi_MCM_process * Pi_process_rectifier
            lambda_constant_profile = lambda_constant_profile / 2  # equivalent for a packaged diode (2 diode per module)
        else:
            # using packaged diode model
            lambda_constant_profile = weighted_stress_sum_profile * Pi_PM_rectifier * Pi_process_rectifier

        # Aging of a single diode
        eta_aging_single_diode_hours  = Lifetime_hours

        # random (beta=1)
        mttf_single_diode = (1e9 / lambda_constant_profile) if lambda_constant_profile > 0 else math.inf
        mttf_system       = mttf_single_diode / (num_identical_Modules * 2.0)  # 2 diodes per module
        scale_random_system_years = (mttf_system / t_total) if np.isfinite(mttf_system) else math.inf
        beta_rand = 1.0

        # Aging (beta configurable: 2.2, 2.5 ...)
        # beta_age = 2.5
        beta_age = P("aging_beta", 2.5)
        # 2 diodes per module
        denom_pop = (num_identical_Modules * 2.0) ** (1.0 / beta_age)
        eta_aging_system_hours  = (eta_aging_single_diode_hours  / denom_pop) if np.isfinite(eta_aging_single_diode_hours) else math.inf

        scale_aging_system_years  = (eta_aging_system_hours  / t_total) if np.isfinite(eta_aging_system_hours) else math.inf


        # debug summary
        print("\nSummary for this mission profile:")
        print("failure rate rectifier (in FIT):", lambda_constant_profile * (num_identical_Modules * 2.0))
        print("mttf_rectifier in years:", scale_random_system_years)
        print("lifetime rectifier (wearout) in years:", scale_aging_system_years)
        print("Lifetime in years (one diode)", Lifetime_years)

        # order of columns matters!
        profile_summary_rows.append([
            profile_id, current_profile_name,
            scale_random_system_years, beta_rand, # Random failure (sigma, year) , Random failure (beta)
            scale_aging_system_years, beta_age    # Wear-out failure (sigma, year) , Wear-out failure (beta)
        ])

        # ===============================
        # CDF
        # ===============================
        time_years = np.linspace(0, 20000000 / t_total, 1000)
        R_rand = np.exp(-lambda_constant_profile * (time_years * t_total) / 1e9)
        R_age  = np.exp(-((time_years * t_total) / max(eta_aging_single_diode_hours, 1e-30))**beta_age)
        R_sys  = (R_rand * R_age) ** (num_identical_Modules * 2.0)
        all_cdf_results_system.append(1.0 - R_sys)

    # ===============================
    # PLOTS & EXPORT
    # ===============================
    if plot_CDF_enabled:
        print("drawing requested graphs")
        Plot_CDFs(profile_names, time_years, all_cdf_results_system, max_time=30)

    profile_summary_df = pd.DataFrame(
        profile_summary_rows,
        columns=[
            "MP_ID", "Profile_Name",
            "Random failure (sigma, year)", "Random failure (beta)", # Scale_Random_System_years , Shape_Random_System
            "Wear-out failure (sigma, year)", "Wear-out failure (beta)"    # Scale_Aging_System_years , Shape_Aging_System
        ]
    )

    with pd.ExcelWriter(excel_filename, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        profile_summary_df.to_excel(writer, sheet_name=output_sheet_name, index=False)

    # ====================================================================================================================
    # add thermal data into excel file

    # Build the aggregated dataframe
    aggregated = []
    for mission_id, df in list_of_df:
        tmp = df.copy()
        tmp.insert(0, "mission_id", mission_id)  # keep the origin
        aggregated.append(tmp)

    aggregated_df = pd.concat(aggregated, ignore_index=True)

    # ---  Replace only the aggregated sheet; keep other sheets intact ---
    write_aggregated_thermal_sheet(aggregated_df, filepath=excel_filename, sheet_name="thermal_data")

    # calculate avg power (per mission profile)
    #aggregated_df['cap_bank_losses'] / aggregated_df['operating_phase']

    # note: MP field no filled - uses instead mission_id
    avg_power = (
        aggregated_df.loc[aggregated_df['Operating_Phase']]  # keep only True rows
        .groupby(aggregated_df['mission_id'].ffill())['P_rectifier']  # group by MP blocks (assign each row to the corresponding MP block)
        .mean() # computes average within each MP, using only valid rows
    )
    avg_power = (
        aggregated_df.loc[aggregated_df['Operating_Phase']]  # keep only True rows
        .groupby(aggregated_df['mission_id'])['P_rectifier']  # group by MP blocks (assign each row to the corresponding MP block)
        .mean() # computes average within each MP, using only valid rows
    )

    print("avg power: ", avg_power)



    # for mission_id, mission_df in list_of_df:
    #    append_df_to_excel(mission_df, filepath=excel_filename, sheet_name="thermal_data", mission_id=mission_id)

    # ===================================================================================================================
    print("evaluate_rectifier_reliability: finished!")

#if __name__ == "__main__":
#   evaluate_rectifier_reliability("../rect_data.xlsx")

if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) == 2:
        # Normal case: executed in module with Excel file path as argument
        excel_file = sys.argv[1]
    else:
        # IDE case: use the workbook stored next to this module
        from common import __version__
        excel_file = Path(__file__).resolve().parent / "data" / f"PELCA_Reliability_v{__version__}_Rectifier.xlsx"
        print(">>> Running from IDE, using:", excel_file)

    evaluate_rectifier_reliability(excel_file)
