# -*- coding: utf-8 -*-
"""\brief Prototype inverter lifetime calculations for mission profiles.

This module is part of the PELCA reliability evaluator.
"""
from utils.get_mission_profile import read_excel_to_dict
from utils.read_parameters import read_parameters

from components.DeviceParameters import DeviceParameters
from components.diode import Diode
from components.igbt import IGBT

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# profiles contains the list of mission profiles (but name of variables are lost...)
# order of parameters must be defined
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# one usage in this file
def parse_mission_profiles(mission_profile_dict):
    """Convert mission profiles to numeric format."""
    def convert_to_number(value):
        """Convert to number."""
        if isinstance(value, (int, float)):
            return value
        try:
            return float(value.strip()) if '.' in str(value) else int(value.strip())
        except:
            return value

    profiles = []
    for block_number in range(1, 1 + len(mission_profile_dict)):
        # extraction of one mission profile
        block_data = mission_profile_dict[block_number]
        mission_profile = [
            [convert_to_number(v) for k, v in variables.items()
             if k.lower() not in ["mission profile", "mp"]]
            for variables in block_data.values()
        ]
        profiles.append(mission_profile)
    return profiles

import pandas as pd
# one usage in this file
def get_profiles(filename, sheet_name):
    # to load Excel data in a DataFrame
    """Read profiles."""
    all_data = pd.read_excel(filename, sheet_name) # no need to close excel file for that
    num_rows = len(all_data)

    # Find starting indices for each mission profile  (two formats...)
    # beginning of mission profiles (line indexes in all_data dataframe)
    if 'MP' in all_data.keys():
        mission_profile_ID = 'MP'
    else:
        mission_profile_ID = 'mission profile'

    profile_start_indices = all_data.index[all_data[mission_profile_ID].notna() &
                                                         pd.to_numeric(all_data[mission_profile_ID], errors='coerce').notna()]
    num_profiles = len(profile_start_indices) # number of profiles
    #print("num_profiles:", num_profiles)

    return mission_profile_ID, num_profiles, profile_start_indices, all_data

# mission_profile_ID, num_profiles, profile_start_indices, all_data = get_profiles(excel_path, 'mission_profile')

# one usage in this file
# two in cap_lifetime_using_excel_fides_model1.py
def get_profile_data(index_profile, mission_profile_ID, profile_start_indices, all_data):
    """Read profile data."""
    num_rows = len(all_data)
    num_profiles = len(profile_start_indices)
    #profile_names = []

    # get profile_data
    start_row  = profile_start_indices[index_profile]
    profile_id = int(all_data.loc[start_row, mission_profile_ID])
    #profile_names.append(f"Mission Profile {profile_id}")

    end_row      = profile_start_indices[index_profile + 1] - 1 if index_profile < num_profiles - 1 else num_rows-1

    profile_data = all_data.iloc[start_row:end_row+1]
    profile_data = profile_data.dropna(how='all') # default: axis=0 (line) => suppress line(s) complete of nan
    return profile_data

# to get profile_data of each mission profile:
# profile_data = get_profile_data(0, mission_profile_ID, profile_start_indices, all_data)
# profile_data = get_profile_data(1, mission_profile_ID, profile_start_indices, all_data)
# profile_data = get_profile_data(2, mission_profile_ID, profile_start_indices, all_data)
# profile_data = get_profile_data(3, mission_profile_ID, profile_start_indices, all_data)
# profile_data = get_profile_data(4, mission_profile_ID, profile_start_indices, all_data)

# one usage in this file
def display_profile_data_parameters(profile_data):
    # to get parameters columns of mission profile:

    """Display profile data parameters."""
    life_ratio_i      = profile_data['life_ratio'].to_numpy() # related to Hours_per_Year_i
                                                              # Hours_per_Year_i = life_ratio_i * 8760 (t_total)

    Operating_Phase_i =  profile_data['Operating_Phase'].to_numpy()

    # load_factor (%of PN) not needed since power calculated now using Rel_torque
    # PN_i              = profile_data['PN'].to_numpy()


    Rel_speed_i       =  profile_data['Rel_speed'].to_numpy()
    Rel_torque_i      =  profile_data['Rel_torque'].to_numpy()

    T_i = profile_data['Tx'].to_numpy() # ambient temperature for power modules (considered heatsink air temperature here)
    # heatsink temperature will be calculated using this parameter

    delta_T_cycling_i = profile_data['delta_T_cycling'].to_numpy()
    T_max_cycling_i   = profile_data['T_max_cycling'].to_numpy()

    Hours_per_Year_i  = profile_data['Operating_Hours_per_Year'].to_numpy()      #  t_annual ? time associated with each operating phase over a year (hours)

    N_cy_i            = profile_data['N_cy'].to_numpy()            # N_annual_cy : number of cycles assocated with each cycling phase over a year (cycles)
    theta_cy_i        = profile_data['theta_cy'].to_numpy()        # cycle duration (hours)
                                                                   # now called t_phase in FIDES 2022 (?)


    Pi_application_i  = profile_data['Pi_application'].to_numpy()  # ignored:  the constant internPiApplication is used instead in calculation of FIT rate
    #Pi_type?


    # now calculated ("electro-thermal" simulation)
    #delta_T_cycling_i = profile_data['delta_T_cycling'].to_numpy() # maximum board temperature (?) during a cycling phase (degC)
    #T_max_cycling_i   = profile_data['T_max_cycling'].to_numpy()   #

    #RH_ambient ... always the same value
    G_RMS_i           = profile_data['G_RMS'].to_numpy()           # stress associated with each random vibration phase

    print("life_ratio_i: ", life_ratio_i)
    # could check that sum of life_ratio_i = 1

    print("Operating_Phase_i:",Operating_Phase_i)
    print("Rel_speed_i:",Rel_speed_i)
    print("Rel_torque_i:",Rel_torque_i)

    # =======================================================================
    # test
    # with Rel_torque_i, Rel_speed_i it is possible to calculate output power
    from converter.converter import Converter
    converter_gpi = Converter(
        name="REFERENCE_CONVERTER",
        power_range=(245, 1209),
        # might be defined in excel sheet
        torque_points_output={25: 0.39, 50: 0.56, 75: 0.77, 100: 1.0},
        torque_points_displacement={25: 0.57, 50: 0.78, 75: 0.85, 100: 0.87}
    )
    # calculation of active power for the different operating points defined in mission profile
    for i in range(len(Rel_torque_i)):
        rel_torque = Rel_torque_i[i]*100
        cos_phy = converter_gpi.get_displacement_factor(rel_torque)
        rel_output_current = converter_gpi.get_rel_output_current(rel_torque)
        m = Rel_speed_i[i]
        rms_out_voltage = 230 * m   # under assumption that with m=1, output voltage (phase to "neutral") = 230V rms
        rms_out_current = 360 * rel_output_current
        active_Pout = 3 * rms_out_voltage * rms_out_current * cos_phy
        # or UxIxcos_phy*sqrt(3), with U=sqrt(3)*230~400V
        print(f"{i} rel_output_current: {rel_output_current}")
        print(f"{i} output displacement factor: {cos_phy}" ) # same thing?
        print(f"{i} => output active power: {active_Pout}" )
    # =======================================================================

    print("T_i: ", T_i)

    print("delta_T_cycling_i: ", delta_T_cycling_i)
    print("T_max_cycling_i: ", T_max_cycling_i)

    print("Hours_per_Year_i: ", Hours_per_Year_i)
    # could check that sum of Hours_per_year_i = 8760

    print("N_cy_i: ", N_cy_i)
    print("theta_cy_i: ", theta_cy_i)
    # could check that sum of N_cy_i*theta_cy_i = 8760

    print("Pi_application_i: ", Pi_application_i)
    print("G_RMS_i: ", G_RMS_i)

# test:
# mission_profile_ID, num_profiles, profile_start_indices, all_data = get_profiles(excel_path, 'mission_profile')
# profile_data = get_profile_data(0, mission_profile_ID, profile_start_indices, all_data)
# display_profile_data_parameters(profile_data)


if __name__ == "__main__":
    excel_path   = 'old/inverter_stage_data2.xlsx'  # Path to Excel file (new file format)
    param_sheet  = 'parameters'         # Sheet where parameters are stored
    result_sheet = 'results'           # Sheet where results are written
    option_sheet = 'options'           # to enable / disable plots for instance

    # get mission profiles from excel sheet
    mission_profile_dict = read_excel_to_dict(excel_path, sheet_name='mission_profile')
    #print(mission_profile_dict)
    #display_blocks(mission_profile_dict) # to display the different segments of the mission profiles
    print("read ",len(mission_profile_dict.items()), "mission profile(s)")

    params  = read_parameters(excel_path, param_sheet)           # build dictionnary with parameters
    options = read_parameters(excel_path, option_sheet)

    # selection of desired plots
    plot_CDF_enabled = options['plot_CDF_en']
    plot_bathtub_enabled = options['plot_bathtub_en']
    plot_lifetime_mission_profile_enabled = options['plot_lifetime_mission_profile_en']
    plot_mission_profile_enabled = options['plot_mission_profile_en']

    # add information to params
    params["excel_path"]=excel_path
    params["param_sheet"]=param_sheet

    # depending on number of power modules in parallel the current
    # flowing in diodes and IGBT is divided or not.
    current_ratio = 1 / params['nb_parallel_sw']
    # add informations to params
    params["current_ratio"]=current_ratio

    reference_module_params = DeviceParameters(params) # component parameters to enable calculation of losses (conduction & switching)
    # update device parameters from data provided in Excel sheet => might be done in class itself
    # <need to pass param as parameter>
    #reference_module_params.Rg = params.get('Rg',6.67)          # ohm  (impacts the sw losses...)


    reference_module_diode  = Diode(device_params=reference_module_params) # PowerSemi with specific lambda0_TH (for FIDES model)
    reference_module_igbt   = IGBT(device_params=reference_module_params)  # "


    profiles = parse_mission_profiles(mission_profile_dict)
    for i, mission_profile in enumerate(profiles):
        print(f'mission profile {i+1}: {mission_profile}')
    # profiles is just an ordered list of values (no var. names) => requires to know the order of variables


    # test: alternative way to get mission profile (keeping variable names)
    mission_profile_ID, num_profiles, profile_start_indices, all_data = get_profiles(excel_path, 'mission_profile')
    # get profile 0
    profile_data = get_profile_data(0, mission_profile_ID, profile_start_indices, all_data)
    # display contents (debug)
    display_profile_data_parameters(profile_data)

    # debug
    print("=> mission profile are read")

    # Note: Tj, deltaT must be part of mission profile (completed after electro-thermal simulation)
    # reference_module_diode_reliab_model.reliab_calc(mission_profile, params)
    # reference_module_igbt_reliability_model.reliab_calc(mission_profile, params)

    """
    for each mission profile:
        for each segment of mission profile:
            determine losses within diodes & igbt for operating point
                < the losses are found when Tj has converged> => made jointly with estimation of Tj, Th(heatsink) >
                calc_diode_losses
                calc_igbt_losses
    ...


    """

    lambda_D, lambda_T = reference_module_diode.fit_rate_calc(profile_data, params, use_iec_temp=True)  # bof bof...


    print("\n\ndetermine fit rate of diode")
    diode_MTTF = reference_module_diode.fit_rate_calc(profile_data, params, use_iec_temp=True) # mission_profile without name of variables..
    diode_FITrate = 1/(diode_MTTF/1e9)

    print("\n\ndetermine fit rate of igbt")
    igbt_MTTF = reference_module_igbt.fit_rate_calc(profile_data, params, use_iec_temp=True)
    igbt_FITrate  = 1/(igbt_MTTF/1e9)

    # <both calculations might be done simultaneously>



    print("Diode MTTF (h):", diode_MTTF)
    print("IGBT MTTF (h):", igbt_MTTF)
