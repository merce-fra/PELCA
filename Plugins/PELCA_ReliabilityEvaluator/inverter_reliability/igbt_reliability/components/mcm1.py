# -*- coding: utf-8 -*-
"""\brief Calculate reliability factors for multi-chip module approximations.

This module is part of the PELCA reliability evaluator.
"""

# -*- coding: utf-8 -*-
"""


"""

# hybrid and multichip modules
# evaluation of operations

# neglected failure rate associated with the external connections (mass of module not supported by PCB...)
# <focus on internal failure>

import numpy as np
import math
from inverter_reliability.igbt_reliability.components.power_semi import  PowerSemi


Pi_MCM_process = 1.35    # PI_H&M_process
Pi_process = 4
Pi_PM_ucomponent = 1.25

Pi_placement     = 1.8  # Analogue power interface  (1.8) or non-interface function (1.6)
Pi_application_i = 1    # normally comes from mission profile, but constant here
Pi_ruggedising   = 1.7  # default value
Csensitivity     = 5.5

# 2.39 if Pi_placement=1.6 / 2.65 if Pi_placement=1.8
Pi_induced_i     =  (Pi_placement * Pi_application_i * Pi_ruggedising)**(0.511*np.log(Csensitivity)) # normally one per phase (simplified here)

# calculation of Pi_thermal for active components (p199, FIDES 2022)
# Tj in degC
def calc_Pi_thermal(Tj):
    """calculates the factor Pi_thermal for given junction temperature."""
    return np.exp(11604 * 0.7 * (1/293 - 1/(Tj+273)))

def calc_Pi_TCY_case(T_phase, N_cy_i, T_max_cycling_i, delta_T_cycling_i):
    """Calculate pi t c y case."""
    Pi_TCY_case = (12 * N_cy_i/T_phase) * (delta_T_cycling_i/20)**4     * np.exp(1414*((1/313) - (1/(T_max_cycling_i+273))))
    return   Pi_TCY_case
# same as PiTCy package ?

def calc_lambda_chip(lambda0_th, S, N, Pi_thermal, Pi_TCy_case):
    # Pi_thermal function of die temperature
    # Pi_TCY_case function of thermal cycles (Ncy, deltaT_cycling, Tmax_cycling)
    # S: individual surface area of chip in mm2
    """Calculate lambda chip."""
    lambda0_chip_TCy = 0.011
    C_moulding = 2 # for epoxy moulding
    d = 0.1 # discrete circuit (IGBT or diode die - not integrated circuit)
    C_chip_surface = (1 + S**d)
    # p 185
    lambda_chip = (lambda0_th * np.sqrt(N) * Pi_thermal) + (lambda0_chip_TCy * C_moulding * C_chip_surface * Pi_TCy_case)
    return lambda_chip
# note in our case dies are very large compared to examples provided in FIDES guide (see p185)

def calc_Pi_RH(RH_ambient, Tambient):
    """ calculates Pi_RH related to impact of humidity & temperature """
    Pi_RH = (RH_ambient/70)**4.4 * np.exp(11604*0.9*((1/293) - (1/(Tambient+273))))
    return Pi_RH

def calc_Pi_ME(Grms):
    """calculates the factor Pi_ME (mechanical) as function of vibrations."""
    return (Grms/0.5)**1.5

# failure rate of internal wiring
def calc_lambda_wiring(Nb_wires, Pi_RH, Pi_TCy):
    """calculates lambda_wiring (impact of internal wirebonds...)."""
    lambda0_wiring = 1.04 * 10**(-4) * Nb_wires**0.93
    C_moulding=2
    C_hermeticity = 1 # molded
    lamda0_CHIP_RH = 7.01 * (10**-7) * Nb_wires**2.41
    gamma_TCy = 0.65
    lambda_wiring = lambda0_wiring * (  C_moulding * gamma_TCy * Pi_TCy
                                      + lamda0_CHIP_RH * C_hermeticity * Pi_RH)
    # note: no term c_particle * gamma_ME * Pi_ME,  since c_particle=0 (molded)
    return lambda_wiring


# failure rate of substrate
def calc_lambda_CS(S_case, Pi_TCy_case, Pi_ME, Pi_RH, Pi_chemical):
    """ calculates lambda_CS related to case & substrate """
    # Scase : surface of module in cm2
    Pi_class = 1 # minimum conductor width (um) / minimum spacing between conductors or pads (um)
    Pi_techno_substrate = 0.25 # ceramic
    N_layers = 1

    # alumina substrate with moulding
    lambda0_substrate = 2.08e-4 # 2.08*10**(-4)
    b = 0.93
    gamma_TCy = 0.6
    gamma_ME = 0.35
    gamma_RH = 0.04
    gamma_chemical = 0.01
    C_ME = 1 + 0.1 * np.sqrt(S_case)

    N_tracks = 5
    lambda0_CS = lambda0_substrate * N_layers**(1/2) * (N_tracks**b / 2) * Pi_class * Pi_techno_substrate

    lambda_CS = lambda0_CS * (gamma_TCy * Pi_TCy_case
                              + C_ME * gamma_ME * Pi_ME
                              + gamma_RH*Pi_RH
                              + gamma_chemical*Pi_chemical)
    return lambda_CS



# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# specific to power module
# constants related to considered MCM (equivalent to reference_module power module)
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Scase = 75.64 # cm2
# wiring related

Nb_wires = 310+5 # number of aluminum wirebonds: 310 (+ 5 strips?)
# note by default: Nbwires = 2.9*NbI/O for MCM  (far less than actual number here...)
# nb_ios : 7 control terminals / 4 power terminals (to count?) => Nbwires = 20.3  .. 31.9
# Nb_wires = 2.9 * 7 # no significant impact on calculated MTBF

# surfaces of dies
S_diode = 120    # mm2
S_igbt  = 166.75 # mm2
Nb_diode = 3
Nb_igbt = 3

# calc_lambda_MCM_reference_module
def MCM_fit_rate_calc(profile_data, params, DeviceParams, debug_log=False, use_iec_temp=True):
    """

    :param profile_data: mission profile
    :param params: global parameters
    :param DeviceParams: semiconductors parameters
    :return: fit rate of power module
    """
    reference_module = PowerSemi(DeviceParams)

    weighted_elements_stress_sum_profile = 0

    # --- LOOP THROUGH EACH PHASE [segment] WITHIN THE CURRENT MISSION PROFILE ---
    for idx in range(len(profile_data)):
        #  *** Extract inputs for the current phase (segment) of mission profile ***

        if debug_log:
            # debug msg
            print(f"\nMCM_fit_rate_calc: processing segment {idx} of mission profile")

        # *** get parameters for current segment of mission profile ***
        life_ratio_i      = profile_data['life_ratio'].to_numpy()[idx] # related to Hours_per_Year_i
                                                                       # Hours_per_Year_i = life_ratio_i * 8760 (t_total)
        Operating_Phase_i =  profile_data['Operating_Phase'].to_numpy()[idx]

        if Operating_Phase_i == False:
            if debug_log:
                print("MCM_fit_rate_calc: this segment is not an operating phase")
            # no active deltaT of dies during operation : no thermal simulation to do
            # only the slow passive deltaT specified in mission profile are considered (delta_T_cycling, T_max_cycling, N_cy)

        Rel_speed_i       =  profile_data['Rel_speed'].to_numpy()[idx]
        # Rel_speed_i must not be too low
        if Rel_speed_i<0.01:
            print(f"Rel_speed_i ({Rel_speed_i}) too small! Limited to 1%")
            Rel_speed_i=0.01 # limited to 1%

        Rel_torque_i      =  profile_data['Rel_torque'].to_numpy()[idx] # 0 .. 1

        T_i = profile_data['Tx'].to_numpy()[idx] # ambient temperature for power modules (considered heatsink air flow temperature here)
        # heatsink temperature will be calculated using this parameter

        # not what we need in FIDES formula: we need case temperature variations!
        delta_T_cycling_i = profile_data['delta_T_cycling'].to_numpy()[idx]  # variation of ambient temperature    during a cycle within current phase of mission profile
        T_max_cycling_i   = profile_data['T_max_cycling'].to_numpy()[idx]    # maximum ambient temperature reached during a cycle ...

        Hours_per_Year_i  = profile_data['Operating_Hours_per_Year'].to_numpy()[idx]  #  t_annual ? duration of operating phase over a year (hours)
        T_phase = Hours_per_Year_i

        N_cy_i            = profile_data['N_cy'].to_numpy()[idx]            # N_annual_cy : number of cycles assocated with each cycling phase over a year (cycles)
        theta_cy_i        = profile_data['theta_cy'].to_numpy()[idx]        # cycle duration (hours)
                                                                            # now called t_phase in FIDES 2022 (?)

        Pi_application_i  = profile_data['Pi_application'].to_numpy()[idx]  # ignored:  the constant internPiApplication is used instead in calculation of FIT rate
        #Pi_type?

        RH_ambient_i      = profile_data['RH_ambient'].to_numpy()[idx]      # ... always the same value = 0.3 (30%)
        G_RMS_i           = profile_data['G_RMS'].to_numpy()[idx]           # stress associated with each random vibration phase .. always the same value = 0.3 G

        # note: T_i is supposed to be "ambient temperature" of component =>
        # in mission profile it is the air flow temperature for heatsink...

        # update with case temperature parameters to evaluate reliability
        T_i = profile_data['Tc'].to_numpy()[idx]
        delta_T_cycling_i = profile_data['delta_Tc_cycling'].to_numpy()[idx]
        T_max_cycling_i = profile_data['Tc_max_cycling'].to_numpy()[idx]

        # ==============================================================================================================
        #  Perform electro-thermal simulation
        #  => Not needed any more - done once and for all before evaluating reliability
        # ==============================================================================================================
        # Tj_D, deltaT_D, Tj_D_pwm, deltaT_D_pwm, Tj_Q, deltaT_Q, Tj_Q_pwm, deltaT_Q_pwm = reference_module.calc_TJ_components(params, Rel_torque_i, Rel_speed_i, T_i) # life_ratio_i, load_factor
        # temperatures have been evaluated by previous electro-thermal simulation
        #
        #   => Tj_diode, Tj_IGBT
        #   Remark: All diodes within power module are supposed to have the same avg temperature
        #   Same thing for IGBT
        if use_iec_temp:
            Tj_D = profile_data['Tj_D'].to_numpy()[idx]  # avg temperature of diode determined in that phase
            Tj_Q = profile_data['Tj_Q'].to_numpy()[idx]  # avg temperature of igbt determined in that phase
        else:
            # temperatures estimated using "pwm" simulation
            Tj_D = profile_data['Tj_D_pwm'].to_numpy()[idx]
            Tj_Q = profile_data['Tj_Q_pwm'].to_numpy()[idx]


        Tj_D1 = Tj_D2 = Tj_D # both diodes have the same averaged temperature during whole phase of mission profile
        if Operating_Phase_i:
            Pi_thermal_D1 = calc_Pi_thermal(Tj_D1) # function of junction temperature of die
        else:
            Pi_thermal_D1 = 0

        Pi_TCy_case_D1 = calc_Pi_TCY_case(T_phase, N_cy_i, T_max_cycling_i, delta_T_cycling_i)
        #Pi_thermal_D2 = Pi_thermal_D1
        #Pi_TCy_case_D2 = Pi_TCy_case_D1

        Tj_Q1 = Tj_Q2 = Tj_Q
        if Operating_Phase_i:
            Pi_thermal_T1 = calc_Pi_thermal(Tj_Q1) # function of junction temperature of die
        else:
            Pi_thermal_T1 = 0

        Pi_TCy_case_T1 = calc_Pi_TCY_case(T_phase, N_cy_i, T_max_cycling_i, delta_T_cycling_i)
        #Pi_thermal_T2 = Pi_thermal_T1
        #Pi_TCy_case_T2 = Pi_TCy_case_T1
        # ==============================================================================================================

        #  *** evaluate FIDES formulas ***

        # (note: Pi_application_i comes from Excel sheet but is expected to be constant for the whole mission profile)
        Pi_induced_i = (Pi_placement * Pi_application_i * Pi_ruggedising) ** (0.511 * math.log(Csensitivity))
        # from 1 to 100 (1=best case)

        #   diode (see p 136 for lambda0_th value)
        lambda_D1 = calc_lambda_chip(lambda0_th=0.1574, S=S_diode, N=Nb_diode, Pi_thermal=Pi_thermal_D1, Pi_TCy_case=Pi_TCy_case_D1)
        lambda_D2 = lambda_D1

        #   igbt (see p 139 for lambda0_th value)
        lambda_T1 = calc_lambda_chip(lambda0_th=0.56, S=S_igbt, N=Nb_igbt, Pi_thermal=Pi_thermal_T1, Pi_TCy_case=Pi_TCy_case_T1)
        lambda_T2 = lambda_T1

        # ? temperature of package... / deltaT of package of dies inside?
        # PiTCy package same as _Pi_TCY_case ?
        Pi_TCy_package = calc_Pi_TCY_case(T_phase, N_cy_i, T_max_cycling_i, delta_T_cycling_i)

        # Tambient is supposed to be the heatsink surface temperature
        Tambient = T_i

        if Operating_Phase_i == True:
            Pi_RH = 0
        else:
            Pi_RH = calc_Pi_RH(RH_ambient_i, Tambient)

        lambda_wiring = calc_lambda_wiring(Nb_wires, Pi_RH, Pi_TCy_package) # wires and strips (aluminum)

        Pi_ME = calc_Pi_ME(G_RMS_i) # could be ignored

        Pi_chemical = 0 # ignored

        # case substrate
        lambda_CS = calc_lambda_CS(Scase, Pi_TCy_package, Pi_ME, Pi_RH, Pi_chemical)

        # failure rate associated with the external connections
        # the module is fixed to heatsink with screws (not supported by a PCB)
        # => lambda0_ME does not make sense here (impact of module mass? ...)
        lambda_ext_connections = 0

        #     accum weighted elements stress
        weighted_elements_stress_sum_profile = ((  lambda_T1
                                                 + lambda_T2
                                                 + lambda_D1
                                                 + lambda_D2
                                                 + lambda_wiring
                                                 + lambda_CS) * life_ratio_i * Pi_induced_i
                                         + weighted_elements_stress_sum_profile)


    # determine lambda_MCM (module)
    lambda_MCM =  weighted_elements_stress_sum_profile * Pi_MCM_process * Pi_process

    print("lambda total of power module", lambda_MCM)

    return lambda_MCM


