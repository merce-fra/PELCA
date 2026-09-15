# -*- coding: utf-8 -*-
"""\brief Extract mission-profile DataFrames from Excel workbooks.

This module is part of the PELCA reliability evaluator.
"""


import pandas as pd
#from openpyxl import load_workbook



def get_profiles(filename, sheet_name):
    """ to load Excel data in a DataFrame"""

    # *** alternative using openpyxl ***

    # # Load workbook in "values only" mode (uses cached results)
    # wb = load_workbook(filename, data_only=True)
    # ws = wb[sheet_name]

    # # Convert to DataFrame
    # data = ws.values
    # # Optionally treat the first row as header:
    # columns = next(data)
    # all_data = pd.DataFrame(data, columns=columns)

    # *** using pandas ***
    # works also if xlsx file has been save with ctrl+alt F9 (to read cache values instead of formula...)
    # <otherwise, store only data in read cells to avoid problems...>
    all_data = pd.read_excel(filename, sheet_name) # no need to close excel file for that
#    num_rows = len(all_data)

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

def get_profile_data(index_profile, mission_profile_ID, profile_start_indices, all_data):
    """Read profile data."""
    num_rows = len(all_data)
    num_profiles = len(profile_start_indices)
    #profile_names = []

    # get profile_data
    start_row  = profile_start_indices[index_profile]
#    profile_id = int(all_data.loc[start_row, mission_profile_ID])
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




def display_profile_data_parameters(profile_data):
    # to get parameters columns of mission profile:

# now calculated
#    life_ratio_i      = profile_data['life_ratio'].to_numpy() # related to Hours_per_Year_i
#                                                              # Hours_per_Year_i = life_ratio_i * 8760 (t_total)

    """Display profile data parameters."""
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

    #RH_ambiante ... always the same value
    G_RMS_i           = profile_data['G_RMS'].to_numpy()           # stress associated with each random vibration phase

    # suppressed
    # print("life_ratio_i: ", life_ratio_i)
    # could check that sum of life_ratio_i = 1

    print("Operating_Phase_i:",Operating_Phase_i)
    print("Rel_speed_i:",Rel_speed_i)
    print("Rel_torque_i:",Rel_torque_i)

    # =======================================================================
    # test
    # with Rel_torque_i, Rel_speed_i it is possible to calculate output power
    from inverter_reliability.igbt_reliability.converter.converter import Converter
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
