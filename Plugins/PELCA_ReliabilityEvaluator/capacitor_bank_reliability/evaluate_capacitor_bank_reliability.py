# -*- coding: utf-8 -*-
"""\brief Evaluate capacitor bank reliability and write PELCA-ready results to Excel.

This module is part of the PELCA reliability evaluator.
"""
# ===========================================================
# Reliability evaluation of a capacitor bank
# ===========================================================
# Evolutions:
# 07/2025:
# evaluation of lifetime (random part only) using FIDES model
# Added a few variables to determine the topology / the costs
# nb_capacitors	4
# topology	2p2s
#
# cost parameters
#   man_hour_rate
#   mounting_time
#   dismounting_time
#   capacitor_cost

# LF _ 18/05/2026 :  addition of avg losses during operation in results
# ===========================================================

import numpy as np
import matplotlib.pyplot as plt
import math

from openpyxl import load_workbook
from openpyxl.styles import Alignment

from inverter_reliability.igbt_reliability.calculations.calc_op_point import calc_active_power, calc_op_points
from capacitor_bank_reliability.utils.mission_profile import read_excel_to_dict

from capacitor_bank_reliability.utils.interpolation import interpolate_quadratic, LinearInterpolation, interp_fit
from capacitor_bank_reliability.utils.excel_data import ExcelData

# to remove all declared variables (debug)
# def clear_all():
#     from IPython import get_ipython;
#     get_ipython().magic('reset -sf')  # equivalent to clear all

from common.excel_parameters import read_parameters
from capacitor_bank_reliability.calculations.ripple import calc_ripple_current_LF, calc_bank_ripple_HF
from capacitor_bank_reliability.models.electrolytic_capacitor_fides import ELcapacitorFIDES

from capacitor_bank_reliability.models.bathtub_curve_model import BathtubCurveModel
from capacitor_bank_reliability.models.bathtub_model import BathtubModel


# note:
# One evolutions must be done:
# - change input parameters in mission profile to determine the operating point (rel_speed, rel_torque used instead of %PN)
#   This change will enable to align with other mission profiles and determine cos_phy as well as output current
#   From that, the output power and modulation index can be determined (not a worst case constant anymore...)
#


# to calculate relative output power using relative_torque & relative_speed
#from inverter_reliability.igbt_reliability.converter.converter import Converter

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# converter_gpi = Converter(
#     name="REFERENCE_CONVERTER",
#     power_range=(245, 1209),
#     torque_points_output={25: 0.39, 50: 0.56, 75: 0.77, 100: 1.0},
#     torque_points_displacement={25: 0.57, 50: 0.78, 75: 0.85, 100: 0.87}
# )
#
# print("rel_output_current (at rel_torque_current=50%):", converter_gpi.get_rel_output_current(50))  # 0.56
# print("output displacement factor (at rel_torque_current=75%):", converter_gpi.get_displacement_factor(75))  # 0.85
# output phase current (rms) = 363 x rel_output_current
# cos_phy = PF = output displacement factor
# output power = sqrt(3)* U * I * cos_phy (U = interphase voltage = sqrt(3) * Vpn (phase to neutral) - rms)

# def calc_active_power(converter, rel_torque, rel_speed):
#     cos_phy = converter.get_displacement_factor(rel_torque*100)
#     rel_output_current = converter.get_rel_output_current(rel_torque*100)
#     m = rel_speed
#     rms_out_voltage = 230 * m   # under assumption that with m=1, output voltage (phase to "neutral") = 230V rms
#     rms_out_current = 363 * rel_output_current
#     active_Pout = 3 * rms_out_voltage * rms_out_current * cos_phy
#     return active_Pout
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# ******************
# global constant(s)
# ******************
# OLD_MP = False # do not change! (new MP format)

hours_per_year = 8760 # 24*365  (365 days generally used... not 365.235)

# Vin: rms value of input AC voltage (phase to neutral)
def calc_Vdc(Vin):
  """Calculate vdc."""
  Vm = Vin*math.sqrt(2)            # peak input voltage
  Vdc =(3*math.sqrt(3)/math.pi)*Vm # rectified voltage avg value
  return Vdc

# ==================================
# capacitor bank ripple calculation
# =================================
# calc_bank_ripple_LF_vec = np.vectorize(calc_bank_ripple_LF)  # Now this works on arrays

# equivalent ripple current at 120Hz applied to capacitor
def calc_In(cap_ripple_LF, cap_ripple_HF, params):

    # capacitor parameters
    # ripple correction factor as function of frequency
    """Calculate in."""
    KFL	= params.get('KFL', 1.2)  # 300 Hz  (specified number = default value if not existing in excel sheet)
    KFH	= params.get('KFH', 1.41) # 8 kHz

    #print("KFL:",KFL)
    #print("KFH:",KFH)

    # equivalent applied current at 120 Hz
    In  = math.sqrt((cap_ripple_LF/KFL)**2 + (cap_ripple_HF/KFH)**2)

    # <losses might be calculated considering ESR_120 : Ploss = ESR_120 * In**2 >
    return In

# Lifetime calculation (model given by datasheet - based on wearout of capacitor)
# return the predicted Lifetime for a capacitor with (equ. 120 Hz) ripple current In, operating at temperature Tx
def calc_lx_hours(In, Tx, params):
    # parameters from datasheet
    """Calculate lx hours."""
    Lr = params.get('Lr', 5000) # lifetime at 85degC / nominal ripple current
    T0 = params.get('T0', 85)   # maximum category temperature

    # parameters of model chosen (not provided by manufacturer)
    max_lifetime =  params.get('max_lifetime', 150000) # usually between 100000 and 200000

    Kt = params.get('Kt', 1)           #
    deltaT0 = params.get('deltaT0', 5) #
    A = params.get('A', 10)            #
    Kv = params.get('Kv', 1)           # might be different since applied voltage << rated voltage

    # Determine ripple multiplier as function of ambient temperature
    # fitting of interpolation function using table values obtained from Excel sheet
    ripple_mult_temp_table = ExcelData(params["excel_path"],
                                       table_name='ripple multiplier vs temp',
                                       sheet_name=params["param_sheet"]).data
    data_points = [elem for elem in ripple_mult_temp_table] # [tuple(elem) for ...]
    # data_points = [(45, 2.82), (65, 1.73), (85, 1)] # for chosen capacitor
    a, b, c = interpolate_quadratic(data_points)
    # print(f"The quadratic polynomial is: P(t) = {a:.5f}t^2 + {b:.5f}t + {c:.5f}")
    ripple_mult_temp = a*Tx**2 + b*Tx + c # ripple_mult_temp = 0.00045*Tx**2 - 0.104*Tx + 6.59

    # nominal current corrected by ripple mult due to ambient temperature
    Iripple_nom = params.get('Iripple_nom', 30)

    I0 = Iripple_nom * ripple_mult_temp

    Lx = Lr*(2**-(Kt*(Tx-T0)/10))*(2**((deltaT0-(deltaT0*(In/I0)**2))/A))*Kv
    if Lx>max_lifetime: # saturation to max_lifetime if needed
        Lx=max_lifetime
    return Lx

# calculation of lifetime for mission profiles
def calc_lifetime_mission_profile(mission_profile, PN, Vout_rms, PF, Vdc, max_lifetime, params):

    """Calculate lifetime mission profile."""
    total_inverse_life = 0  # Somme des (life_ratio / Lx_hours) pour tous les segments

    for idx, segment in enumerate(mission_profile):
        # % of use  % of PN      ambient temp
        life_ratio, load_factor, Tx = segment[:3] # variables assignment with 3 first values of segment read
        #life_ratio, load_factor, Tx = segment[1:4] # variables assignment with 3 first values of segment read (if first colum is id of mission profile)

        # check if one of the three variables is NaN
        if any(math.isnan(val) for val in (life_ratio, load_factor, Tx)):
            print(f"Ignored segment #{idx} (invalid values) : {segment}")
            continue

        PN_i = PN * load_factor # output power (for this operating point)

        if PN_i==0:
            # no electrical stress of capacitors due to ripple HF
            # neglect at present ripple LF (no load ths vary limited)
            bank_ripple_LF = 0
            bank_ripple_HF = 0
        else:
        # capacitor bank current ripple calculation
            bank_ripple_LF = calc_ripple_current_LF(PN_i)                 # low frequency ripple
            bank_ripple_HF = calc_bank_ripple_HF(PN_i, Vout_rms, PF, Vdc) # high frequency ripple

        # Depending on the bank topology, this current can be divided into several capacitors
        # =>  calculation of capacitor current (as function of topology, i.e number of strings in //)
        current_ratio = params.get('current_ratio', 0.5)
        #voltage_ratio = params.get('voltage_ratio', 0.5)

        cap_ripple_LF = bank_ripple_LF * current_ratio
        cap_ripple_HF = bank_ripple_HF * current_ratio

        # <with these two parameters and with value of ESR it is theoretically possible to calculate losses in one capacitor>
        # It is also possible to use equivalent ripple at 120 Hz (and ESR eq at 120 Hz)
        # |Zcap| = sqrt(ESR^2 + 1/(w.C)^2) @ 120 Hz
        # Ic = Vc/Zcap
        # AC losses : Pcap = Vc^2/Zcap (equivalent components at 120 Hz?)
        # main components of capacitor voltage ripple are HF (multiples of Fsw) and LF components (6xFin = 300HZ)
        # better work with rms values?
        # see: https://www.walson-elec.com/news/industry-news/calculation-details-of-capacitance-loss.html
        # https://passive-components.eu/capacitors-losses-esrimpdfq/
        # https://passive-components.eu/esr-of-capacitors-mechanisms-measurements-and-impact-to-applications/
        # V_300hz_rms^2 / sqrt(ESR_300^2 + 1/(2*pi*300.C)^2) : losses at 300 Hz
        #
        # https://www.tdk-electronics.tdk.com/download/187610/26dc0a865c4f059ca5613940d3d4dcf2/pdf-thermaldesign.pdf
        # P = P_D +P_R
        # P_D = uac^2 * pi* f0 * C * tan(delta0) # dielectric losses [fa=300 Hz]
        # resistive losses:
        # P_R = I^2 * ESR , I = rms value of capacitor current, ESR = series resistance at max hot spot temp.
        #
        # approximation of losses in a capacitor : W = ESR_equ * In^2

        # equivalent 120 Hz ripple current (seen by each capacitor)
        In = calc_In(cap_ripple_LF, cap_ripple_HF, params)

        # theoretical lifetime of capacitor operating constantly under these conditions
        Lx_hours = calc_lx_hours(In, Tx, params) # wearout lifetime calculation

        total_inverse_life += life_ratio / Lx_hours

    # Calculation of global lifetime
    if total_inverse_life == 0:
        Lifetime_hours = max_lifetime
    else:
        Lifetime_hours = 1 / total_inverse_life

    # Clamp at max_lifetime
    Lifetime_hours = min(Lifetime_hours, max_lifetime)

    Lifetime_years = Lifetime_hours / hours_per_year # convert in years
    return Lifetime_years

# using named values
def calc_lifetime_mission_profile_new(profile_data, PN, Vout_rms, PF, Vdc, max_lifetime, params):
    """
    Calculation of lifetime of capacitor, for the given mission profile, using an empirical lifetime model
    :param profile_data: mission profile
    :param PN: percentage of nominal power
    :param Vout_rms: output voltage RMS value
    :param PF: power factor
    :param Vdc: DC bus voltage
    :param max_lifetime: limit guaranteed by manufacturer
    :param params: parameters used for the modules of this tool
    :return: calculated lifetime in years, cap_losses
    """
    total_inverse_life = 0  # Somme des (life_ratio / Lx_hours) pour tous les segments
    cap_losses = np.zeros(len(profile_data))

    # for each phase (segment) of mission profile:
    for idx in range(len(profile_data)):
        # life_ratio_i = profile_data['life_ratio'].to_numpy()[idx]
        #load_factor_i = profile_data['PN'].to_numpy()[idx]
        T_i = profile_data['Tx'].to_numpy()[idx]
        Operating_Phase_i = profile_data['operating_phase'].to_numpy()[idx] # not handled yet

        # LF _ 12/03/2026
        Rel_Speed_i = profile_data['Rel_Speed_i'].to_numpy()[idx]
        Rel_Torque_i = profile_data['Rel_Torque_i'].to_numpy()[idx]
        # now used to determine the load_factor_i
        load_factor_i = calc_active_power(Rel_Torque_i, Rel_Speed_i)/PN

        PN_i = PN * load_factor_i  # output power (for this operating point)
        #print("load factor_i: ", load_factor_i)
        #print("PN_i: ", PN_i)

        life_ratio_i = profile_data['Operating_Hours_per_Year'].to_numpy()[idx] / 8760
        #print("life_ratio : ", life_ratio_i)

        if PN_i == 0:
            # no electrical stress of capacitors due to ripple HF
            # neglect at present ripple LF (no load thus very limited)
            bank_ripple_LF = 0
            bank_ripple_HF = 0
        else:
            # capacitor bank current ripple calculation
            bank_ripple_LF = calc_ripple_current_LF(PN_i)  # low frequency ripple
            bank_ripple_HF = calc_bank_ripple_HF(PN_i, Vout_rms, PF, Vdc)  # high frequency ripple

        # Depending on the bank topology, this current can be divided into several capacitors
        # =>  calculation of capacitor current (as function of topology, i.e number of strings in //)
        current_ratio = params.get('current_ratio', 0.5) # default value = 0.5 (2 strings in //)
        # voltage_ratio = params.get('voltage_ratio', 0.5)

        cap_ripple_LF = bank_ripple_LF * current_ratio
        cap_ripple_HF = bank_ripple_HF * current_ratio

        # <with these two parameters and with value of ESR it is theoretically possible to calculate losses in one capacitor>
        # It is also possible to use equivalent ripple at 120 Hz (and ESR eq at 120 Hz)
        # |Zcap| = sqrt(ESR^2 + 1/(w.C)^2) @ 120 Hz
        # Ic = Vc/Zcap
        # AC losses : Pcap = Vc^2/Zcap (equivalent components at 120 Hz?)
        # main components of capacitor voltage ripple are HF (multiples of Fsw) and LF components (6xFin = 300HZ)
        # better work with rms values?
        # see: https://www.walson-elec.com/news/industry-news/calculation-details-of-capacitance-loss.html
        # https://passive-components.eu/capacitors-losses-esrimpdfq/
        # https://passive-components.eu/esr-of-capacitors-mechanisms-measurements-and-impact-to-applications/
        # V_300hz_rms^2 / sqrt(ESR_300^2 + 1/(2*pi*300.C)^2) : losses at 300 Hz
        #
        # https://www.tdk-electronics.tdk.com/download/187610/26dc0a865c4f059ca5613940d3d4dcf2/pdf-thermaldesign.pdf
        # P = P_D +P_R
        # P_D = uac^2 * pi* f0 * C * tan(delta0) # dielectric losses [fa=300 Hz]
        # resistive losses:
        # P_R = I^2 * ESR , I = rms value of capacitor current, ESR = series resistance at max hot spot temp.
        #
        # approximation of losses in one capacitor : W = ESR_equ * In^2
        ESR_LF = params['ESR_120'] / params['KFL']**2 # estimation of ESR at 300 Hz
        ESR_HF = params['ESR_120'] / params['KFH']**2 # estimation of ESR at approx 2*fsw
        cap_losses[idx] = cap_ripple_LF**2 * ESR_LF + cap_ripple_HF**2 * ESR_HF # estimation of losses in one capacitor

        # equivalent 120 Hz ripple current (seen by each capacitor)
        In = calc_In(cap_ripple_LF, cap_ripple_HF, params)

        # note: losses in capacitor could be expressed also: cap_losses[idx] = In**2 * ESR_120

        # theoretical lifetime of capacitor operating constantly under these conditions
        Lx_hours = calc_lx_hours(In, T_i, params)  # wearout lifetime calculation

        total_inverse_life += life_ratio_i / Lx_hours

    # Calculation of global lifetime
    if total_inverse_life == 0:
        Lifetime_hours = max_lifetime
    else:
        Lifetime_hours = 1 / total_inverse_life

    # Clamp at max_lifetime
    Lifetime_hours = min(Lifetime_hours, max_lifetime)

    Lifetime_years = Lifetime_hours / hours_per_year  # convert in years
    return Lifetime_years, cap_losses


# for one given mission profile
def calc_fit_for_random_part_mission_profile(mission_profile, params):

    # FIT (failure in time) rate for random failure period of one capacitor


    # ========================================================================
    # when using interpolation between two "known" points (at two different temperatures)
    """Calculate fit for random part mission profile."""
    FIT40 = params.get('FIT40', 12)
    FIT85 = params.get('FIT85', 250)
    total_fit_rate = 0  # sum (life_ratio * fit_rate) for all segments
    for idx, segment in enumerate(mission_profile):
        life_ratio, load_factor, Tx = segment[:3] # variables assignment with 3 first values of segment read
        #life_ratio, load_factor, Tx = segment[1:4] # variables assignment with 3 first values of segment read (if colum mission profile is present...)
        # check if one of the three variables is NaN
        if any(math.isnan(val) for val in (life_ratio, load_factor, Tx)):
            print(f"Ignored segment #{idx} (invalid values) : {segment}")
            continue
        fit_Tx = interp_fit(Tx, FIT40, FIT85) # fit rate at temperature Tx
        total_fit_rate += life_ratio * fit_Tx

    # ========================================================================

    # <considering only random failure>
    MTBF_years = (1/(total_fit_rate*0.000000001))*(1/hours_per_year)

    # reliability R(t) = np.exp(-lambda*t)

    return total_fit_rate, MTBF_years

def write_result(params, excel_path, sheet_name, lifetime, PELCA_params):
    """Write the result to the specified sheet."""
    book = load_workbook(excel_path)
    if sheet_name not in book.sheetnames:
        book.create_sheet(sheet_name)

    sheet = book[sheet_name]

    # Loop through rows 1 to 50 and columns A to I
    for row in range(1, 51):
        for col in range(1, 10):  # 1=A, 9=I
            sheet.cell(row=row, column=col).value = None  # Clear cell value

    # first line
    sheet['B'+str(1)] = '(capacitor)'
    sheet['D'+str(1)] = 'Parameters for PELCA (DC bus bank)'

    line_header=2
    sheet['A'+str(line_header)] = 'mission profile'
    sheet['B'+str(line_header)] = 'lifetime (year)'
    # for early failure, defaults values (low fit rate) are used

    sheet['D'+str(line_header)] = 'Early failure (sigma, year)'    # 'eta_early'
    sheet['E'+str(line_header)] = 'Early failure (beta)'           # 'beta_early'
    sheet['F'+str(line_header)] = 'Random failure (sigma, year)'   # 'eta_random'
    sheet['G'+str(line_header)] = 'Random failure (beta)'          # 'beta_random'
    sheet['H'+str(line_header)] = 'Wear-out failure (sigma, year)' # 'eta_wearout'
    sheet['I'+str(line_header)] = 'Wear-out failure (beta)'        # 'beta_wearout'


    # result here are the lifetimes for the different mission profiles
    # add the parameters for PELCA (random / wearout parts for each mission profile)

    for i in range(0,len(lifetime)):
        value = lifetime[i] # get lifetime value
        # calculate lifetime [considered lifetime of one capacitor]
        sheet['A'+str(i+line_header+1)] = 'profile '+str(i+1)
        sheet['B'+str(i+line_header+1)] = value

        # parameters for PELCA
        # early life part
        sheet['D' + str(i + line_header + 1)] = PELCA_params['eta_early']
        sheet['E'+str(i+line_header+1)] = PELCA_params['beta_early'] # beta<1

        # (random part)
        eta = PELCA_params['eta_random'][i]
        sheet['F'+str(i+line_header+1)] = eta
        sheet['G'+str(i+line_header+1)] = PELCA_params['beta_random'] # beta=1

        # wearout part
        sheet['H'+str(i+line_header+1)] = PELCA_params['eta_wearout'][i]
        sheet['I'+str(i+line_header+1)] = PELCA_params['beta_wearout']

    # cost calculation

    # total_cost = man_hour_rate * (mounting_time + dismounting_time) + nb_capacitors * capacitor_cost
    RU_raw_cost = params['nb_capacitors'] * params['capacitor_cost']
    RU_assembly_cost    = params['man_hour_rate'] *  params['mounting_time']*(1/60)    # convert time in hours!
    RU_disassembly_cost = params['man_hour_rate'] *  params['dismounting_time']*(1/60)

    total_cost = RU_assembly_cost + RU_disassembly_cost + RU_raw_cost
    print("Maintenance cost:")
    print('with current topology, the replacement cost of capacitor bank would be:', total_cost, ' euros' )

    line_header_cost = max(i+line_header+3,9)
    sheet['A'+str(line_header_cost)] = 'to copy into \'Cost - Price\' sheet of PELCA input Excel file'
    line_header_cost = line_header_cost + 1

    # header for cost parameters
    sheet['A'+str(line_header_cost)] = 'RU raw cost/price (€))'
    # sheet['B'+str(line_header_cost)] = 'RU repair cost/price (%)' # change of format of PELCA input file
    sheet['B'+str(line_header_cost)] = 'RU assembly cost/price (€)'
    sheet['C'+str(line_header_cost)] = 'RU disassembly cost/price (€)'

    sheet['A'+str(line_header_cost+1)] = RU_raw_cost
    # sheet['B'+str(line_header_cost+1)] = '100.00 %' # (or 1.0 and cell type = percentage ?)
    sheet['B'+str(line_header_cost+1)] = RU_assembly_cost
    sheet['C'+str(line_header_cost+1)] = RU_disassembly_cost

    book.save(excel_path)

# LF _ 06/03/2026 : to write thermal_data
# <to factorize with other tools>
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
    """
    # Open in append mode and replace only the target sheet
    writer = pd.ExcelWriter(filepath, engine='openpyxl', mode="a", if_sheet_exists="replace",)

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


plot_bathtub_with_uncertainty = 0
def plot_bathtub_mission_profiles(RU_name, result, PELCA_params):
    """Plot bathtub mission profiles results."""
    t = np.linspace(1, 20, 240) # 20 years with a resolution of one month

    model_list= []
    for index in range(0,len(PELCA_params['eta_random'])):

        # early failures (no idea!)
        infant_shape=PELCA_params['beta_early']
        infant_scale=PELCA_params['eta_early']

        # normal life
        normal_scale = PELCA_params['eta_random'][index]
        normal_rate=(1/normal_scale)

        # wearout
        wearout_shape=PELCA_params['beta_wearout']
        wearout_scale=PELCA_params['eta_wearout'][index]

        # Instantiate model with default parameters
        model_list.append(BathtubCurveModel(infant_shape, infant_scale,
                                       normal_rate,
                                       wearout_shape, wearout_scale)
                     )

    # plot the different bathtub curves corresponding to mission profiles
    for i,model in enumerate(model_list):
        # Plot failure rate and CDF
        model.plot_curve(RU_name, t, "profile"+str(i+1))

        if plot_bathtub_with_uncertainty==1:
            # Plot failure rate with confidence interval
            model.plot_with_uncertainty(t, 'profile'+str(i+1), confidence=0.60)




def setup_common_parameters(params):
    """Extract common parameters and compute ripple multipliers."""
    #  nominal power of motor drive inverter
    PN = params.get('PN', 200000)  # Default to 200000 if parameter is missing
    Vin = params.get('Vin', 220)   # input AC line to neutral voltage (RMS)
    Vout_rms = params.get('Vout_rms', 170) # output voltage RMS <for M~0.7>
    PF = params.get('PF', 0.8)     # output voltage power factor

    # parameters of model chosen (not provided by manufacturer)
    max_lifetime = params.get('max_lifetime', 150000) # if not provided, default to 150000 h

    Vdc = calc_Vdc(Vin)            # avg DC bus voltage

    # create interpolation function for ripple multipliers

    # Determine ripple multiplier as function of frequency
    # fitting of interpolation function using table values obtained from Excel sheet
    ripple_mult_freq_table = ExcelData(
        params["excel_path"],
        table_name='ripple multiplier vs freq',
        sheet_name=params["param_sheet"]
    ).data

    # linear interpolation is used for that
    ripple_mult_freq_interp = LinearInterpolation([elem for elem in ripple_mult_freq_table])
    params['KFL'] = ripple_mult_freq_interp.interpolate(300)   # low freq ripple at 300 Hz
    # <under assumption that main harmonic is at 2 x Fsw, with Fsw=4 kHz>
    params['KFH'] = ripple_mult_freq_interp.interpolate(8000)  # high freq ripple at 8 kHz

    return PN, Vout_rms, PF, Vdc, max_lifetime

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

# change method to pass the mission profile: already available in instance of class ElcapacitorFIDES
# def perform_calculation(params, mission_profile_dict, mode="standard", CapBank_FIDES_model=None, show_simple=False):
#     """
#     Perform capacitor reliability calculation.
#     mode: "standard" or "fides"
#     """
#     PN, Vout_rms, PF, Vdc, max_lifetime = setup_common_parameters(params)
#     profiles = parse_mission_profiles(mission_profile_dict)
#
#     if show_simple:
#         _run_simple_example(params, PN, Vout_rms, PF, Vdc)
#
#     lifetime = []
#     eta_random = []
#
#     print('Calculation reliability for the mission profile(s)')
#
#     for i, mission_profile in enumerate(profiles):
#         print(f'mission profile {i+1}: {mission_profile}')
#         lifetime.append(calc_lifetime_mission_profile(mission_profile, PN, Vout_rms, PF, Vdc, max_lifetime, params))
#
#         if mode == "standard":
#             fit_eq, MTBF_years_eq = calc_fit_for_random_part_mission_profile(mission_profile, params)
#             print(f"Cap failure rate:{fit_eq:.2f} FIT => MTBF_years: {MTBF_years_eq:.2f} years")
#             eta_random.append(MTBF_years_eq)
#
#     if mode == "fides" and CapBank_FIDES_model:
#         for i in range(CapBank_FIDES_model.num_profiles):
#             start_row = CapBank_FIDES_model.profile_start_indices[i]
#             profile_id = int(CapBank_FIDES_model.all_data.loc[start_row, CapBank_FIDES_model.mission_profile_ID])
#             CapBank_FIDES_model.profile_names.append(f"Mission Profile {profile_id}")
#
#             end_row = (
#                 CapBank_FIDES_model.profile_start_indices[i + 1] - 2
#                 if i < CapBank_FIDES_model.num_profiles - 1
#                 else CapBank_FIDES_model.num_rows
#             )
#             CapBank_FIDES_model.profile_data = CapBank_FIDES_model.all_data.iloc[start_row:end_row + 1]
#
#             if not CapBank_FIDES_model.profile_data.empty:
#                 fit_eq, MTBF_years_eq = CapBank_FIDES_model.calc_fit_FIDES_for_random_part_mission_profile()
#                 print(f"Cap failure rate:{fit_eq:.2f} FIT; MTBF_years: {MTBF_years_eq:.2f} years")
#                 eta_random.append(MTBF_years_eq)
#
#     #print("(fit rate(s) of one capacitor)")
#     print("\n")
#     return lifetime, eta_random # with lifetime, eta_random: list

# change method to pass the mission profile: already available in instance of class ElcapacitorFIDES
def perform_calculation_new(params, CapBank_FIDES_model, mode="standard", show_simple=False):
    """
    Perform capacitor reliability calculation.
    mode: "standard" or "fides"
    CapBank_FIDES_model : contains the mission profile data  (used even if mode "standard" selected)
    """
    PN, Vout_rms, PF, Vdc, max_lifetime = setup_common_parameters(params)

    # LF _ 12/03/2026: Vout_rms, PF  are now to be calculated for each segment of mission profile

    if show_simple:
        _run_simple_example(params, PN, Vout_rms, PF, Vdc)
    # list of lifetime(s) & eta_wearout for final report
    lifetime = []
    eta_random = []
    list_of_df = []  # list of mission profiles with thermal data

    print('perform_calculation_new: Calculation reliability for the mission profile(s)')
    for i in range(CapBank_FIDES_model.num_profiles):  # num_profiles

        # get one mission profile
        mission_profile = CapBank_FIDES_model.get_profile_data(i)

        print(f'mission profile {i + 1}: {mission_profile}')
        MP_lifetime, cap_losses = calc_lifetime_mission_profile_new(mission_profile, PN, Vout_rms, PF, Vdc, max_lifetime, params)
        lifetime.append(MP_lifetime)

        if mode == "standard":
            fit_eq, MTBF_years_eq = calc_fit_for_random_part_mission_profile(mission_profile, params)
            print(f"Cap failure rate:{fit_eq:.2f} FIT => MTBF_years: {MTBF_years_eq:.2f} years")
            eta_random.append(MTBF_years_eq)
        else:
            # mode == "fides"
            start_row = CapBank_FIDES_model.profile_start_indices[i]
            profile_id = int(CapBank_FIDES_model.all_data.loc[start_row, CapBank_FIDES_model.mission_profile_ID])
            CapBank_FIDES_model.profile_names.append(f"Mission Profile {profile_id}")

            end_row = (
                CapBank_FIDES_model.profile_start_indices[i + 1] - 2
                if i < CapBank_FIDES_model.num_profiles - 1
                else CapBank_FIDES_model.num_rows
            )
            CapBank_FIDES_model.profile_data = CapBank_FIDES_model.all_data.iloc[start_row:end_row + 1]

            if not CapBank_FIDES_model.profile_data.empty:
                fit_eq, MTBF_years_eq = CapBank_FIDES_model.calc_fit_FIDES_for_random_part_mission_profile()
                print(f"Cap failure rate:{fit_eq:.2f} FIT; MTBF_years: {MTBF_years_eq:.2f} years")
                eta_random.append(MTBF_years_eq)

        df = mission_profile.copy()
        # add additional information (dissipated power, ...)
        cap_bank_losses         = cap_losses * params['nb_capacitors']
        df["cap_bank_losses"]   = cap_bank_losses

        # increase of air flow temperature
        # F : air flow = 0,17 m3/s
        # Cv =  Isobaric volumetric heat capacity CP,v J*cm-3*K-1 = 0.00121  => 1210 J/(m^3*K)
        df["deltaTx_heatsink"]  = cap_bank_losses / (0.17 * 1210)
        list_of_df.append((i, df))

        # for debug
        # LF _ 12/03/2026
        Rel_Speed_i = df['Rel_Speed_i']
        Rel_Torque_i = df['Rel_Torque_i']
        load_factor_i = calc_active_power(Rel_Torque_i, Rel_Speed_i)/PN
        PN_i = PN * load_factor_i  # output power (for this operating point)
        life_ratio_i = df['Operating_Hours_per_Year'].to_numpy() / 8760

        df["load_factor_i"] = load_factor_i
        df["active_power"] = PN_i
        df["life_ratio_i"] = life_ratio_i

    # print("(fit rate(s) of one capacitor)")
    print("\n")
    return lifetime, eta_random, list_of_df  # with lifetime, eta_random: list



def _run_simple_example(params, PN, Vout_rms, PF, Vdc):
    """Internal helper for run simple example."""
    print("**********************")
    print("example of calculation")
    print("**********************")

    Pout_percent = 0.75
    Pout = Pout_percent * PN
    Pdc = Pout

    print(f"operation point: Pout = {Pout_percent:.2f} of PN => Pout = {Pout:.2f} W")

    bank_ripple_LF = calc_ripple_current_LF(Pdc)
    bank_ripple_HF = calc_bank_ripple_HF(Pout, Vout_rms, PF, Vdc)

    print('  bank_ripple_LF:', f'{bank_ripple_LF:.2f}', 'A rms')
    print('  bank_ripple_HF:', f'{bank_ripple_HF:.2f}', 'A rms')

    current_ratio = params.get('current_ratio', 0.5)
    cap_ripple_LF = bank_ripple_LF * current_ratio
    cap_ripple_HF = bank_ripple_HF * current_ratio

    print('  cap_ripple_LF:', f'{cap_ripple_LF:.2f}', 'A rms')
    print('  cap_ripple_HF:', f'{cap_ripple_HF:.2f}', 'A rms')

    In = calc_In(cap_ripple_LF, cap_ripple_HF, params)
    Tx = 55
    print("lifetime at Tx=", f'{Tx}', 'degC')

    Lx_hours = calc_lx_hours(In, Tx, params)
    Lx_years = Lx_hours / hours_per_year

    print('  Lifetime (wearout):', f'{Lx_hours:.2f}', 'h')
    print('  Lifetime (wearout):', f'{Lx_years:.2f}', 'years')

    FIT40 = params.get('FIT40', 12)
    FIT85 = params.get('FIT85', 250)
    fit_Tx = interp_fit(Tx, FIT40, FIT85)
    print('  FIT rate (random part):', f'{fit_Tx:.2f}', ' (fit) at Tx=', f'{Tx}', 'degC')

    print("**********************")
    print("end of example")
    print("**********************")
    return



def plot_lifetime_mission_profile(item_name, lifetime):
    #index = [i+1 for i in range(0, len(lifetime))]
    """Plot lifetime mission profile results."""
    index = list(range(1, len(lifetime) + 1))

    plt.figure()
    plt.plot(index, lifetime, 'o--', label='lifetime in years', color='black')

    # Add labels and legend
    plt.title(f"({item_name}) Lifetime according to mission profile")
    plt.xlabel("mission profile number")
    plt.ylabel("Lifetime (years)")
    plt.legend()
    plt.grid(True)

    plt.xticks(range(1, len(lifetime) + 1)) # draw only integer values

    # add values above each point
    for xi, yi in zip(index, lifetime):
        #plt.text(xi, yi + 0.3, str(yi), ha='center', va='bottom', fontsize=9, color='black')
        plt.text(xi, yi + 0.3, f"{yi:.2f}", ha='center', va='bottom', fontsize=9, color='black')

    # Show the plot
    plt.show()


def plot_mission_profile(data, profile_number, width_var, height_var, label_var):
    """Plot mission profile results."""
    segments = data.get(profile_number, {})
    if not segments:
        print(f"Mission profile {profile_number} not found.")
        return

    labels = list(segments.keys())
    try:
        widths = [float(segments[k][width_var]) for k in labels]
        heights = [float(segments[k][height_var]) for k in labels]
        annotations = [segments[k][label_var] for k in labels]
        life_labels = [f"{float(segments[k][width_var]):.2f}" for k in labels]
    except KeyError as e:
        print(f"Missing key : {e}")
        return

    # Place bars consecutively
    positions = np.cumsum([0] + widths[:-1])

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(positions, heights, width=widths, align='edge', color='skyblue', edgecolor='black')

    # Ajouter le label au-dessus de chaque barre (ex: PN)
    for bar, annotation in zip(bars, annotations):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + 1, f'{label_var}={annotation}', ha='center', va='bottom')

    # Ajouter les valeurs de width_var (ex: life_ratio) sous chaque barre
    ax.set_xticks([bar.get_x() + bar.get_width() / 2 for bar in bars])
    ax.set_xticklabels(life_labels)
    ax.set_xlabel(f"{width_var} (largeur ∝ {width_var})")
    ax.set_ylabel(f"{height_var}")
    ax.set_title(f"Profile {profile_number} : {height_var} vs segments (width ∝ {width_var}, label = {label_var})")
    ax.grid(True, axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.show()

def plot_new_mission_profiles(CapBank_FIDES_model, width_var='life_ratio', height_var='Tx', label_var='PN'):
    # just a placeholder for now
    #return
    # purpose: display the different mission profiles present in instance CapBank_FIDES_model
    # loop through all mission profiles:
    """Plot new mission profiles results."""
    for profile_number in range(CapBank_FIDES_model.num_profiles):  # num_profiles
        # get one mission profile
        profile_data = CapBank_FIDES_model.get_profile_data(profile_number)

        #widths = list(profile_data[width_var].to_numpy())
        widths = list(profile_data['Operating_Hours_per_Year'].to_numpy() / 8760)  # life_ratio
        heights = profile_data[height_var].to_numpy()

        Rel_speed_vec = profile_data['Rel_Speed_i'].to_numpy()   # slightly different names used in eval_inv_reliab... Rel_speed
        Rel_Torque_vec = profile_data['Rel_Torque_i'].to_numpy() # slightly different names used in eval_inv_reliab... Rel_torque
        Pout, Iout, PF, Vout_rms = calc_op_points(540, Rel_speed_vec, Rel_Torque_vec)
        annotations = Pout  # active_Pout
        #annotations = profile_data[label_var].to_numpy()

        #life_labels = [f"{float(profile_data[width_var].to_numpy()[k]):.2f}" for k in range(len(profile_data))]
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
        ax.set_xticklabels(life_labels)
        ax.set_xlabel(f"{width_var} (largeur ∝ {width_var})")
        ax.set_ylabel(f"{height_var}")
        ax.set_title(f"Profile {profile_number} : {height_var} vs segments (width ∝ {width_var}, label = {label_var})")
        ax.grid(True, axis='y', linestyle='--', alpha=0.5)

        plt.tight_layout()
        plt.show()

def plot_cdf(RU_name, lifetime, PELCA_params):
    # calculate & display cdf of the different profiles

    """Plot cdf results."""
    plt.figure(figsize=(10, 6))

    plt.xlabel("Time (years)")
    plt.ylabel("Cumulative Distribution Function (CDF)")
    plt.title(RU_name + ": CDFs depending on mission profile(s)")
    plt.grid(True)
    for i, eta_wearout in enumerate(lifetime):
        model = BathtubModel(
            beta1=PELCA_params['beta_early'],   eta1=PELCA_params['eta_early'],     # Early-life <fixed default parameters
            beta2=PELCA_params['beta_random'],  eta2=PELCA_params['eta_random'][i], # Useful-life
            beta3=PELCA_params['beta_wearout'], eta3=PELCA_params['eta_wearout'][i], # Wear-out
            time_range=(0.01, max(lifetime))
        )
        # model.plot_cdfs()
        plt.plot(model.t, model.F_total, label=f"mission profile {i}") # , color='blue'
    plt.legend()
    plt.show()



# calculation of parameter for the bank
# - since we have N (4) capacitors in a bank, considering that each failure
# lead to system failure, lambda should be multiplied by N:
# Rcap1(t)*Rcap2(t)*Rcap3(t)*Rcap4(t)=(exp(-lambda*t))**4=exp(-4*lambda*t) => lamda_eq =4*lambda
#
# On the other hand (for wearout), lifetime of bank  = lifetime of the weakest component
# Since all capacitors are expected to age rather similarly (same lambda_wearout for each capacitor),
# the lifetime of the bank is expected to be close (?) to the lifetime of one capacitor:

# (under assumption that reliability of ageing cap follows a weibull law)
# slightly less maybe... R = exp(-N*(lambda_wearout*t)**beta_wearout) = exp(-(lambda_eq*t)**beta_wearout)
# lambda_eq = lambda_wearout * N**(1/beta_wearout)
# with N=4
#   - at low beta_wearout  (2 for instance) : lambda_eq = 2    x lambda_wearout <slow ageing>
#   - at large beta_wearout (8?):             lambda_eq = 1.19 x lambda_wearout <fast ageing>

def bank_wearout_scaling_factor(N, beta_wearout):
    # eta = Lx / (gamma(1+1/beta)) for a single capacitor
    # eta = Lx / (gamma(1+1/beta) * N**(1/beta)) for N capacitor
    """Run bank wearout scaling factor."""
    scaling_factor = 1/(math.gamma(1 + 1/beta_wearout)*N ** (1/beta_wearout))
    return scaling_factor

def calc_Weibull_parameters_for_bank(params, lifetime, eta_random):

    """Calculate weibull parameters for bank."""
    PELCA_params = {}

    # determination of parameters for PELCA (specification of bathtub model for a replacement unit, i.e. the capacitor bank)

    # early life not evaluated
    # if information is available, this must be updated manually in PELCA input
    # constant default values considered here
    PELCA_params['beta_early']=0.6
    PELCA_params['eta_early']=3424

    # random part:
    PELCA_params['beta_random']=1
    PELCA_params['eta_random']=[eta / params['nb_capacitors'] for eta in eta_random] #  list of characteristic life (random) - beta random=1

    # wearout part:
    # beta_wearout = 1.5 or 2 for instance for slow ageing
    # 3 to 4 for faster ageing
    PELCA_params['beta_wearout'] = 3
    PELCA_params['eta_wearout']=[Lx * bank_wearout_scaling_factor(params['nb_capacitors'],PELCA_params['beta_wearout'] ) for Lx in lifetime] # list of characterisitic life for wearout part
    # eta_wearout = scaling_factor * lifetime

    return PELCA_params


# ====================================================================================================================
# Main code
# ====================================================================================================================
def evaluate_capacitor_bank_reliability(excel_path):
    #excel_path = 'capacitor_bank_reliability/data/cap_data.xlsx'  # Path to Excel file
    """Evaluate capacitor bank reliability."""
    print(f"Starting capacitor bank reliability evaluation with workbook: {excel_path}", flush=True)

    param_sheet = 'parameters'          # Sheet where parameters are stored
    result_sheet = 'results'            # Sheet where results are written
    option_sheet = 'options'            # to enable / disable plots for instance

    # get mission profiles from Excel sheet
    # if OLD_MP:
    #     mission_profile_dict = read_excel_to_dict(excel_path, sheet_name='mission_profile') # CAP_MP / system_MP
    #
    #     #print(mission_profile_dict)
    #     #display_blocks(mission_profile_dict) # to display the different segments of the mission profiles
    #     print("read ",len(mission_profile_dict.items()), "mission profile(s)")
    #
    #     ## debug
    #     # from get_mission_profile import display_blocks, get_block_variables
    #     #block1_variables = get_block_variables(mission_profile_dict, 1)
    #     ## block1_variables then contains a list of values for each segment of mission profile
    #     ## (but the variable names are not given : order is important...)
    #     #print(block1_variables)

    # Change method to read mission profile (at present - same method as for IGBTs)
    # ---------------------- LOAD DATA ----------------------
    # Read mission profile table
    # from inverter_reliability.igbt_reliability.utils.get_profiles import get_profiles, get_profile_data, display_profile_data_parameters
    #
    # # get (all) mission profiles (keeping variable names)
    # mission_profile_ID, num_profiles, profile_start_indices, all_data = get_profiles(excel_path, 'mission_profile')
    # already done in class ElcapacitorFIDES...

    # read parameters and options
    params = read_parameters(excel_path, param_sheet)           # build dictionary with parameters
    options = read_parameters(excel_path, option_sheet)

    # selection of desired plots
    plot_CDF_enabled = options['plot_CDF_en']
    plot_bathtub_enabled = options['plot_bathtub_en']
    plot_lifetime_mission_profile_enabled = options['plot_lifetime_mission_profile_en']
    plot_mission_profile_enabled = options['plot_mission_profile_en']

    # add information to params
    params["excel_path"]=excel_path
    params["param_sheet"]=param_sheet

    # Depending on the bank topology, the DC bus ripple current & bus voltage can be divided into several capacitors
    # affecting the stress level of components. Under assumption that components are identical:
    # => current is divided by the number of strings in //
    # => bus voltage is divided by the number of components in series
    #
    # Calculation of current_ratio (fraction of cap bank current seen by one capacitor) : cap_current = bank_current * current_ratio
    # =>  it is the inverse of the number of parallel string : xp where x is the number of parallel string [max 9!]
    # Calculation of voltage_ratio (fraction of DC bus voltage seen by one capacitor) : cap_voltage = bank_voltage * voltage_ratio
    # =>  it is the inverse of the number of capacitors in series : ys where y is the number of parallel string [max 9!]
    #if params['topology']== '2p2s':
    #    print("bank composed of 2 parallel strings of two capacitors in series")

    nb_strings = int(params['topology'][0])  # first character
    if nb_strings==0:
        print("error: nb_strings = 0")
        return
    nb_cap_in_series = int(params['topology'][2]) # third character
    if nb_cap_in_series == 0:
        print("error: nb_cap_in_series = 0")
        return
    if nb_strings>1:
        print(f"Capacitor bank composed of {nb_strings} parallel strings")
    else:
        print(f"Capacitor bank has a single string")
    if nb_cap_in_series>1:
        print(f"String composed of {nb_cap_in_series} capacitor(s) in series\n")
    current_ratio = 1/nb_strings       # bank current is divided by the number of strings
    voltage_ratio = 1/nb_cap_in_series # voltage across bank divided by number of cap in series


    # add information to params
    params["current_ratio"]=current_ratio
    params["voltage_ratio"]=voltage_ratio

    Vdc = params.get('Vin', 230) * np.sqrt(2) * np.sqrt(3) * (3 / np.pi)
    Vapplied = Vdc * voltage_ratio
    params["Vapplied"] = Vapplied


    # for use with FIDES model
    CapBank_FIDES_model = ELcapacitorFIDES(excel_path,'mission_profile', params)    # CAP_MP / system_MP

    # reliability calculation (random + wearout)
    if params['FIT_calculation_mode']=='interpolated' or params['FIT_calculation_mode']!='FIDES':
        # using interpolation between to known FIT values
        print("random failure rate calculated by interpolation between given fit values")
        # if OLD_MP:
        #     lifetime, eta_random = perform_calculation(params, mission_profile_dict, mode="standard",
        #                                                CapBank_FIDES_model=None, show_simple=False)
        # else:
        #     lifetime, eta_random, list_of_df = perform_calculation_new(params, CapBank_FIDES_model, mode="standard", show_simple=False)
        lifetime, eta_random, list_of_df = perform_calculation_new(params, CapBank_FIDES_model, mode="standard",
                                                                   show_simple=False)
    else:
        print("random failure rate calculated by using FIDES model")
        # using FIDES for random part
        # (calculated for a single capacitor)
        # if OLD_MP:
        #     lifetime, eta_random = perform_calculation(params, mission_profile_dict, mode="fides",
        #                                                CapBank_FIDES_model=CapBank_FIDES_model, show_simple=False)
        # else:   # new mission profile format
        #     lifetime, eta_random, list_of_df = perform_calculation_new(params, CapBank_FIDES_model, mode="fides", show_simple=False)
        lifetime, eta_random, list_of_df = perform_calculation_new(params, CapBank_FIDES_model, mode="fides",
                                                                   show_simple=False)
        print(f"Calculation complete. Result: {lifetime} (lifetime in years, for one capacitor)\n")

    # determination of parameters for PELCA (specification of bathtub model for a replacement unit, i.e. the capacitor bank)
    print("Calculation of parameters for PELCA (for the replacement unit, i.e. the capacitor bank)")
    PELCA_params = calc_Weibull_parameters_for_bank(params, lifetime, eta_random)

    print("PELCA parameters:")
    # Note: eta_random & eta_wearout can contain a list of values
    print(f" Early failure (sigma, year): {PELCA_params['eta_early']:.2f}") # Early failure (sigma, year)
    print(f" Early failure (beta): {PELCA_params['beta_early']:.2f}")       # Early failure (beta)
    print(" Random failure (sigma, year): ", PELCA_params['eta_random'])    # Random failure (sigma, year)
    print(f" Random failure (beta): { PELCA_params['beta_random']:.2f}")    # Random failure (beta)
    print(" Wear-out failure (sigma, year): ", PELCA_params['eta_wearout']) # Wear-out failure (sigma, year)
    print(f" Wear-out failure (beta): { PELCA_params['beta_wearout']:.2f}") # Wear-out failure (beta)

    # update of result sheet
    print("\nupdate of result sheet\n")
    write_result(params, excel_path, result_sheet, lifetime, PELCA_params)

    # **************
    # optional plots
    # **************
    if plot_CDF_enabled==1 or plot_bathtub_enabled==1 or plot_lifetime_mission_profile_enabled==1 or plot_mission_profile_enabled==1:
        print("drawing requested graphs")

    # plot CDFs
    if plot_CDF_enabled==1:
        # neglecting (low) early failure rate
        max_duration = max(lifetime, [30.0] * len(lifetime)) # display at leat 30 years
        plot_cdf("Capacitor bank", max_duration, PELCA_params)

    # plot hazard functions
    if plot_bathtub_enabled==1:
        #* remark:
        # here the early failure rate is considered (fixed parameters: beta=0.6 / gamma=3424)
        # => slightly impact cdf
        plot_bathtub_mission_profiles("capacitor", lifetime, PELCA_params)

    #plot lifetime for the different mission profiles (lifetime of one capacitor - all capacitors supposed to age similarly)
    if plot_lifetime_mission_profile_enabled==1:
        plot_lifetime_mission_profile("capacitor", lifetime)

    # plot a representation of the different mission profiles
    # if OLD_MP:
    #     if plot_mission_profile_enabled==1:
    #         plot_mission_profile(mission_profile_dict, profile_number=1, width_var='life_ratio', height_var='Tx', label_var='PN')
    #         plot_mission_profile(mission_profile_dict, profile_number=2, width_var='life_ratio', height_var='Tx', label_var='PN')
    #         plot_mission_profile(mission_profile_dict, profile_number=3, width_var='life_ratio', height_var='Tx', label_var='PN')
    #         plot_mission_profile(mission_profile_dict, profile_number=4, width_var='life_ratio', height_var='Tx', label_var='PN')
    #         plot_mission_profile(mission_profile_dict, profile_number=5, width_var='life_ratio', height_var='Tx', label_var='PN')
    # else:
    #     if plot_mission_profile_enabled==1:
    #         plot_new_mission_profiles(CapBank_FIDES_model, width_var='life_ratio', height_var='Tx', label_var='PN')
    if plot_mission_profile_enabled==1:
        plot_new_mission_profiles(CapBank_FIDES_model, width_var='life_ratio', height_var='Tx', label_var='PN')

# ====================================================================================================================
    # add thermal data into Excel file

    # Build the aggregated dataframe
    aggregated = []
    for mission_id, df in list_of_df:
        tmp = df.copy()
        tmp.insert(0, "mission_id", mission_id)  # keep the origin
        aggregated.append(tmp)

    aggregated_df = pd.concat(aggregated, ignore_index=True)

    # ---  Replace only the aggregated sheet; keep other sheets intact ---
    write_aggregated_thermal_sheet(aggregated_df, filepath=excel_path, sheet_name="thermal_data")

    # for mission_id, mission_df in list_of_df:
    #    append_df_to_excel(mission_df, filepath=excel_filename, sheet_name="thermal_data", mission_id=mission_id)

    # calculate avg power (per mission profile)
    #aggregated_df['cap_bank_losses'] / aggregated_df['operating_phase']

    avg_power = (
        aggregated_df.loc[aggregated_df['operating_phase']]  # keep only True rows
        .groupby(aggregated_df['MP'].ffill())['cap_bank_losses']  # group by MP blocks (assign each row to the corresponding MP block)
        .mean() # computes average within each MP, using only valid rows
    )

    print("avg power: ", avg_power)

    print("evaluate_capacitor_bank_reliability: finished!")

    # ===================================================================================================================
    return

# test
#if __name__ == "__main__":
#    evaluate_capacitor_bank_reliability('../cap_data.xlsx')


if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) == 2:
        # Normal case: executed in module with Excel file path as argument
        excel_file = sys.argv[1]
    else:
        # IDE case: use the workbook stored next to this module
        from common import __version__
        excel_file = Path(__file__).resolve().parent / "data" / f"PELCA_Reliability_v{__version__}_CapacitorBank.xlsx"
        print(">>> Running from IDE, using:", excel_file)

    evaluate_capacitor_bank_reliability(excel_file)


