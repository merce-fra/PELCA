# -*- coding: utf-8 -*-
"""\brief Evaluate cooling fan reliability and write PELCA-ready results to Excel.

This module is part of the PELCA reliability evaluator.
"""
import os
# note: at present losses in fans are not considered (not needed here). It could be handled easily by considering
# constant losses during operation (under assumption that FANs is always at full speed).
# <FAN max absorbed power ~ 32.88 W (?) x 2 during operating phase> => < 70W
# https://www.fan-supplier.example/Download/Spec/FFB1424VHG-EP.pdf (similar FAN)

# Requires: pandas, numpy, matplotlib, openpyxl

import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from common.excel_parameters import read_parameters

# ===============================
# Switches / Options
# ===============================
#DISPLAY_CDF = True                      # False => no display, True => display CDF

# ======================================================================================================================
# <to be placed later in a utility file>
# debug / investigation
def calc_combined_cdf(all_cdf_results_system, all_overall_cdf_time, num_identical_fans ):
    """Calculate combined cdf."""
    if len(all_cdf_results_system) > 0:
        num_time_points = len(all_overall_cdf_time[0])
        F_avg = np.zeros(num_time_points)
        weight_per_profile = 1.0 / max(1, len(all_cdf_results_system))

        for cdf in all_cdf_results_system:
            F_avg += weight_per_profile * cdf

        plt.figure()
        plt.plot(all_overall_cdf_time[0], F_avg, 'k-', linewidth=2,
                 label=f'Combined CDF (Weighted Average - {int(num_identical_fans)} Fans)')
        plt.xlabel('Time (years)')
        plt.ylabel('Cumulative Failure Probability')
        plt.title(f'FANs: Combined CDF Across All Mission Profiles (Weighted Average - {int(num_identical_fans)} Fans)')
        plt.legend(loc='lower right')
        plt.grid(True)

# for debug only
def plot_BATHTUB_CURVE_single_fan_profile_1(all_lambda_constant_profile, all_eta_aging_hours, eta_early_years,beta_early, beta, t_total):
    # ---------------------- BATHTUB CURVE (single fan, profile 1) ----------------------
    """Plot b a t h t u b c u r v e single fan profile 1 results."""
    if len(all_lambda_constant_profile) > 0 and len(all_eta_aging_hours) > 0:
        time_hours = np.logspace(0, 5.5, 500)  # 1 to ~316,000 hours

        # Early stage (beta < 1)
        eta_early_hours = eta_early_years * t_total
        lambda_early = (beta_early / eta_early_hours) * (time_hours / eta_early_hours) ** (beta_early - 1.0)

        # Random stage (constant)
        lambda_random_per_hour = float(all_lambda_constant_profile[0]) / (10.0 ** 9)
        lambda_random = np.full_like(time_hours, lambda_random_per_hour)

        # Aging stage (beta > 1)
        eta_aging_single_fan_hours_1 = float(all_eta_aging_hours[0])
        lambda_aging = (beta / eta_aging_single_fan_hours_1) * (time_hours / eta_aging_single_fan_hours_1) ** (beta - 1.0)

        plt.figure()
        plt.loglog(time_hours, lambda_early, 'b-', linewidth=2, label='Early Stage (beta < 1)')
        plt.loglog(time_hours, lambda_random, 'g--', linewidth=2, label='Random Stage (beta = 1)')
        plt.loglog(time_hours, lambda_aging, 'r-', linewidth=2, label='Aging Stage (beta > 1)')
        plt.xlabel('Time (hours)')
        plt.ylabel('Failure Rate λ(t) (failures/hour)')
        plt.title('FANs: Weibull Bathtub Curve for a Single Fan (Profile 1)')
        plt.legend(loc='upper right')
        plt.grid(True, which='both')
        plt.show()
# ======================================================================================================================


# import os
# from pathlib import Path


def evaluate_fan_reliability(filename):


    # print(">>> cwd =", os.getcwd())
    # print(">>> arg filename =", filename)
    # print(">>> abspath(filename) =", os.path.abspath(filename))
    # print(">>> __file__ =", __file__)
    # print(">>> project_dir (parent of this package) =", Path(__file__).resolve().parents[1])
    #
    # try:
    #     options = read_parameters(filename, 'options')
    # except FileNotFoundError as e:
    #     print("!!! FileNotFoundError raised by read_parameters with argument:", filename)
    #     raise

    # filename = os.path.abspath(filename)

    # Load Excel data
    # (The SAME Excel file will be used for both input and output)

    # ---------------------- CONFIG ----------------------
    """Evaluate fan reliability."""
    excel_filename = filename
    input_sheet_name = 'mission_profile'
    output_sheet_name = 'results'
    parameter_sheet_name = 'Parameters'
    option_sheet = 'options'  # to enable / disable plots for instance

    print(f"Starting fan reliability evaluation with workbook: {excel_filename}", flush=True)
    print("*** evaluation of FAN reliability *** ")

    # ---------------------- CONSTANTS ----------------------
    # FIDES-like constants and settings (same as MATLAB)
    # <could possibly come from parameters in Excel file>
    gamma_Th = 0.51
    gamma_Tcy = 0.31
    gamma_M = 0.08
    gamma_Rh = 0.11
    lambda_0 = 0.17
    Pi_placement = 1.6  # to fill with table contents
    Pi_durcissement = 1 #
    C_sensibilite = 5.5
    t_total = 8760      #  hours/year (1 year)

    Pi_process = 4      #
    Pi_PM = 1.25
    Ea = 0.28           # eV
    beta = 2.2          # Weibull shape factor for fans (wear-out)
    m = 0.93


    # Early stage (infant mortality): no data available
    beta_early = 0.6
    eta_early_years = 3424



    # ---------------------- LOAD DATA ----------------------
    options = read_parameters(excel_filename, option_sheet)

    # selection of desired plots
    DISPLAY_CDF = options['plot_CDF_en']  # False => no display, True => display CDF

    # Read mission profile table
    all_data = pd.read_excel(excel_filename, sheet_name=input_sheet_name, engine='openpyxl')

    params = read_parameters(excel_filename, parameter_sheet_name)

    # Read number of identical fans from Parameters!B1
    # num_identical_fans = pd.read_excel(
    #     excel_filename, sheet_name=parameter_sheet_name,
    #     usecols='B', nrows=1, header=None, engine='openpyxl'
    # ).iloc[0, 0]

    num_identical_fans = params.get('num_identical_fans', 2) # default : 2 fans
    max_fan_power = params.get('max_fan_power', 32.88)

    # Enforce numeric for expected numeric columns (coerce errors to NaN where needed)
    numeric_cols = [
        'MP', 'B', 'V', 'T', 'Pi_type', 'Operating_Hours_per_Year', 'Pi_application',
        'RH_ambient', 'delta_T_cycling', 'T_max_cycling', 'N_cy', 'theta_cy', 'G_RMS'
    ]
    for col in numeric_cols:
        if col in all_data.columns:
            all_data[col] = pd.to_numeric(all_data[col], errors='coerce')

    num_rows = len(all_data)


    # Identify profile start rows: non-missing and numeric in MP column
    mp_series = all_data.get('MP', pd.Series([np.nan] * num_rows))
    mp_numeric_mask = (~mp_series.isna()) & (pd.to_numeric(mp_series, errors='coerce').notna())
    profile_start_indices = all_data.index[mp_numeric_mask].tolist()
    num_profiles = len(profile_start_indices)


    # ---------------------- STORAGE ----------------------
    profile_names = []
    all_lambda_constant_profile = []      # scalar per profile (failures per billion hours)
    all_lambda_aging_profile = []  # scalar per profile (failures per billion hours)
    all_cdf_results_system = []           # arrays for system CDF per profile
    all_overall_cdf_time = []             # time vector (years) per profile
    all_overall_cdf_values = []           # system CDF arrays per profile
    all_mttf_random_hours = np.zeros(num_profiles)  # per profile
    all_eta_aging_hours = np.zeros(num_profiles)    # per profile


    summary_rows = []


    # ---------------------- PER-PROFILE LOOP ----------------------
    for i in range(num_profiles):
        start_row = profile_start_indices[i]
        profile_id = mp_series.iloc[start_row]
        current_profile_name = f"Mission Profile {int(profile_id) if pd.notna(profile_id) else 'NA'}"
        profile_names.append(current_profile_name)

        # Determine end row (inclusive) like MATLAB: next start - 2, else end of data
        if i < num_profiles - 1:
            end_row = profile_start_indices[i + 1] - 2
        else:
            end_row = all_data.index[-1]

        # Slice rows immediately AFTER the marker row through end_row
        # (MATLAB used start_row+1 : end_row)
        # <start row contains just le identifier of MP>
        profile_data = all_data.loc[start_row + 1:end_row].copy()

        if profile_data.empty:
            # Still add an empty row with NaNs to keep lengths aligned if needed
            print(f"[WARN] {current_profile_name}: no data rows found between markers.")
            continue

        # Extract series (as numpy arrays) for calculations
        # Use .to_numpy(dtype=float) for vectorized operations
        B_i = profile_data['B'].to_numpy(dtype=float)
        V_i = profile_data['V'].to_numpy(dtype=float)
        T_i = profile_data['T'].to_numpy(dtype=float)
        Pi_type_i = profile_data['Pi_type'].to_numpy(dtype=float)
        Hours_per_Year_i = profile_data['Operating_Hours_per_Year'].to_numpy(dtype=float)
        Pi_application_i = profile_data['Pi_application'].to_numpy(dtype=float)
        RH_ambient_i = profile_data['RH_ambient'].to_numpy(dtype=float)
        delta_T_cycling_i = profile_data['delta_T_cycling'].to_numpy(dtype=float)
        T_max_cycling_i = profile_data['T_max_cycling'].to_numpy(dtype=float)
        N_cy_i = profile_data['N_cy'].to_numpy(dtype=float)
        theta_cy_i = profile_data['theta_cy'].to_numpy(dtype=float)
        G_RMS_i = profile_data['G_RMS'].to_numpy(dtype=float)
        operating_phase_i = profile_data['operating_phase'].to_numpy()
        operating_phase_i = operating_phase_i.astype(bool)
        # note: operating_time = sum of Hours_per_Year_i where operating_phase_i=true
        operating_time = np.sum(Hours_per_Year_i[operating_phase_i])

        # to specify the phases used for calculation of delta_T_cycling
        #phases = profile_data['phases'].to_numpy()
        #phase_i = int(phases[0].split("#")[0])
        #phase_j = int(phases[0].split("#")[1])

        # ----- Physical stress: transform T_i like MATLAB -----
        T_result_i = T_i.copy()
        mask1 = (T_i >= -40) & (T_i <= 16)
        mask2 = (T_i > 16) & (T_i <= 70)
        T_result_i[mask1] = 30
        T_result_i[mask2] = 1.1 * T_i[mask2] + 12.5
        T_i = T_result_i

        # ----- Thermal stress (Pi_Thermique) -----
        # exp(11604 * 0.15 * ((1 / 293) - (1 ./ (T_i + 273))))
        Pi_Thermique_i = np.where(operating_phase_i, gamma_Th * np.exp(11604 * 0.15 * ((1.0 / 293.0) - (1.0 / (T_i + 273.0)))), 0)

        # ----- Cyclic stress (Pi_Tcy) -----
        # gamma_Tcy * (12*N_cy/t_total) * (min(theta_cy,2)/2)^(1/3) * (delta_T/20)^1.9
        # * exp(1414*((1/313) - (1/(T_max+273))))
        theta_clip = np.minimum(theta_cy_i, 2.0)
        Pi_Tcy_i = (
            gamma_Tcy
            * (12.0 * N_cy_i / t_total)
            * (theta_clip / 2.0) ** (1.0 / 3.0)
            * (delta_T_cycling_i / 20.0) ** 1.9
            * np.exp(1414.0 * ((1.0 / 313.0) - (1.0 / (T_max_cycling_i + 273.0))))
        )

        # ----- Mechanical stress (Pi_Mecanique) -----
        Pi_Mecanique_i = gamma_M * (G_RMS_i / 0.5) ** 1.5

        # ----- Humidity stress (Pi_RH) -----
        Pi_RH_i = (
            gamma_Rh
            * (RH_ambient_i / 70.0) ** 4.4
            * np.exp(11604 * 0.8 * ((1.0 / 293.0) - (1.0 / (T_i + 273.0))))
        )

        # ----- Induced factor (scalar per profile) -----
        # (Pi_placement * Pi_application * Pi_durcissement)^(0.511 * log(C_sensibilite))
        # MATLAB log is natural log; numpy.log is also natural log.
        Pi_induit_i = (Pi_placement * Pi_application_i * Pi_durcissement) ** (
            0.511 * np.log(C_sensibilite)
        )
        Pi_induit_profile_scalar = float(np.nanmean(Pi_induit_i))

        # Weighted sum of stresses
        hours_frac = (Hours_per_Year_i / t_total)
        weighted_stress_sum_profile = float(
            np.nansum(hours_frac * (Pi_Thermique_i + Pi_Tcy_i + Pi_Mecanique_i + Pi_RH_i)) # (NaNs) treated as zero
        )

        # ----- Lambda_Physique & lambda_constant (per billion hours) -----
        lambda_Physique_profile = lambda_0 * 20.0 * weighted_stress_sum_profile * Pi_induit_profile_scalar
        lambda_constant_profile_per_billion_hours = lambda_Physique_profile * Pi_PM * Pi_process
        all_lambda_constant_profile.append(lambda_constant_profile_per_billion_hours)

        # ----- Wearout (aging) parameters -----
        # L10_i in hours:
        # 79200 * Pi_type * (3.53 - 0.744*log(B)) * exp((-Ea*11604)*(1/313 - 1/(T+273))) * (V/3000)^(-m)

        # Guard against invalid B_i (<=0) in log
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            logB = np.log(B_i)
        coeff = (3.53 - 0.744 * logB)
        Arrh = np.exp((-Ea * 11604.0) * (1.0 / 313.0 - 1.0 / (T_i + 273.0)))

        #rpm_term = (V_i / 3000.0) ** (-m)
        #rpm_term = np.where(V_i == 0, np.inf, (V_i / 3000.0) ** (-m))

        # infinite lifetime if V=0 <=> null degradation 1/L10_i = 0
        with np.errstate(divide='ignore', invalid='ignore'):
             rpm_term = (V_i / 3000.0) ** (-m)
             rpm_term[V_i == 0] = np.inf

        L10_i = 79200.0 * Pi_type_i * coeff * Arrh * rpm_term   # OL (operational life) p 247

        # Calendar life expectancy for profile (hours) via harmonic mean weighted by operating fraction
        # denom = np.sum(np.where(operating_phase_i, (Hours_per_Year_i / 8760.0) * (1.0 / L10_i), 0))
        # equivalent to:

        denom = np.nansum((Hours_per_Year_i / 8760.0) * (1.0 / L10_i)) # (NaNs) treated as zero
        if denom <= 0 or np.isnan(denom):
            L10_cal_profile = np.nan
        else:
            L10_cal_profile = 1.0 / denom

        # Mean Corrective Maintenance Time (MC) in hours
        MC_profile = L10_cal_profile * (6.5798 ** (1.0 / beta))

        # lambda_aging (failures per billion hours) # p 147
        lambda_aging_profile_per_billion_hours = 0.105 * (10.0 ** 9) * (
            (MC_profile ** (beta - 1.0)) / (L10_cal_profile ** beta)
        )
        all_lambda_aging_profile.append(lambda_aging_profile_per_billion_hours)

        # ----- Single fan parameters (hours) -----
        # Ensure scalar values (MATLAB indexed (1) but both are scalars here)
        mttf_random_single_fan_hours = (10.0 ** 9) / float(lambda_constant_profile_per_billion_hours)
        eta_aging_single_fan_hours = (10.0 ** 9) / float(lambda_aging_profile_per_billion_hours)

        all_mttf_random_hours[i] = mttf_random_single_fan_hours
        all_eta_aging_hours[i] = eta_aging_single_fan_hours

        # ----- System scaling -----
        # Early stage (years)
        eta_early_system_years = eta_early_years / (num_identical_fans ** (1.0 / beta_early))
        scale_early_system_years = eta_early_system_years # eta_early
        shape_early_system = beta_early                   # beta_early

        # Random stage
        mttf_random_system_hours = mttf_random_single_fan_hours / num_identical_fans
        scale_random_system_years = mttf_random_system_hours / t_total # eta_random
        shape_random_system = 1.0                                      # beta_random

        # Aging stage
        eta_aging_system_hours = eta_aging_single_fan_hours / (num_identical_fans ** (1.0 / beta))
        scale_aging_system_years = eta_aging_system_hours / t_total   # eta_wearout
        shape_aging_system = beta                                     # beta_wearout

        # ----- CDF calculation (system) -----
        time_max_hours_for_plot = 30*8760 # 30 years converted in hours
        time_years = np.linspace(0.0, time_max_hours_for_plot / t_total, 1000)

        # Reliability of a single fan (random * aging only)
        reliability_random_single_fan = np.exp(
            -float(lambda_constant_profile_per_billion_hours) * (time_years * t_total) / (10.0 ** 9)
        )
        reliability_aging_single_fan = np.exp(
            -((time_years * t_total) / eta_aging_single_fan_hours) ** beta
        )
        reliability_total_single_fan = reliability_random_single_fan * reliability_aging_single_fan

        # System reliability = R_single^N  -> system CDF = 1 - R_system
        reliability_system_for_profile_i = reliability_total_single_fan ** num_identical_fans
        cdf_system_i = 1.0 - reliability_system_for_profile_i

        all_cdf_results_system.append(cdf_system_i)
        all_overall_cdf_time.append(time_years)
        all_overall_cdf_values.append(cdf_system_i)

        # ----- Collect summary row -----
        # columns renamed according to PELCA format (order correct)
        summary_rows.append({
            'MP_ID': str(int(profile_id)) if pd.notna(profile_id) else '',
            'Profile_Name': current_profile_name,
            'Early failure (sigma, year)': scale_early_system_years,    # Early failure (sigma, year),
            'Early failure (beta)': shape_early_system,                 # Early failure (beta),
            'Random failure (sigma, year)': scale_random_system_years,  # Random failure (sigma, year),
            'Random failure (beta)': shape_random_system,               # Random failure (beta),
            'Wear-out failure (sigma, year)': scale_aging_system_years, # Wear-out failure (sigma, year),
            'Wear-out failure (beta)': shape_aging_system               # Wear-out failure (beta)
        })

        # next to develop: adapt to new format (values separated by # in same cell for simulations with several mission profiles)

        # Console display (like MATLAB disp)
        print(f"Mission Profile {int(profile_id) if pd.notna(profile_id) else 'NA'}")
        print(f"  System ({int(num_identical_fans)} Fans) - Early Scale:  {scale_early_system_years:.6g} years, Shape: {shape_early_system}")
        print(f"  System ({int(num_identical_fans)} Fans) - Random Scale: {scale_random_system_years:.6g} years, Shape: {shape_random_system}")
        print(f"  System ({int(num_identical_fans)} Fans) - Aging Scale:  {scale_aging_system_years:.6g} years, Shape: {shape_aging_system}")
        print("")


    # attempt...
    # ---------------------- COMBINED CDF (weighted average) ----------------------
    #calc_combined_cdf(all_cdf_results_system, all_overall_cdf_time, num_identical_fans)


    # **************
    # optional plots
    # **************
    if DISPLAY_CDF:
        print("drawing requested graph")
    # ---------------------- PER-PROFILE SYSTEM CDF PLOT ----------------------
    if DISPLAY_CDF: # note: equivalent to plot_CDF_enabled in capacitor and inverter (using different display function)
        if len(profile_names) > 0 and len(all_overall_cdf_values) == len(profile_names):
            plt.figure()
            colors = plt.cm.tab20(np.linspace(0, 1, len(profile_names)))
            for i, name in enumerate(profile_names):
                plt.plot(all_overall_cdf_time[i], all_overall_cdf_values[i],
                         linewidth=1.5, label=f"{name} ({int(num_identical_fans)} Fans)",
                         color=colors[i % len(colors)])
            plt.xlabel('Time (years)')
            plt.ylabel('Cumulative Failure Probability')
            plt.title(f'FANs: Comparison of Overall CDFs for All Mission Profiles (for {int(num_identical_fans)} Identical Fans)')
            plt.legend(loc='lower right')
            plt.grid(True)
            plt.show()

    # calculate avg power during operation
    # trivial here: FANs supposed to always consume the same power (full speed in operations)
    total_FANs_power = num_identical_fans * max_fan_power
    avg_FANs_power_during_operation  = total_FANs_power
    print("avg power in FANs during operation: ", avg_FANs_power_during_operation)

    # ---------------------- WRITE SUMMARY TO EXCEL ----------------------
    profile_summary_data = pd.DataFrame(summary_rows)
    with pd.ExcelWriter(excel_filename, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        profile_summary_data.to_excel(writer, sheet_name=output_sheet_name, index=False)

    print("evaluate_fan_reliability: finished!")

    # debug
    #plot_BATHTUB_CURVE_single_fan_profile_1(all_lambda_constant_profile, all_eta_aging_hours, eta_early_years,beta_early, beta, t_total)


# test
# if __name__ == "__main__":
#     filename = '../fan_data.xlsx' # that file must contain the structured table (mission profiles)
#     evaluate_fan_reliability(filename)

# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) < 2:
#         raise ValueError("Usage: python -m fan_reliability.evaluate_fan_reliability <excel_filename>")
#     evaluate_fan_reliability(sys.argv[1])

if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) == 2:
        # Normal case: executed in module with Excel file path as argument
        excel_file = sys.argv[1]
    else:
        # IDE case: use the workbook stored next to this module
        from common import __version__
        excel_file = Path(__file__).resolve().parent / "data" / f"PELCA_Reliability_v{__version__}_Fan.xlsx"
        print(">>> Running from IDE, using:", excel_file)

    evaluate_fan_reliability(excel_file)
