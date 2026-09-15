# -*- coding: utf-8 -*-
"""\brief Estimate junction temperatures from IEC loss calculations.

This module is part of the PELCA reliability evaluator.
"""

from  inverter_reliability.igbt_reliability.calculations.IEC_TC_22_calc_losses import IEC_TC_22_calc_losses
from  inverter_reliability.igbt_reliability.components.DeviceParameters import DeviceParameters
from  inverter_reliability.igbt_reliability.thermal.simulate_thermal_profile import simulate_thermal_profile

import matplotlib.pyplot as plt

from .calc_op_point import calc_Iout, calc_active_power, calc_PF
import numpy as np


# ==================================================================================================================================================
# calculation of output inverter losses / IGBT, diodes Tj  <for a given segment of mission profile>

# to add: handle number of parallel modules (implicitly considered = 2 here)

# note: device_params (instance of DeviceParameters) used to enable calculation of UT_th, UT_r, ...
# <those parameters are not needed any more in parameters sheet of Excel file>
# note: Tx: ambient temperature (the one of air used to cool heatsink)
def calc_Tj_values_IEC(params, device_params: DeviceParameters,  Rel_torque_i, Rel_speed_i,  Tx,
                       display_sim=False,
                       plot_cond_currents_en=True,
                       log_losses=False): # life_ratio, load_factor
    """
    calculation of losses using formula from IEC_TC_22_calc_losses in an attempt to determine the deltaT of dies

    Parameters
    ----------
    params : TYPE
        parameters.
    device_params : DeviceParameters
        specific parameters of power module.
    Rel_torque_i : float
        relative torque (0 .. 1). <from current phase of mission profile>
    Rel_speed_i : float
        relative speed (0.01 .. 1). <from current phase of mission profile>
    Tx : float
        air flow temperature of heatsink <from current phase of mission profile>
    display_sim : bool, optional
        DESCRIPTION. The default is True.
    plot_cond_currents_en : bool, optional <not used>
        DESCRIPTION. The default is True.
    log_losses : bool, optional
        DESCRIPTION. The default is False.

    Returns
    -------
    Tj_diode, Tj_Q, deltaT_D, deltaT_Q (float)

    """
    # notes:
    # * if the use of the analytic formula provided in this standard provide accurate enough result,
    # it would accelerate the processing (no need to simulate at "PWM level" the operation of inverter, *
    # which is time-consuming)
    # * plot_cond_currents_en not used

    # <old mission profile definition:
    # * Life ratio is the percentage of time spent in a given segment (of mission profile)
    # * load_factor is the % of output power with respect to PN
    # >

    # remarks:
    # <the duration is not specified here... >
    # the output frequency is not specified either - considered implicitly = 50 Hz used for thermal simulation
    # might be added as parameter in params sheet

    # * Tcase, i.e. temperature of baseplate of power module ("ambient" for power module) depends on load
    # => can be estimated by heatsink thermal model fed with losses of power module (air flow temperature : Ta)


    # general constants
    # remarks: a number of parameters are fixed (no change from one mission profile to another)

    # input data
    #PN       = params.get('PN', 200000)             # nominal (active) output power
    Udc      = params.get('Udc', 540)               # CDM DC link voltage <can be calculated>
    # Vin      =  params.get('Vin', 230)            # volt RMS
    # Udc = calc_Vdc(Vin)                           #
    Ir_out   = params.get('Ir_out', 363)            # rated CDM output current, RMS value # Default to 490 if parameter is missing <light (or Heave?) duty, i.e max current for for short period of time>

    #PN_i     = PN * load_factor # PN* [PN_percent]  # load_factor from mission profile

    # pb in very low frequency...
    if Rel_speed_i<0.01:
        Rel_speed_i=0.01
        print("calc_Tj_values_IEC: Rel_speed_i adjusted to min value")

    # fout = Rel_speed * 50

    # determination of operating point
    active_Pout =  calc_active_power(Rel_torque_i, Rel_speed_i) # shouldn't be 0 if Rel_torque_i!=0 (even if Rel_speed_i=0) => torque hold consumes active power
    # Rel_Torque=1 Rel_speed_i=0.25 => active_Pout = 54027

    fsw      = params.get('fsw', 2000)              # 4 000 for a CDM up to 90 kW / 2 000 for a CDM above 90 kW

    # override of few default parameters
    m = min(Rel_speed_i, 1) # >0 .. 1 : modulation index, identical to the relative CDM output freq up to rated output freq
    # should be derived from operating point  (to specify in mission profile: relative speed)
    # 0 .. 50Hz   => m = fout/50
    # above 50 Hz => m = 1

    # use converter.find_elec_op_point  get_rel_output_current  => to calculate Iout
    #                                   get_displacement_factor => to calculate PF

    # PF & m can be derived from rel_torque and speed
    PF = calc_PF(Rel_torque_i) # output voltage power factor

    Vout_rms = 230 * m # inverter phase to "neutral" output voltage   # output voltage rms for Mi ~ 0.7 >

    # inverter output phase current
    Iout     = calc_Iout(active_Pout, Vout_rms, PF, Udc) # current (rms value) shared by power modules connected n //

    if log_losses:
        print("calc_Tj_values_IEC: active_Pout=", active_Pout)
        print("calc_Tj_values_IEC: Iout=", Iout)
        print("calc_Tj_values_IEC: PF=", PF)
        print("calc_Tj_values_IEC: Vout_rms=", Vout_rms)


    # configuration / modularity of inverter stage
    nb_parallel_sw = params.get('nb_parallel_sw', 2) # number of (half-bridge) power modules connected in //

    # heatsink thermal resistance (for a power module)
    Rth_heatsink = params.get('Rth_heatsink', 0.2085)

    # creates an instance of class IEC_TC_22_calc_losses
    HB_losses = IEC_TC_22_calc_losses(fsw=fsw, PF=PF, m=m, nb_parallel_modules=nb_parallel_sw)
    # validity: pwm freq >= 15 ... 20 x fundamental freq of motor current : ok here (fout=50 Hz, fsw>=2 khz > foutx20)

    # Note: typical parameter values come from IEC-TC_1.pdf and must be adapted to the selected power module.

    # parameters for losses calculations

    Tj_igbt = 80   # assumption - initial guess
    Tj_diode = 80  #

    # ========================================================================================================
    # calculation of currents (takes into account the topology of system: i.e. modules connected in // or not)
    # nb_modules: 1, 2, ...
    # ========================================================================================================

    # Iout                       # output current (flowing through an equivalent "switch" (IGBT), nb_parallel_sw modules in //))
    # <note: the fact that a single "IGBT" is composed of three dies in // in a module is not considered here>

    Iout_rms_module = Iout/nb_parallel_sw  # conduction current per power module (Iout considered shared equally between modules connected in //)


    # performs a few iteration until Tj_diode and Tj_IGBT stabilizes
    for i in range(6):  # <6 iteration has been checked as sufficient>

        # debug
        # print(f"calc_Tj_value: Tj_igbt: {Tj_igbt} Tj_diode: {Tj_diode}")

        # parameters UT_th, UT_r, YD_th, UD_r, ET and ED must be calculated depending on operating point:
        # i.e. function of current, dc bus voltage, junction temperature...

        # (individual) transistor parameters for on state (conduction) losses calculation

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # warning! function UT_th internally divides the parameter 'current' (Iout) by nb_parallel_sw... same for UT_r, UD_th, UD_r
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # => For conduction losses, the rms output current of inverter (Iout)  is given as parameter
        UT_th = device_params.UT_th(Tj_igbt, Iout_rms_module*nb_parallel_sw) # Threshold voltage of the power transistor (IGBT)
        UT_r  = device_params.UT_r(Tj_igbt,  Iout_rms_module*nb_parallel_sw) # reference power module : Vcesat_terminals = 1.90V (@600A, Tvj=150degC)

        # diode parameters for on state losses calculation
        UD_th = device_params.UD_th(Tj_diode, Iout_rms_module*nb_parallel_sw)  # Threshold voltage  of the power diode
        UD_r  = device_params.UD_r(Tj_diode,  Iout_rms_module*nb_parallel_sw)  # On state voltage of the power diode at rated CDM output current

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # for switching losses, the current flowing in one module is given as parameter
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # peak current or rms current to consider? => rms current considered

        # # (individual) transistor switching losses calculation (J/VA)
        # #ET = device_params.ET(Tj_igbt, Udc, Iout_rms_module, device_params.Rg)*1e-3  # Switching loss energy of the power transistor (IGBT) per volt and per ampere
        #
        # # losses at DC current equivalent to half-period of AC output current
        # ET = device_params.ET(Tj_igbt, Udc, np.sqrt(2)*Iout_rms_module/np.pi, device_params.Rg)*1e-3  # Switching loss energy of the power transistor (IGBT) per volt and per ampere

        # (individual) transistor switching losses calculation (J/VA)
        # almost no error for switching loss estimation whater method employed
        ET = device_params.ET(Tj_igbt, Udc, Iout_rms_module,
                              device_params.Rg) * 1e-3  # Switching loss energy of the power transistor (IGBT) per volt and per ampere

        # losses at DC current equivalent to half-period of AC output current (?)
        # ET = device_params.ET(Tj_igbt, Udc, np.sqrt(2) * Iout_rms_module / np.pi,
        #                      device_params.Rg) * 1e-3  # Switching loss energy of the power transistor (IGBT) per volt and per ampere

        # for diode switching losses calculation (J/VA)
        # less difference with pwm estimation with this formula...
        ED = device_params.ED(Tj_diode, Udc, Iout_rms_module,
                              device_params.Rg) * 1e-3  # Switching loss energy of the power diode per volt and per ampere

        # losses at DC current equivalent to half-period of AC output current
        # with a bit of fitting...
        ED = device_params.ED(Tj_diode, Udc, 0.95 * Iout_rms_module,
                              device_params.Rg) * 1e-3  # Switching loss energy of the power diode per volt and per ampere


        # calculation of losses according to IEC_TC_22 - for one diode and one transistor  <IEC-TC_1.pdf (p85...)>
        # calculation of avg losses affecting one IGBT, one diode in a HB during a period of output current

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # to add: selector depending on module configuration (single module / 2 x HB...) => specify number of HB in //
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # At present topology with 2 HB in // considered in calc_losses
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # losses in one half-bridge (on losses of IGBT, on losses of diode, switching losses of IGBT, switching losses of diode)
        PL_on_T_HB, PL_on_D_HB, PL_sw_T_HB, PL_sw_D_HB = HB_losses.calc_losses(m, Iout, Ir_out, Udc, UT_th, UT_r, UD_th, UD_r, ET, ED)

        # these are losses for one diode / one transistor => to multiply by the number of transistors in 3-phase inverter
        # 1 HB module = 2 diodes / 2 IGBTs
        # 3 phases inverter => 3 legs
        # <1 leg =  nb_parallel_sw * modules in parallel>

        # output inverter total losses
        #PL_inverter = 2*3*(PL_on_T + PL_on_D + PL_sw_T + PL_sw_D)                           # without modules in //
        #PL_inverter_parallel_HB
        total_loss = 2*3*nb_parallel_sw*(PL_on_T_HB + PL_on_D_HB + PL_sw_T_HB + PL_sw_D_HB) # with nb_parallel_sw HB in //
        semicond_powers = {
            "PL_on_T_HB": PL_on_T_HB,
            "PL_on_D_HB": PL_on_D_HB,
            "PL_sw_T_HB": PL_sw_T_HB,
            "PL_sw_D_HB": PL_sw_D_HB,
            "total_loss": total_loss
        }

        # update of junction temperatures

        # heatsink temperature under a power module considered the Tcase of that module
        # => Th = Tambient (heatsink) + Rth_heatsink * module_losses
        # One module contains 2*IGBT + 2*diodes => module_losses (avg) = 2 * (losses of one IGBT + losses of one diode)
        Th = Tx + Rth_heatsink * 2 * (PL_on_T_HB+PL_sw_T_HB + PL_on_D_HB+PL_sw_D_HB) # temperature of heatsink temperature below one HB module
        # here heatsink temperature is supposed to have reached steady state (i.e. operating phase long compared to time constant of heatsink)

        # appears sufficient to evaluate avg temperature considering the avg losses of IGBT
        Tj_igbt = Th + (PL_on_T_HB+PL_sw_T_HB)*device_params.Rth_jc_Q * 1e-3 # igbt junction temperature


        if Tj_igbt>125:
            print("calc_Tj_values_IEC: IGBT overtemperature")

        # appears sufficient to evaluate avg temperature considering the avg losses of diode
        Tj_diode = Th + (PL_on_D_HB+PL_sw_D_HB)*device_params.Rth_jc_D * 1e-3 # diode junction temperature


    # debug
    if log_losses:
        print("calc_Tj_values_IEC: IGBT total losses:  PL_on_T_HB + PL_sw_T_HB:", PL_on_T_HB + PL_sw_T_HB) #
        print("calc_Tj_values_IEC: Diode total losses: PL_on_D_HB + PL_sw_D_HB:", PL_on_D_HB + PL_sw_D_HB) #

        # display final estimation
        # detail of losses
        print("calc_Tj_value_IEC: (one IGBT)  on losses:" , PL_on_T_HB, "W")
        print("calc_Tj_value_IEC:             sw losses:" , PL_sw_T_HB, "W")
        print("calc_Tj_value_IEC: (one diode) on losses:" , PL_on_D_HB, "W")
        print("calc_Tj_value_IEC:             sw losses:" , PL_sw_D_HB, "W")
        print(f"calc_Tj_value_IEC: total losses for the full inverter ({2*3*nb_parallel_sw} switches= {total_loss} W)") # 2337W (fsw=2 khz)

    # ==================================================================================================================================================

    # calculation of Tj thermal increase
    # "For active components, the temperature stress model uses the component junction temperature"

    # Parameters from the selected power-module datasheet.
    # junction to case thermal resistances (unusual units: not degC/W but K/kW)
    #Rth_jc_Q = 48 # K/kW
    #Rth_jc_D = 76 # K/kW
    # [case here designates the baseplate]

    # VERY (far too?) simple model - considering that steady state is reached

    # assumptions:
    #              no thermal coupling considered between dies
    #Calculation of each die temperature, i.e. increase (transistor or diode) with respect to case due to losses
    # <Tj = Tc + Rjc*Pdissipated >

    # for non-parallel power module:
        # Tj_diode = Tcase + Rth_jc_D * (PL_on_D + PL_sw_D) * 1e-3 # need to convert powers in kW
        # Tj_Q = Tcase + Rth_jc_Q * (PL_on_T + PL_sw_T) * 1e-3

    # for 2 power modules in parallel (power in HB considered)


    # debug
    if log_losses:
        print("calc_Tj_value_IEC: steady state avg temperature of diode:",Tj_diode)
        print("calc_Tj_value_IEC: steady state avg temperature of igbt:", Tj_igbt)

    # calculation of deltaT
    # the deltaT ("low frequency" at Fout) must be determined by feeding the losses to a thermal model
    # that represents the transient impedance


    # -------------------------------------
    # Foster model parameters (order 4)
    # -------------------------------------
    Rth_IGBT  = device_params.Rth_IGBT
    Cth_IGBT  = device_params.Cth_IGBT
    Rth_Diode = device_params.Rth_Diode
    Cth_Diode = device_params.Cth_Diode


    freq = 50.0     # nominal output frequency
    sim_time = 1.0

    # first process the diode

    # losses for the diode
    # Note: losses are multiplied by 2 because the loss formula give the avg value for a full period
    # Here we consider that these losses are present during only during half period / the second half is 0
    # (to have the same avg losses over one period!)

    P_on = (PL_on_D_HB  + PL_sw_D_HB ) * 2      # W
    P_off = 0.0      # W
    if log_losses:
        print("calc_Tj_values_IEC: simulate thermal profile of diode")
    time, Tj_d, metrics =  simulate_thermal_profile(Rth_Diode, Cth_Diode, P_on, P_off, freq*Rel_speed_i, Th, sim_time, display_sim=False)


    Tj_diode = metrics["Tmean (degC)"]   # avg junction temperature of IGBT
    deltaT_D = metrics["DeltaT (K)"]   # deltaT of diode

    # IGBT
    # losses for the IGBT (during conduction period)
    # <factor 2 on losses : same explanation as for diodes>
    P_on = (PL_on_T_HB  + PL_sw_T_HB) * 2      # W
    P_off = 0.0      # W
    if log_losses:
        print("calc_Tj_values_IEC: simulate thermal profile of IGBT")
    time, Tj_Q, metrics =  simulate_thermal_profile(Rth_IGBT, Cth_IGBT, P_on, P_off, freq*Rel_speed_i, Th, sim_time, display_sim=False)


    # could add display of segment number to ease identification of curves
    if display_sim:
        # <display ok when enabled>
        # -----------------------------
        # Display
        # -----------------------------
        plt.figure(figsize=(10, 5))
        plt.plot(time, Tj_d, label='Tj diode (degC)')
        plt.plot(time, Tj_Q, label='Tj IGBT (degC)')
        plt.xlabel('Time (s)')
        plt.ylabel('Junction temperature (degC)')
        plt.title('(IEC) Thermal variation of semiconductor')
        plt.grid(True)
        plt.legend()
        plt.show()

    Tj_Q = metrics["Tmean (degC)"]      # avg junction temperature of IGBT
    deltaT_Q = metrics["DeltaT (K)"]  # deltaT of IGBT

    #return Tj_diode, Tj_Q, deltaT_D, deltaT_Q
    # should return also the heatsink temperature (Tcase for power module) : Th

    # alternative:
    semicond_temperatures = {
         "Tj_diode": Tj_diode,
         "Tj_Q": Tj_Q,
         "deltaT_D": deltaT_D,
         "deltaT_Q": deltaT_Q,
         "Th": Th
    }

    return semicond_temperatures, semicond_powers
    # ========================================================================================================


# only for test (not an electrothermal simulation : Tj = Tx)
def calc_powers_IEC(params, device_params: DeviceParameters, Rel_torque_i, Rel_speed_i, Tx,
                       log_losses=False):

    # input data
    """Calculate powers i e c."""
    Udc = params.get('Udc', 540)  # CDM DC link voltage <can be calculated>
    Ir_out = params.get('Ir_out',
                        363)  # rated CDM output current, RMS value
    #Ir_out = Ir_out * np.sqrt(2)

    if Rel_speed_i < 0.01:
        Rel_speed_i = 0.01
        print("calc_Tj_values_IEC: Rel_speed_i adjusted to min value")
    active_Pout = calc_active_power(Rel_torque_i,
                                    Rel_speed_i)  # shouldn't be 0 if Rel_torque_i!=0 (even if Rel_speed_i=0) => torque hold consumes active power
    fsw = params.get('fsw', 2000)  # 4 000 for a CDM up to 90 kW / 2 000 for a CDM above 90 kW
    m = min(Rel_speed_i,
            1)  # >0 .. 1 : modulation index, identical to the relative CDM output freq up to rated output freq

    PF = calc_PF(Rel_torque_i)  # output voltage power factor
    Vout_rms = 230 * m  # inverter phase to "neutral" output voltage   # output voltage rms for Mi ~ 0.7 >
    Iout = calc_Iout(active_Pout, Vout_rms, PF, Udc)  # current (rms value) shared by power modules connected n //
    nb_parallel_sw = params.get('nb_parallel_sw', 2)  # number of (half-bridge) power modules connected in //

    HB_losses = IEC_TC_22_calc_losses(fsw=fsw, PF=PF, m=m, nb_parallel_modules=nb_parallel_sw)

    # for this evaluation, temperature is supposed constant = Tx
    Tj_igbt = Tx
    Tj_diode = Tx

    Iout_rms_module = Iout / nb_parallel_sw  # conduction current per power module (Iout considered shared equally between modules connected in //)

    # parameters UT_th, UT_r, YD_th, UD_r, ET and ED must be calculated depending on operating point:
    # i.e. function of current, dc bus voltage, junction temperature...

    # (individual) transistor parameters for on state (conduction) losses calculation

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # warning! function UT_th internally divides the parameter 'current' (Iout) by nb_parallel_sw... same for UT_r, UD_th, UD_r
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # => For conduction losses, the rms output current of inverter (Iout)  is given as parameter
    UT_th = device_params.UT_th(Tj_igbt,
                                Iout_rms_module * nb_parallel_sw)  # Threshold voltage of the power transistor (IGBT)
    # (intersection with axis at I=0)
    #UT_th = device_params.UT_r(Tj_igbt,0) # ~ equivalent?

    UT_r = device_params.UT_r(Tj_igbt,
                                Iout_rms_module * nb_parallel_sw)  # reference power module : Vcesat_terminals = 1.90V (@600A, Tvj=150degC)

    # diode parameters for on state losses calculation
    UD_th = device_params.UD_th(Tj_diode, Iout_rms_module * nb_parallel_sw)  # Threshold voltage  of the power diode
    UD_r = device_params.UD_r(Tj_diode,   Iout_rms_module * nb_parallel_sw)  # On state voltage of the power diode at rated CDM output current

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # for switching losses, the current flowing in one module is given as parameter
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # peak current or rms current to consider? => rms current considered

    # (individual) transistor switching losses calculation (J/VA)
    # almost no error for switching loss estimation whatever method employed
    ET = device_params.ET(Tj_igbt, Udc, Iout_rms_module,
                          device_params.Rg)*1e-3  # Switching loss energy of the power transistor (IGBT) per volt and per ampere

    # losses at DC current equivalent to half-period of AC output current (?)
    #ET = device_params.ET(Tj_igbt, Udc, np.sqrt(2) * Iout_rms_module / np.pi,
    #                      device_params.Rg) * 1e-3  # Switching loss energy of the power transistor (IGBT) per volt and per ampere

    # with a bit of fitting... (to better match results obtained with "PWM" simulation)
    # factor sqrt(3)/2 ?
    ET = device_params.ET(Tj_igbt, Udc, 0.866*Iout_rms_module,
                          device_params.Rg)*1e-3  # Switching loss energy of the power transistor (IGBT) per volt and per ampere

    # for diode switching losses calculation (J/VA)
    ED = device_params.ED(Tj_diode, Udc, Iout_rms_module,
                          device_params.Rg) * 1e-3  # Switching loss energy of the power diode per volt and per ampere

    # <losses at DC current equivalent to half-period of AC output current?>
    # with a bit of fitting... (to better match results obtained with "PWM" simulation)
    ED = device_params.ED(Tj_diode, Udc, 0.901*Iout_rms_module,
                         device_params.Rg) * 1e-3  # Switching loss energy of the power diode per volt and per ampere

    # calculation of losses according to IEC_TC_22 - for one diode and one transistor  <IEC-TC_1.pdf (p85...)>
    # calculation of avg losses affecting one IGBT, one diode in a HB during a period of output current


    # losses in one half-bridge (on losses of one IGBT, on losses of one diode,
    #                            switching losses of one IGBT, switching losses of one diode)
    PL_on_T_HB, PL_on_D_HB, PL_sw_T_HB, PL_sw_D_HB = HB_losses.calc_losses(m, Iout, Ir_out, Udc, UT_th, UT_r, UD_th,
                                                                           UD_r, ET, ED)

    # output inverter total losses
    # PL_inverter = 2*3*(PL_on_T + PL_on_D + PL_sw_T + PL_sw_D)                           # without modules in //
    # PL_inverter_parallel_HB
    # 2 IGBT and 2 diodes per HB / at least 3 legs
    total_loss = 2 * 3 * nb_parallel_sw * (
                PL_on_T_HB + PL_on_D_HB + PL_sw_T_HB + PL_sw_D_HB)  # with nb_parallel_sw HB in //

    # debug
    if log_losses:
        print("calc_Tj_values_IEC: IGBT total losses:  PL_on_T_HB + PL_sw_T_HB:", PL_on_T_HB + PL_sw_T_HB)  #
        print("calc_Tj_values_IEC: Diode total losses: PL_on_D_HB + PL_sw_D_HB:", PL_on_D_HB + PL_sw_D_HB)  #

        # display final estimation
        # detail of losses
        print("calc_Tj_value_IEC: (one IGBT)  on losses:", PL_on_T_HB, "W")
        print("calc_Tj_value_IEC:             sw losses:", PL_sw_T_HB, "W")
        print("calc_Tj_value_IEC: (one diode) on losses:", PL_on_D_HB, "W")
        print("calc_Tj_value_IEC:             sw losses:", PL_sw_D_HB, "W")
        print(
            f"calc_Tj_value_IEC: total losses for the full inverter ({2 * 3 * nb_parallel_sw} switches= {total_loss} W)")  # 2337W (fsw=2 khz)


    semicond_powers = {
        "PL_on_T_HB": PL_on_T_HB,
        "PL_on_D_HB": PL_on_D_HB,
        "PL_sw_T_HB": PL_sw_T_HB,
        "PL_sw_D_HB": PL_sw_D_HB,
        "total_loss": total_loss
    }
    return semicond_powers
    # ========================================================================================================
