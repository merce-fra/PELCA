# -*- coding: utf-8 -*-
"""\brief Evaluate inverter power module reliability and write PELCA-ready results to Excel.

This module is part of the PELCA reliability evaluator.
"""
from typing import Any

from openpyxl.styles import Alignment

from inverter_reliability.igbt_reliability.calculations.calc_op_point import calc_op_point, calc_op_points
#from inverter_reliability.igbt_reliability.utils.get_mission_profile import read_excel_to_dict
from common.excel_parameters import read_parameters
from inverter_reliability.igbt_reliability.utils.get_profiles import get_profiles, get_profile_data, display_profile_data_parameters
from inverter_reliability.igbt_reliability.utils.write_result import write_result
from inverter_reliability.igbt_reliability.utils.calc_PELCA_parameters import calc_Weibull_parameters_for_inverter

from inverter_reliability.igbt_reliability.components.DeviceParameters import DeviceParameters
from inverter_reliability.igbt_reliability.components.diode import Diode
from inverter_reliability.igbt_reliability.components.igbt import IGBT
from inverter_reliability.igbt_reliability.components.mcm1 import MCM_fit_rate_calc

from inverter_reliability.igbt_reliability.calculations.calc_Tj_values_IEC import calc_Tj_values_IEC
from inverter_reliability.igbt_reliability.calculations.calc_Tj_values_PWM import calc_Tj_values_PWM
#from inverter_reliability.igbt_reliability.calculations.check_Tj_estimations import check_Tj_estimations

from inverter_reliability.igbt_reliability.lifetime.AgeingModel import AgeingModel

import math

#from inverter_reliability.igbt_reliability.converter.converter import Converter

# ===============================
# Switches / Options
# ===============================
USING_MCM = 0                      # 0 => packaged diode/igbt, 1 => MCM  (no validated yet! much shorter MTBF...)                   [impact on MTBF]
USING_IEC = True                  # False: losses calculated using "PWM" level simulation / True: losses calculated using IEC formulas

# *******************************************************************************************************
def calc_thermal_stress(profile_data, params, reference_module_params, debug_log=False, log_losses=False, use_iec_temp=True,
                        plot_cond_currents_en=False,
                        display_sim_IEC=False,
                        display_sim_pwm=False):
    """
    determines the thermal stress of IGBT and DIODE of the inverter part for a given mission profile
    (using FIDES method)
    At present, the losses (and thus the temperatures) are calculated using two different methods: IEC, or "PWM" based.

    Parameters
    ----------
    profile_data : TYPE
        one mission profile
    params : TYPE
        parameters specified in Excel file
    reference_module_params:
        parameters of power module device (coef for losses calculations, ...)

    Returns
    -------

    df : dataframe
        updated profile_data with new columns (temperatures, deltaT ... as function of mission profile)
        :param reference_module_params: parameters of power module device
        :type profile_data: dataframe
        :param params: dictionary with main parameters
        :param log_losses: to print / plot debug information related to losses / temperature estimations
        :param debug_log: to print / plot debug information
        :param use_iec_temp: boolean True when using IEC method to calculate losses
    """

    df = profile_data.copy()
    df_first_idx = profile_data.iloc[0].name # index (name) of first line of dataframe

    # processing will add columns to returned profile_data:
    #
    # * related to case (heatsink) temperatures : Tc, delta_Tc_cycling, Tc_max_cycling
    #
    # * related to junction temperatures:
    #    * diode :
    #            Tj_D_iec, deltaT_D_iec, Tj_D_pwm, deltaT_D_pwm
    #            Tj_D_phase, deltaTj_D_phase, delta_Tj_D_cycling (variation due to change of phase)
    #    * igbt :
    #            Tj_Q_iec, deltaT_Q_iec, Tj_Q_pwm, deltaT_Q_pwm
    #            Tj_Q_phase, deltaTj_Q_phase, delta_Tj_Q_cycling (variation due to change of phase)
    # *  N_fout_cy : the number of "fout" cycles  (for lifetime calculation)

    # for each segment (phase) of mission profile:
    for i in range(len(profile_data)):

        if debug_log:
            # debug msg
            print(f"\nfit_rate_calc: processing segment {i} of mission profile")

        # *** get parameters for current segment of mission profile ***
        Operating_Phase_i =  profile_data['Operating_Phase'].to_numpy()[i]

        Rel_speed_i       =  profile_data['Rel_speed'].to_numpy()[i]
        # Rel_speed_i must not be too low
        if Rel_speed_i<0.01:
            if debug_log:
                print(f"fit_rate_calc: Rel_speed_i ({Rel_speed_i}) too small! Limited to 1%")
            Rel_speed_i=0.01 # limited to 1%

        Rel_torque_i      = profile_data['Rel_torque'].to_numpy()[i]
        delta_T_cycling_i = profile_data['delta_T_cycling'].to_numpy()[i]  # variation of ambient temperature    during a cycle within current phase
        T_max_cycling_i   = profile_data['T_max_cycling'].to_numpy()[i]    # maximum ambient temperature reached during a cycle ...

        T_i = profile_data['Tx'].to_numpy()[i] # ambient temperature for power modules (considered heat sink air flow temperature here)
        # => heat sink temperature will be calculated using this parameter (and function of total losses of a power module)

        N_cy_i            = profile_data['N_cy'].to_numpy()[i]            # N_annual_cy : number of cycles associated with each cycling phase over a year (cycles)
        theta_cy_i        = profile_data['theta_cy'].to_numpy()[i]        # cycle duration (hours)

        if not Operating_Phase_i:
            if debug_log:
                print("fit_rate_calc: this segment is not an operating phase")
            # no active deltaT of dies during that phase => no thermal simulation to do
            # Only the slow passive temperature variation parameters specified in mission profile
            # are considered (delta_T_cycling, T_max_cycling, N_cy).

            # every part is supposed to follow the ambient air temperature (and its variations)
            delta_Tc_cycling = delta_T_cycling_i   # easy to calculate in non-operating phase
            Tc_max_cycling   = T_max_cycling_i
            delta_Tj_D_cycling = delta_T_cycling_i #
            delta_Tj_Q_cycling = delta_T_cycling_i #

            # =================================================
            Tj_D_iec = Tj_D_pwm = T_i # passive cycling only
            Tj_Q_iec = Tj_Q_pwm = T_i
            # the variation of ambient air is affects also the dies
            deltaT_D_iec = deltaT_D_pwm = delta_T_cycling_i
            deltaT_Q_iec = deltaT_Q_pwm = delta_T_cycling_i

            T_h_iec = T_h_pwm = T_i   # heatsink temperature is also T_i
            # =================================================

            N_fout_cy = 0 # number of "short cycles" (fout cycles) for the current segment phase (per year)
            #number of "long cycles" : N_cy_i

            # no power in a non-operating phase
            semicond_powers_IEC = {
                "PL_on_T_HB": 0,
                "PL_on_D_HB": 0,
                "PL_sw_T_HB": 0,
                "PL_sw_D_HB": 0,
                "total_loss": 0
            }
            semicond_powers_pwm = {
                "PL_avg_Q": 0,
                "PL_avg_D": 0,
                "PL_on_T_HB": 0,
                "PL_on_D_HB": 0,
                "PL_sw_T_HB": 0,
                "PL_sw_D_HB": 0,
                "total_loss": 0
            }

            # operating point:
            active_Pout = 0
            Iout = 0
            PF = 1            # don't care
            Vout_rms = 0
        else:
            # operating phase

            # perform electro-thermal simulations (2 methods evaluated)
            # - one simple with coarse results: based on IEC formula for calculations of losses
            # - one more computing intensive with time based simulation to calculate the losses (more accurate)

            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # could determine operating point only once (but done in calc_Tj_values_IEC & calc_Tj_values_PWM)
            # done here for log (debug)
            Udc = params.get('Udc', 540)  # CDM DC link voltage <can be calculated>
            if Rel_speed_i < 0.01:
                Rel_speed_i = 0.01
            active_Pout, Iout, PF, Vout_rms = calc_op_point(Udc, Rel_speed_i, Rel_torque_i)
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

            # temperatures calculated by two methods: pwm & IEC
            # default method, using IEC formulas
            semicond_temperatures_IEC, semicond_powers_IEC = calc_Tj_values_IEC(params, reference_module_params, Rel_torque_i, Rel_speed_i,  T_i, display_sim=display_sim_IEC, plot_cond_currents_en=False, log_losses=log_losses) # life_ratio, load_factor
            # note: parameter plot_cond_currents_en not used
            # ===========================================================================
            Tj_D_iec     = semicond_temperatures_IEC["Tj_diode"] # diode junction temperature
            Tj_Q_iec     = semicond_temperatures_IEC["Tj_Q"]     # IGBT junction temperature
            deltaT_D_iec = semicond_temperatures_IEC["deltaT_D"] # variation of junction temperature of diode
            deltaT_Q_iec = semicond_temperatures_IEC["deltaT_Q"] #                                      IGBT
            T_h_iec      = semicond_temperatures_IEC["Th"]       # heatsink temperature (under power module)
            # ===========================================================================

            # calculation also using simulation at "pwm" level for comparison
            #  * determination of electrical constraints (output current, ...) function of operating point
            #  * determination of electric current within all devices for this operating point (electrical "simulation")
            #  * electro-thermal simulation (few iteration to converge to correct operating point)
            #       * determination of losses of components (time domain)
            #       * evaluation of thermal models (time domain)
            semicond_temperatures_pwm, semicond_powers_pwm = calc_Tj_values_PWM(params, reference_module_params,  Rel_torque_i, Rel_speed_i,  T_i,
                                                                                display_sim=display_sim_pwm,
                                                                                plot_cond_currents_en=plot_cond_currents_en,
                                                                                plot_tj_en=False,
                                                                                log_losses=log_losses) # life_ratio, load_factor
            Tj_D_pwm     = semicond_temperatures_pwm["Tj_diode"]
            Tj_Q_pwm     = semicond_temperatures_pwm["Tj_Q"]
            deltaT_D_pwm = semicond_temperatures_pwm["deltaT_D"]
            deltaT_Q_pwm = semicond_temperatures_pwm["deltaT_Q"]
            T_h_pwm      = semicond_temperatures_pwm["Th"]       # not used

            # estimation of number of 'fout' thermal cycles (at output voltage frequency...) <not needed actually for FIDES model, only for lifetime model>
            # as a simplification, can convert the whole segment in a number of cycles, at a given delta T

            # duration (in hours) of a thermal cycle at output frequency
            theta_fout_cy = (1/(Rel_speed_i * 50)) / 3600   # in hours considering nominal output frequency = 50 Hz

            # number of "short cycles" (fout cycles) for the current phase (per year)
            N_fout_cy     = (N_cy_i*theta_cy_i)/theta_fout_cy  # Operating_Hours_per_Year/T_out(in hours)
            #number of "long cycles" : N_cy_i

            #delta_Tc_cycling : for operating phase: should be the difference between Tc of this phase - Tc of prev phase
            # must explicit what prev phase is... (additional column to specify couples of phases?)
            # or order the phases as consecutive lines [current choice]
            delta_Tc_cycling   = delta_T_cycling_i # possibly wrong at present - just a placeholder
            delta_Tj_D_cycling = delta_T_cycling_i # "
            delta_Tj_Q_cycling = delta_T_cycling_i # "

            #Tc_max_cycling   : in FIDES profile, usually = Tc
            if use_iec_temp:
                Tc_max_cycling = T_h_iec # IEC considered here...
            else:
                Tc_max_cycling = T_h_pwm

        # add elements to columns of dataframe
        idx = i + df_first_idx

        # LF _ 06/03/2026 : reordering

        # log of temperatures calculated using IEC losses methods
        df.at[idx, "Tj_D_iec"] = Tj_D_iec
        df.at[idx, "Tj_Q_iec"] = Tj_Q_iec
        df.at[idx, "deltaT_D_iec"] = deltaT_D_iec
        df.at[idx, "deltaT_Q_iec"] = deltaT_Q_iec

        # if temperatures are calculated using "PWM" calculation of losses
        df.at[idx, "Tj_D_pwm"] =  Tj_D_pwm
        df.at[idx, "Tj_Q_pwm"] =  Tj_Q_pwm
        df.at[idx, "deltaT_D_pwm"] =  deltaT_D_pwm
        df.at[idx, "deltaT_Q_pwm"] =  deltaT_Q_pwm

        df.at[idx, "N_fout_cy"] = N_fout_cy # number of "fout" cycles (for lifetime calculation)

        # case temperature (depending on loss calculation model)
        # or store both values?
        if use_iec_temp:
            T_h  = T_h_iec
            Tj_D = Tj_D_iec
            Tj_Q = Tj_Q_iec
        else:
            T_h  = T_h_pwm
            Tj_D = Tj_D_pwm
            Tj_Q = Tj_Q_pwm

        df.at[idx, "Tc"] = T_h # case temperature = heatsink temperature

        # to rename delta_Tc_phase / delta_Tj_D_phase / delta_Tj_Q_phase ?
        df.at[
            idx, "delta_Tc_cycling"]   = delta_Tc_cycling    # variation of Tcase (heat sink temperature from phase to phase)
        df.at[
            idx, "delta_Tj_D_cycling"] = delta_Tj_D_cycling  # difference between delta_Tj_D_cycling and deltaTj_D_phase ?
        df.at[
            idx, "delta_Tj_Q_cycling"] = delta_Tj_Q_cycling  # difference between delta_Tj_Q_cycling and deltaTj_Q_phase ?

        df.at[idx, "Tc_max_cycling"] = Tc_max_cycling

        # note: deltaTj_D_phase = delta_Tj_D_cycling
        #       deltaTj_Q_phase = delta_Tj_Q_cycling

        # additional columns to handle deltaT due to cycles between phases
        # for diode
        df.at[idx, "deltaTj_D_phase"] =  delta_T_cycling_i # placeholder (value updated in another loop)
        df.at[idx, "Tj_D_phase"]      =  Tj_D
        # for IGBT
        df.at[idx, "deltaTj_Q_phase"] =  delta_T_cycling_i # placeholder (value updated in another loop)
        df.at[idx, "Tj_Q_phase"]      =  Tj_Q

        # log of losses (debug)
        if use_iec_temp:
            df.at[idx, "PL_on_T_HB"] = semicond_powers_IEC["PL_on_T_HB"]
            df.at[idx, "PL_on_D_HB"] = semicond_powers_IEC["PL_on_D_HB"]
            df.at[idx, "PL_sw_T_HB"] = semicond_powers_IEC["PL_sw_T_HB"]
            df.at[idx, "PL_sw_D_HB"] = semicond_powers_IEC["PL_sw_D_HB"]
            inverter_losses = semicond_powers_IEC["total_loss"]
            df.at[idx, "total_loss"] = inverter_losses
        else:
            #df.at[idx, "PL_avg_Q"]   = semicond_powers_pwm["PL_avg_Q"]
            #df.at[idx, "PL_avg_D"]   = semicond_powers_pwm["PL_avg_D"]
            df.at[idx, "PL_on_T_HB"] = semicond_powers_pwm["PL_on_T_HB"]
            df.at[idx, "PL_on_D_HB"] = semicond_powers_pwm["PL_on_D_HB"]
            df.at[idx, "PL_sw_T_HB"] = semicond_powers_pwm["PL_sw_T_HB"]
            df.at[idx, "PL_sw_D_HB"] = semicond_powers_pwm["PL_sw_D_HB"]
            inverter_losses = semicond_powers_pwm["total_loss"]
            df.at[idx, "total_loss"] = inverter_losses


        # increase of air flow temperature
        # F : air flow = 0,17 m3/s
        # Cv =  Isobaric volumetric heat capacity CP,v J*cm-3*K-1 = 0.00121  => 1210 J/(m^3*K)
        df.at[idx, "deltaTx_heatsink"]  = inverter_losses / (0.17 * 1210)

        # log of information related to operating point
        df.at[idx, "active_Pout"] = active_Pout
        df.at[idx, "Iout"] = Iout
        df.at[idx, "PF"] = PF
        df.at[idx, "Vout_rms"] = Vout_rms
        df.at[idx, "life_ratio"] = profile_data['Operating_Hours_per_Year'].to_numpy()[i] / 8760

    # add a correction loop of delta_TC_cycling...
    # phases are supposed ordered consecutively
    for i in range(len(profile_data)):
        idx = i + df_first_idx

        last_line = (i==len(profile_data)-1)
        if last_line:
            # if last line is active, normally it has no cycles (N_cy_i=0)  and no delta_Tc_cycling
            Operating_Phase_i =  profile_data['Operating_Phase'].to_numpy()[i]
            if Operating_Phase_i:
                df.at[idx, "delta_Tc_cycling"] = 0
                df.at[idx, "delta_Tj_D_cycling"] = 0
                df.at[idx, "delta_Tj_Q_cycling"] = 0

                df.at[idx, "deltaTj_D_phase"] = 0 # (continuous phase (no cycles))
                df.at[idx, "Tj_D_phase"] = 0
                df.at[idx, "deltaTj_Q_phase"] = 0
                df.at[idx, "Tj_Q_phase"] = 0
            else:
                # not an operative phase (only passive thermal cycles linked to Ta)
                df.at[idx, "deltaTj_D_phase"] = delta_T_cycling_i
                df.at[idx, "Tj_D_phase"] = T_i
                df.at[idx, "deltaTj_Q_phase"] = delta_T_cycling_i
                df.at[idx, "Tj_Q_phase"] = T_i

        else:
            if use_iec_temp:
                df.at[idx, "delta_Tc_cycling"]   = df.at[idx, "Tc"]   - df.at[idx+1, "Tc"]   # deltaTc due to cycling (between phases)
                df.at[idx, "delta_Tj_D_cycling"] = df.at[idx, "Tj_D_iec"] - df.at[idx+1, "Tj_D_iec"] # deltaTj " (diode)
                df.at[idx, "delta_Tj_Q_cycling"] = df.at[idx, "Tj_Q_iec"] - df.at[idx+1, "Tj_Q_iec"] # deltaTj " (igbt)

                df.at[idx, "deltaTj_D_phase"] = deltaTj_D_phase = df.at[idx, "Tj_D_iec"] - df.at[idx+1, "Tj_D_iec"] # deltaT due to cycle
                df.at[idx, "Tj_D_phase"] = df.at[idx+1, "Tj_D_iec"] + deltaTj_D_phase/2 # Tj average considered in middle of deltaTj_D_phase
                df.at[idx, "deltaTj_Q_phase"] = deltaTj_Q_phase = df.at[idx, "Tj_Q_iec"] - df.at[idx+1, "Tj_Q_iec"] # deltaT due to cycle
                df.at[idx, "Tj_Q_phase"] = df.at[idx+1, "Tj_Q_iec"] + deltaTj_Q_phase/2  # Tj average considered in middle of deltaTj_D_phase
            else:
                df.at[idx, "delta_Tc_cycling"] = df.at[idx, "Tc"] - df.at[
                    idx + 1, "Tc"]  # deltaTc due to cycling (between phases)
                df.at[idx, "delta_Tj_D_cycling"] = df.at[idx, "Tj_D_pwm"] - df.at[idx + 1, "Tj_D_pwm"]  # deltaTj " (diode)
                df.at[idx, "delta_Tj_Q_cycling"] = df.at[idx, "Tj_Q_pwm"] - df.at[idx + 1, "Tj_Q_pwm"]  # deltaTj " (igbt)

                df.at[idx, "deltaTj_D_phase"] = deltaTj_D_phase = df.at[idx, "Tj_D_pwm"] - df.at[
                    idx + 1, "Tj_D_pwm"]  # deltaT due to cycle
                df.at[idx, "Tj_D_phase"] = df.at[
                                               idx + 1, "Tj_D_pwm"] + deltaTj_D_phase / 2  # Tj average considered in middle of deltaTj_D_phase
                df.at[idx, "deltaTj_Q_phase"] = deltaTj_Q_phase = df.at[idx, "Tj_Q_pwm"] - df.at[
                    idx + 1, "Tj_Q_pwm"]  # deltaT due to cycle
                df.at[idx, "Tj_Q_phase"] = df.at[
                                               idx + 1, "Tj_Q_pwm"] + deltaTj_Q_phase / 2  # Tj average considered in middle of deltaTj_D_phase

    return df

import pandas as pd

def write_aggregated_thermal_sheet(
    df: pd.DataFrame,
    filepath: str,
    sheet_name: str = "thermal_data",
    include_index: bool = False,
):
    """
    Overwrite (replace) a specific sheet within an existing Excel file, or create it if the file doesn't exist.
    Other sheets are preserved. [error if Excel file does not exist]
    :param df: data frame to write in specified sheet
    :param filepath: filename of Excel file
    :param sheet_name: name of sheet to write (thermal_sheet)
    :param include_index: boolean to include or not an index (default: False)
    :return: nothing
    """
    # # Open in append mode and replace only the target sheet
    # with pd.ExcelWriter(
    #     filepath,
    #     engine="openpyxl",
    #     mode="a",
    #     if_sheet_exists="replace",
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

def create_thermal_data_sheet(excel_path, sheet_name, list_of_df: list[Any]):
    """
    Creates a sheet "sheet_name" in Excel file (excel_path) containing thermal data determined during reliability estimation
    :param excel_path: filename of Excel file
    :param sheet_name:
    :param list_of_df: list of dataframe to write in thermal_data sheet
    """
    # ====================================================================================================================
    # create a file containing the thermal data / or write in a dedicated sheet of main Excel file

    # Build the aggregated dataframe (optional if you only want per-mission sheets)
    aggregated = []
    for mission_id, df in list_of_df:
        tmp = df.copy()
        tmp.insert(0, "mission_id", mission_id)  # keep the origin
        aggregated.append(tmp)

    aggregated_df = pd.concat(aggregated, ignore_index=True)
    # thermal_excel_path = "thermal_results.xlsx"
    thermal_excel_path = excel_path

    # --- Option 1: Replace only the aggregated sheet; keep other sheets intact ---
    write_aggregated_thermal_sheet(aggregated_df, filepath=thermal_excel_path, sheet_name=sheet_name)

    # --- Option 2: Write/replace one sheet per mission without touching others ---
    # for mission_id, df in list_of_df:
    #     write_per_mission_sheet(df, filepath=thermal_excel_path, mission_id=mission_id, base_sheet_name="thermal")

    # for mission_id, mission_df in list_of_df:
    #    append_df_to_excel(mission_df, filepath=thermal_excel_path, sheet_name="thermal_data", mission_id=mission_id)

    # ===================================================================================================================

def calc_PELCA_parameters(nb_parallel_sw, lambda_HB_PM, Nb_modules,
                          eta_random, lifetime,
                          Lifetime_years_diode, Lifetime_years_igbt, debug_inv_reliab ):
    """

    :param nb_parallel_sw: number of switches in //
    :param lambda_HB_PM: reliability of one half-bridge power module
    :param Nb_modules: number of power modules
    :param eta_random: list to append parameter for PELCA (for whole inverter) <updated by this function>
    :param lifetime:   list to append parameter for PELCA (for whole inverter) <updated by this function>
    :param Lifetime_years_diode: calculated lifetime of a diode
    :param Lifetime_years_igbt:  calculated lifetime of an IGBT
    :param debug_inv_reliab:
    :return: eta_random : updated list
    :        lifetime   : update list
    """
    # determination of parameters for PELCA
    # ...
    # PELCA_params = calc_Weibull_parameters()

    # single half-bridge power module                     inverter (N x half bridge power modules)
    # --------------------------------------------------------------------------------------------
    # beta_random_HB_PM = 1                               beta_random_inv  = 1
    # eta_random_HB_PM  = 1 / lambda_random               eta_random_inv   = eta_random_HB_PM / N
    # beta_wearout_HB_PM = 3                              beta_wearout_inv = beta_wearout_PM
    # eta_wearout_HB_PM = Lx / (gamma(1+1/beta_wearout))  eta_wearout_inv  = Lx / (gamma(1+1/beta) * N**(1/beta_wearout))

    # early stage (default values - no data)
    beta_early = 0.6
    eta_early_years = 3424
    eta_early_system_years = eta_early_years / ((3*nb_parallel_sw) ** (1.0 / beta_early))
    scale_early_system_years = eta_early_system_years
    shape_early_system = beta_early

    # random failure (useful life)
    #beta_random_HB_PM = 1
    beta_random_inv   = 1                                               #

    mttf_random_single_HB = 1e9 /  lambda_HB_PM                         # mttf in hours ()
    eta_random_HB_PM  = mttf_random_single_HB / 8760                    # in years
    eta_random_inv    = eta_random_HB_PM / Nb_modules                   # for Nb_modules

    eta_random.append(eta_random_HB_PM) # add eta_random_HB_PM to eta_random list

    # wearout period
    beta_wearout = 3                                                    #

    # *** lifetime calculation ***
    # the system will be considered aged as soon as one of devices as reached wearout
    # (the earliest that fails determine lifetime)

    Lx = min(Lifetime_years_diode,Lifetime_years_igbt)                  # ? right way to determine lifetime ?
    lifetime.append(Lx)                  # add Lx to lifetime list
    if debug_inv_reliab:
        print("shortest lifetime (years) between IGBT & diode: ", Lx)

    #eta_wearout_HB_PM = Lx / (math.gamma(1+1/beta_wearout))             #

    # eta = Lx / (gamma(1+1/beta)) for a single power module
    # eta = Lx / (gamma(1+1/beta) * N**(1/beta)) for N modules => N=2 (//) * 3 (legs) = 6
    scaling_factor = 1/(math.gamma(1 + 1/beta_wearout) * (3*nb_parallel_sw)**(1/beta_wearout))

    eta_wearout_inv = Lx * scaling_factor

    if debug_inv_reliab:
        print("\n*** PELCA parameters ***")
        # beta = shape / eta = scale
        print(f"shape_early_inv: {shape_early_system}; scale_early_inv_years: {scale_early_system_years};")
        print(f"beta_random: {beta_random_inv}; eta_random: {eta_random_inv};")
        print(f"beta_wearout: {beta_wearout}; eta_wearout: {eta_wearout_inv}\n")

    # for final report
    return eta_random, lifetime

# =================== utility to write result mission profile in Excel ===============================
# import os
# import pandas as pd
#
# # not used anymore
# def append_df_to_excel(
#     df: pd.DataFrame,
#     filepath: str,
#     sheet_name: str = "thermal_data",
#     mission_id: str | int | None = None,
#     include_index: bool = False,
# ):
#     """
#     Adds a DataFrame to the end of an Excel worksheet.
#     - Creates the file/worksheet if necessary.
#     - Writes the header only if the worksheet is empty.
#     - Adds a 'mission_id' column if provided.
#     """
#     # Optional: Add a column to plot the source mission
#     if mission_id is not None:
#         df_to_write = df.copy()
#         df_to_write.insert(0, "mission_id", mission_id)
#     else:
#         df_to_write = df
#
#     # if the file does not exist yet : direct creation with header
#     if not os.path.exists(filepath):
#         with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
#             df_to_write.to_excel(
#                 writer,
#                 sheet_name=sheet_name,
#                 index=include_index,
#                 header=True,
#                 startrow=0,
#             )
#         return
#
#     # the file exists : we open in append mode
#     with pd.ExcelWriter(
#         filepath,
#         engine="openpyxl",
#         mode="a",
#         if_sheet_exists="overlay",  # do not overwrite sheet
#     ) as writer:
#         # Try to recover the existing sheet
#         wb = writer.book
#         if sheet_name in wb.sheetnames:
#             ws = wb[sheet_name]
#             # openpyxl counts the lines up to the last non-empty one
#             existing_rows = ws.max_row or 0
#             is_empty = existing_rows in (0, 1) and ws.max_column == 1 and ws["A1"].value in (None, "")
#             # If the sheet is completely empty, we reset startrow=0 and header=True.
#             if is_empty:
#                 startrow = 0
#                 write_header = True
#             else:
#                 startrow = existing_rows  # we write just below
#                 write_header = False      # header already present
#         else:
#             # The sheet does not exist in the file: it will be created
#             startrow = 0
#             write_header = True
#
#         df_to_write.to_excel(
#             writer,
#             sheet_name=sheet_name,
#             index=include_index,
#             header=write_header,
#             startrow=startrow,
#         )
#
#
# # not used anymore
# def write_per_mission_sheet(
#     df: pd.DataFrame,
#     filepath: str,
#     mission_id: str | int,
#     base_sheet_name: str = "thermal",
#     include_index: bool = False,
# ):
#     """
#     Write one sheet per mission. If the mission sheet already exists, replace only that sheet.
#     Does not remove other sheets.
#     """
#     sheet_name = f"{base_sheet_name}_{mission_id}"
#
#     # Append mode allows keeping existing sheets; we replace only this mission's sheet
#     with pd.ExcelWriter(
#         filepath,
#         engine="openpyxl",
#         mode="a",
#         if_sheet_exists="replace",
#     ) as writer:
#         df.to_excel(
#             writer,
#             sheet_name=sheet_name,
#             index=include_index,
#             header=True,
#             startrow=0,
#         )

# note: a similar function exists in ELcapacitorFIDES.py (not compatible at present)
import numpy as np
import matplotlib.pyplot as plt
def plot_new_mission_profiles(mission_profile_ID, num_profiles, profile_start_indices, all_data, width_var='life_ratio', height_var='Tx', label_var='PN'):
    # purpose: display the different mission profiles present in all_data
    # loop through all mission profiles:
    """Plot new mission profiles results."""
    for profile_number in range(num_profiles):
        # get one mission profile
        profile_data = get_profile_data(profile_number, mission_profile_ID, profile_start_indices, all_data)

        widths = list(profile_data['Operating_Hours_per_Year'].to_numpy() /8760) # life_ratio
        heights = profile_data[height_var].to_numpy()

        Rel_speed_vec = profile_data['Rel_speed'].to_numpy()
        Rel_Torque_vec = profile_data['Rel_torque'].to_numpy()
        Pout, Iout, PF, Vout_rms = calc_op_points(540, Rel_speed_vec, Rel_Torque_vec)
        annotations = Pout # active_Pout
        life_labels = [f"{float(widths[k]):.2f}" for k in range(len(profile_data))]

        # Place bars consecutively
        # first MP: widths[:-1] = [0.11, 0.4, 0.06]
        positions = np.cumsum([0] + widths[:-1]) # first MP: [0. 0.11 0.51 0.57] {ndarray: (4,)}

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(positions, heights, width=widths, align='edge', color='skyblue', edgecolor='black')

        # Ajouter le label au-dessus de chaque barre (ex: PN)
        for bar, annotation in zip(bars, annotations):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height + 1, f'{label_var}={annotation}', ha='center',
                    va='bottom')

        # Ajouter les valeurs de width_var (ex: life_ratio) sous chaque barre
        ax.set_xticks([bar.get_x() + bar.get_width() / 2 for bar in bars])
        ax.set_xticklabels(life_labels) # life_ratio values
        ax.set_xlabel(f"{width_var} (largeur ∝ {width_var})")
        ax.set_ylabel(f"{height_var}")
        ax.set_title(f"Profile {profile_number} : {height_var} vs segments (width ∝ {width_var}, label = {label_var})")
        ax.grid(True, axis='y', linestyle='--', alpha=0.5)

        plt.tight_layout()
        plt.show()

# =========================================================================================
def evaluate_inverter_reliability(excel_path, debug_inv_reliab=False, debug_log=False, disp_profile=False):
    """
    Main function to evaluate inverter reliability
    :param excel_path: associated Excel file name
    :param debug_inv_reliab: boolean to enable/disable debug information
    :return: nothing
    """

    print(f"Starting inverter reliability evaluation with workbook: {excel_path}", flush=True)

    param_sheet   = 'parameters'                  # Sheet where parameters are stored
    result_sheet  = 'results'                     # Sheet where results are written
    option_sheet  = 'options'                     # to enable / disable plots for instance
    thermal_sheet = 'thermal_data'

    params  = read_parameters(excel_path, param_sheet)           # build dictionary with parameters

    options = read_parameters(excel_path, option_sheet)

    # selection of desired plots
    plot_CDF_enabled                      = options['plot_CDF_en']
    plot_bathtub_enabled                  = options['plot_bathtub_en']
    plot_lifetime_mission_profile_enabled = options['plot_lifetime_mission_profile_en']
    plot_mission_profile_enabled          = options['plot_mission_profile_en']

    plot_cond_currents_en = options['plot_cond_currents_en']
    display_sim_IEC = options['display_sim_IEC']
    display_sim_pwm = options['display_sim_pwm']

    # add information to params
    params["excel_path"]  = excel_path
    params["param_sheet"] = param_sheet

    # configuration / modularity of inverter stage : number of HB power modules in // per phase
    nb_parallel_sw = params['nb_parallel_sw']  # nb_parallel_sw=1 or 2 typically
    Nb_modules = 3*nb_parallel_sw # number of half-bridge power modules composing the three-phase inverter

    # topology dependent parameters
    # depending on number of power modules in parallel the current
    # flowing in diodes and IGBT is divided or not.
    current_ratio = 1 / nb_parallel_sw

    # add information to params
    params["current_ratio"] = current_ratio

    # not used
    # converter_gpi = Converter(
    #     name="REFERENCE_CONVERTER",
    #     power_range=(245, 1209),
    #     torque_points_output={25: 0.39, 50: 0.56, 75: 0.77, 100: 1.0},
    #     torque_points_displacement={25: 0.57, 50: 0.78, 75: 0.85, 100: 0.87}
    # )


    reference_module_params = DeviceParameters(params) # component parameters to enable calculation of losses (conduction & switching)

    # <or a reference_module composed of two diodes & 2 IGBTs ... >
    # one diode of reference_module / one IGBT of reference_module
    reference_module_diode  = Diode(device_params=reference_module_params) # PowerSemi with specific lambda0_TH (for FIDES model)
    reference_module_igbt   = IGBT(device_params=reference_module_params)  # "


    # get (all) mission profiles (keeping variable names)
    mission_profile_ID, num_profiles, profile_start_indices, all_data = get_profiles(excel_path, 'mission_profile')


    lifetime = []       # list for final report (1 line per mission profile)
    eta_random = []     # "

    list_of_df = []     # list of mission profiles calculated by calc_thermal_stress

    # *** mission profile loop ***

    for i in range(num_profiles): # num_profiles

        if debug_inv_reliab:
            print(f"processing mission profile : {i+1}")

        # get one mission profile
        profile_data = get_profile_data(i, mission_profile_ID, profile_start_indices, all_data)

        # *****************************************************************************************

        if disp_profile:
            # display contents of profile_data (debug)
            print(f"\n\ndisplay_profile_parameters (of selected profile_data) {i+1}")
            display_profile_data_parameters(profile_data)

        # --------------------------------------------------------
        # determination of temperatures for the whole profile_data
        # --------------------------------------------------------
        df = calc_thermal_stress(profile_data, params, reference_module_params,
                                 debug_log=False,
                                 log_losses=False,
                                 use_iec_temp=USING_IEC,
                                 plot_cond_currents_en=plot_cond_currents_en,
                                 display_sim_IEC=display_sim_IEC,
                                 display_sim_pwm=display_sim_pwm)
        # <should write the new dataframe in another Excel sheet - thermal...; add also total power info?>
        # output power / calculated inverter losses  /
        # reliability calculations can be performed from there without requirement for new thermal simulation

        # list of all mission profiles with added thermal info
        list_of_df.append((i, df))

        # ---------------------------------------------------------
        # determination of reliability of power modules / inverter
        # ---------------------------------------------------------
        # should specify which losses calculation method is selected for reliability calculation (IEC or PWM)
        if USING_MCM==0:
            # ============================================================================================
            # calculation of random reliability [requires the Tjm, deltaT calculated from mission profile]
            # methods to calculate lambda differ slightly between IGBT & diode
            # <using "packaged models" of diode & igbt>
            if debug_log:
                print("\n\ndetermine fit rate of diode")
            lambda_D = reference_module_diode.calc_lambda(df, params, debug_log=debug_log, use_iec_temp=USING_IEC) # in FIT (i.e. failures per billion hours)
            #diode_FITrate = 1/(diode_MTTF/1e9)

            if debug_log:
                print("\n\ndetermine fit rate of igbt")
            lambda_Q = reference_module_igbt.calc_lambda(df, params, debug_log=debug_log, use_iec_temp=USING_IEC) #
            #igbt_FITrate  = 1/(igbt_MTTF/1e9)

            if debug_inv_reliab:
                print(f"lambda_D: {lambda_D} FIT")
                print(f"lambda_Q: {lambda_Q} FIT")

            # random
            # aggregation of results for module
            # fit rate of one HB power module: 2 diodes / 2 IGBTs per module
            lambda_HB_PM = (2*lambda_D + 2*lambda_Q)

            # aggregation of results for inverter
            # fit rate of complete inverter stage : 3 (legs) x nb_parallel_sw
            lambda_total = (3*nb_parallel_sw) * lambda_HB_PM
            # ============================================================================================
        else:
            # using MCM of power module
            lambda_HB_PM = MCM_fit_rate_calc(df, params, reference_module_params)
            lambda_total = (3*nb_parallel_sw) * lambda_HB_PM

        # ============================================================================================
        MTTF_total = (1/(lambda_total*1e-9))/8760 # in years

        if debug_inv_reliab:
            print(f"lambda_total = {lambda_total} FIT")
            print(f"MTTF_total = {MTTF_total} years")

        # ----------------------
        # calculation of wearout
        # ----------------------
        if debug_inv_reliab:
            print("\n*** aging calculation ***")
        IGBT_LifetimeModel =  AgeingModel()
        #IGBT_LifetimeModel.plot_lifetime_graph()

        Diode_LifetimeModel =  AgeingModel()        # diode & igbt lifetime models might be different
        #Diode_LifetimeModel.plot_lifetime_graph()

        # assumption: considering that ageing of diode & igbt can be different
        # adjustment of constants of models can be required to better represent the
        # failure mechanism, ... alpha > 5 ... 7 (bonding dominent failure mode)  3 ... 5 (solder)?
        # adjustment of Ea 0.3 ... 0.7 eV

        Lifetime_years_diode = Diode_LifetimeModel.calc_wearout_mission_profile(df, 'diode', use_iec_temp=USING_IEC)
        Lifetime_years_igbt  = IGBT_LifetimeModel.calc_wearout_mission_profile(df, 'igbt', use_iec_temp=USING_IEC )

        if debug_inv_reliab:
            print("theoretical Lifetime_years_diode (for a single diode):", Lifetime_years_diode, " (years)")
            print("theoretical Lifetime_years_igbt (for a single IGBT):", Lifetime_years_igbt, " (years)")


        # ageing
        # system lifetime: min(Lifetime_years_diode,Lifetime_years_igbt) ?

        # ------------------------------
        # conversion in PELCA parameters
        # ------------------------------
        # Weibull functions parameters
        eta_random, lifetime = calc_PELCA_parameters(nb_parallel_sw, lambda_HB_PM, Nb_modules,
                                  eta_random, lifetime,
                                  Lifetime_years_diode, Lifetime_years_igbt, debug_inv_reliab )


        # ********************************************************************************************************

    # update Excel file with thermal data results
    create_thermal_data_sheet(excel_path, thermal_sheet, list_of_df)

    # determination of parameters for PELCA (specification of bathtub model for a replacement unit, i.e. the modules of inverter)
    if debug_inv_reliab:
         print("Calculation of parameters for PELCA (for the replacement unit, i.e. the inverter power modules\n")

    PELCA_params = calc_Weibull_parameters_for_inverter(params, lifetime, eta_random)

    # calculate avg power (per mission profile)
    print("Calculation of avg losses")
    i = 1
    for dataframe in list_of_df:
        avg_power = (
            dataframe[1][dataframe[1]['Operating_Phase']]
            ['total_loss']
            .mean()
        )
        print(f"Mission profile {i}, avg power: {avg_power}")
        i = i+1


    # update of result sheet
    if debug_inv_reliab:
        print("\nupdate of result sheet\n")
    write_result(params, excel_path, result_sheet, lifetime, PELCA_params)

    # **************
    # optional plots
    # **************
    from  capacitor_bank_reliability.evaluate_capacitor_bank_reliability import (plot_cdf,
                                                                        plot_bathtub_mission_profiles,
                                                                        plot_lifetime_mission_profile)

    if plot_CDF_enabled == 1 or plot_bathtub_enabled == 1 or plot_lifetime_mission_profile_enabled == 1 or plot_mission_profile_enabled == 1:
        print("drawing requested graphs")

    # plot CDFs
    if plot_CDF_enabled == 1:
        # neglecting (low) early failure rate
        #plot_cdf("inverter_reliability", lifetime, PELCA_params)

        # neglecting (low) early failure rate
        #max_duration = max(lifetime, [30.0] * len(lifetime)) # display at least 30 years
        max_duration = [30.0] * len(lifetime) # display 30 years
        plot_cdf("inverter_reliability", max_duration, PELCA_params)

    # plot hazard functions
    if plot_bathtub_enabled == 1:
        # * remark:
        # here the early failure rate is considered (fixed parameters in code)
        # => slightly impact cdf
        plot_bathtub_mission_profiles("inverter_reliability", lifetime, PELCA_params)

    # plot lifetime for the different mission profiles (lifetime of one capacitor - all capacitors supposed to age similarly)
    if plot_lifetime_mission_profile_enabled == 1:
        plot_lifetime_mission_profile("Shortest semiconductor", lifetime) # or power module?

    # plot a representation of the different mission profiles
    if plot_mission_profile_enabled == 1:
        plot_new_mission_profiles(mission_profile_ID, num_profiles, profile_start_indices, all_data, width_var='life_ratio', height_var='Tx', label_var='PN')

    print("evaluate_inverter_reliability: finished!")



# test# if __name__ == "__main__":
#     evaluate_inverter_reliability('../inv_data.xlsx')

if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) == 2:
        # Normal case: executed in module with Excel file path as argument
        excel_file = sys.argv[1]
    else:
        # IDE case: use the workbook stored next to this module
        from common import __version__
        excel_file = Path(__file__).resolve().parent / "data" / f"PELCA_Reliability_v{__version__}_Inverter.xlsx"
        print(">>> Running from IDE, using:", excel_file)

    evaluate_inverter_reliability(excel_file, debug_inv_reliab=True, debug_log=False, disp_profile=False)















