# -*- coding: utf-8 -*-
"""\brief Estimate junction temperatures from PWM waveform loss calculations.

This module is part of the PELCA reliability evaluator.
"""
from inverter_reliability.igbt_reliability.components.DeviceParameters import DeviceParameters
from inverter_reliability.igbt_reliability.thermal.ThermalModel import ThermalModel, HeatsinkParameters
from inverter_reliability.igbt_reliability.modulator.ModulationStrategy import ModulationStrategy
from inverter_reliability.igbt_reliability.calculations.LossModel import LossModel
from inverter_reliability.igbt_reliability.utils.plot_dataframe import  plot_cond_currents
#from inverter_reliability.igbt_reliability.utils.plot_dataframe import  plot_P_total_semicond, plot_deltaT_devices
from  inverter_reliability.igbt_reliability.thermal.simulate_thermal_profile import simulate_thermal_profile

import numpy as np
import matplotlib.pyplot as plt

from .calc_op_point import calc_Iout, calc_active_power, calc_PF

# rms value of a vector
def rms(y):
    """Run rms."""
    rms = np.sqrt(np.mean(np.square(y)))
    return rms

# called in igbt.py as calc_Tj_values_PWM(params, self.device_params,  life_ratio, load_factor, Tx)...
def calc_Tj_values_PWM(params, device_params: DeviceParameters, Rel_torque_i, Rel_speed_i,  Tx,
                       display_sim=False,
                       plot_cond_currents_en=True,
                       plot_tj_en=True,
                       log_losses=False): # life_ratio, load_factor
    """ calculation of losses at "PWM" level in an attempt to determine the deltaT of dies """


    # to add: specify nominal output frequency (considered implicitly = 50 Hz here )

    # general constants

    # input data
    #PN       = params.get('PN', 200000)            # nominal (active) output power ~ 3*363*230*0.8   (Iout_rms=363A)
                                                    # Sout_nom (apparent power) = 250 kVA = 400*363*sqrt(3)

    Udc      = params.get('Udc', 540)               # CDM DC link voltage <can be calculated as function as input voltage>
    #Udc = calc_Vdc(230)                            # Vin (230V rms here) could be in parameters

    #Ir_out   = params.get('Ir_out', 363)            # rated CDM output current, RMS value # Default to 490 if parameter is missing <only during light (?) duty, i.e max current for for short period of time>

    #PN_i     = PN * load_factor # PN* [PN_percent]  # load_factor from (former) mission profile :  % of output power with respect to PN

    if Rel_speed_i<0.01:
        Rel_speed_i=0.01 # can not be 0 (considered V/F control)
        print("Rel_speed_i adjusted to min value")

    # determination of operating point
    active_Pout =  calc_active_power(Rel_torque_i, Rel_speed_i) # shouldn't be 0 if Rel_torque_i!=0 (even if Rel_speed_i=0) => torque hold consumes active power

    # Vin      =  params.get('Vin', 230)            # volt RMS

    fsw      = params.get('fsw', 2000)              # 4 000 for a CDM up to 90 kW / 2 000 for a CDM above 90 kW

    # override of few default parameters

    m = min(Rel_speed_i, 1) # >0 .. 1    modulation index, identical to the relative CDM output freq up to rated output freq
    # should be derived from operating point  (to specify in mission profile: relative speed)
    # 0 .. 50Hz   => m = fout/50
    # above 50 Hz => m = 1

    # Vout_rms and Iout should be determined considering also the specification of op point in mission profile
    # not simply based on PN_i but rather fout_i (or rel_speed_i) / Rel_Torque_i =>
    # use converter.find_elec_op_point  get_rel_output_current  => to calculate Iout
    #                                   get_displacement_factor => to calculate PF

    # PF & m can be derived from rel_torque and speed
    PF = calc_PF(Rel_torque_i) # output voltage power factor

    Vout_rms = 230 * m # inverter phase to "neutral" output voltage (rms)

    # inverter output phase current
    Iout     = calc_Iout(active_Pout, Vout_rms, PF, Udc) # (current shared by power modules connected n //)

    # configuration / modularity of inverter stage
    nb_parallel_sw = params.get('nb_parallel_sw', 2) # number of (half-bridge) power modules connected in //

    #device_params   = DeviceParameters(params)   # parameters of devices for losses calculation
    heatsink_params = HeatsinkParameters() # parameters of heatsink thermal model (simple first order foster network)

    Rth_heatsink = params.get('Rth_heatsink', 0.2085)

    # methods to evaluate heatsink temperature as well as semiconductors of modules
    thermal_model   = ThermalModel(device_params, heatsink_params) # TM

    # creation of waveforms for the current operating point
    M = ModulationStrategy()

    # generates signals (in a DataFrame) considering current equally shared between nb_parallel_sw power modules)
    Iout_rms_module = (Iout / nb_parallel_sw) # part of current handled by a SINGLE power module
    results = M.generate_waveforms(I_out_rms=Iout_rms_module, cos_phi=PF, f_out=50*m, f_sw=fsw, NB_PERIODS = 1)

    # <=> if 2 modules are connected in //, the same current will flow in the other power module
    # [and the total losses will be doubled]

    # for calculation of losses
    LM = LossModel(device_params)

    # first determines the conduction currents (in 3 x HB)
    results = LM.calculate_conduction_currents(results)

    if plot_cond_currents_en:
        # this plot does not work correctly
        plot_cond_currents(results) # display (plot) the conduction currents flowing into the elements

    # calculate the losses

    # <requires to find right operating electrical/thermal point>
    # Need to perform a few iteration until Tj_diode and Tj_IGBT stabilizes

    # all diodes are supposed to have very similar temperature / same for IGBTs
    Tj_igbt = 80   # assumption - initial guess
    Tj_diode = 80  #

    # should be some iteration until T_j_est is adjusted
    for i in range(6):

        results = LM.calculate_total_losses(data=results, f_sw=fsw,Tj_igbt=Tj_igbt, Tj_diode=Tj_diode) # losses in 3 x HB

        P_avg_Da = np.mean(results['P_total_Da (W)']) # average losses in a diode  (over full fout cycle)
        P_avg_Sa = np.mean(results['P_total_Sa (W)']) # average losses in a switch "

        # even if display is enabled  we don't want to display thermal simulation plot every iteration
        if i==5:
            debug_flag=plot_tj_en # log during last iteration
        else:
            debug_flag=False

        # losses of hb power module : 2 diodes + 2 IGBTs (all diodes have same avg losses; same thing for IGBTs)
        T_case_module = Tx + Rth_heatsink * (P_avg_Sa + P_avg_Da) * 2 # estimation of heatsink temperature of 1 module (steady state)

        data = thermal_model.calculate_junction_temps(data=results, T_case_igbt=T_case_module, T_case_diode=T_case_module, debug_flag=debug_flag)
        # the avg temperature of the different diodes are equal
        # the avg temperatures of the different IGBTs are equal
        # the deltaT of different (identical devices) are not completely equal... => steady state not reached in one output period?
        # take the avg of deltaT? or max?
        # ===========================================================
        # investigation
        #  <to compare with calculation using avg losses >
        delta_Tj_igbt_mean =  np.mean([data['Delta_Tj_Sa (K)'][0],
                                       data['Delta_Tj_Sb (K)'][0],
                                       data['Delta_Tj_Sc (K)'][0],
                                       data['Delta_Tj_S\'a (K)'][0],
                                       data['Delta_Tj_S\'b (K)'][0],
                                       data['Delta_Tj_S\'c (K)'][0]])
        # delta_Tj_igbt_max  =  np.max([data['Delta_Tj_Sa (K)'][0],
        #                               data['Delta_Tj_Sb (K)'][0],
        #                               data['Delta_Tj_Sc (K)'][0],
        #                               data['Delta_Tj_S\'a (K)'][0],
        #                               data['Delta_Tj_S\'b (K)'][0],
        #                               data['Delta_Tj_S\'c (K)'][0]])
        delta_Tj_diode_mean =  np.mean([data['Delta_Tj_Da (K)'][0],
                                        data['Delta_Tj_Db (K)'][0],
                                        data['Delta_Tj_Dc (K)'][0],
                                        data['Delta_Tj_D\'a (K)'][0],
                                        data['Delta_Tj_D\'b (K)'][0],
                                        data['Delta_Tj_D\'c (K)'][0]])
        # delta_Tj_diode_max =  np.max([data['Delta_Tj_Da (K)'][0],
        #                               data['Delta_Tj_Db (K)'][0],
        #                               data['Delta_Tj_Dc (K)'][0],
        #                               data['Delta_Tj_D\'a (K)'][0],
        #                               data['Delta_Tj_D\'b (K)'][0],
        #                               data['Delta_Tj_D\'c (K)'][0]])
        #P_rms_Da = rms(results['P_total_D\'b (W)'])
        #P_rms_Sa = rms(results['P_total_Sa (W)'])
        # ============================================================

        # the avg losses are available in DataFrame as well
        # avg losses during a period of fout
        P_avg_Da = data['P_avg_Da (W)'][0] # avg losses of diode
        P_avg_Sa = data['P_avg_Sa (W)'][0] # avg losses of IGBT

        PL_on_T_HB = np.mean(results['P_cond_Sa (W)'])
        PL_on_D_HB = np.mean(results['P_cond_Da (W)'])
        PL_sw_T_HB = np.mean(results['P_sw_Sa (W)'])
        PL_sw_D_HB = np.mean(results['P_sw_Da (W)'])

        total_loss = 2 * 3 * nb_parallel_sw * (PL_on_T_HB + PL_on_D_HB + PL_sw_T_HB + PL_sw_D_HB)

        semicond_powers = {
            "PL_avg_Q": P_avg_Sa,
            "PL_avg_D": P_avg_Da,
            "PL_on_T_HB": PL_on_T_HB,
            "PL_on_D_HB": PL_on_D_HB,
            "PL_sw_T_HB": PL_sw_T_HB,
            "PL_sw_D_HB": PL_sw_D_HB,
            "total_loss": total_loss
        }

        # update of junction temperatures (next iteration will be more accurate)

        # calculation of temperature reached considering avg losses
        # Rth_heatsink : Rth of heatsink (top plate to ambient) in K/W <for one power module>

        # heatsink temperature estimation under power module
        #    Tambient (heatsink) + Rth_heatsink * module losses
        Th = Tx + Rth_heatsink * (P_avg_Da + P_avg_Sa)*2 # avg temperature that would be reached in steady state

        # may be preferable to use Zth model to determine junction temperatures?
        # or the avg value calculated by calculate_junction_temps
        Tj_diode = Th + P_avg_Da * device_params.Rth_jc_D * 1e-3 # diode avg junction temperature
        Tj_igbt  = Th + P_avg_Sa * device_params.Rth_jc_Q * 1e-3 # igbt avg junction temperature



    if log_losses:
        print("calc_Tj_values_PWM: IGBT losses: P_avg_Sa:", P_avg_Sa)  #
        print("calc_Tj_values_PWM: Diode losses: P_avg_Da:", P_avg_Da) #

    # debug
        print("calc_Tj_value_PWM: delta_Tj_diode_mean:",delta_Tj_diode_mean)
        print("calc_Tj_value_PWM: delta_Tj_igbt_mean:",delta_Tj_igbt_mean)
        print("calc_Tj_value_PWM: steady state avg temperature of diode:",Tj_diode)
        print("calc_Tj_value_PWM: steady state avg temperature of igbt:", Tj_igbt)

    # plot_P_total_semicond(data) # losses within the different devices
    # plot_deltaT_devices(data)

    # Tj_diode = data["Tj_avg_Da (C)"][0]
    # deltaT_D = data["Delta_Tj_Da (K)"][0]
    # Tj_Q     = data["Tj_avg_Sa (C)"][0]
    # deltaT_Q = data["Delta_Tj_Sa (K)"][0]


    # =========================================
    # test alternative to determine the deltaT:
    # =========================================

    # <same as in calc_Tj_values_IEC>
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
    # actual output frequency = freq*Rel_speed_i
    sim_time = 1.0

    # first process the diode

    # losses for the diode : avg losses concentrated in the conduction period

    # Note: losses are multiplied by 2 because the loss formula give the avg value for a full period
    # Here we consider that these losses are present during only during half period / the second half is 0
    # (to same avg losses over one period!)
    P_on = P_avg_Da * 2      # W
    #P_on = P_rms_Da * np.sqrt(2)

    P_off = 0.0      # W
    if log_losses:
        print("simulate thermal profile of diode")
    time, Tj_d, metrics =  simulate_thermal_profile(Rth_Diode, Cth_Diode, P_on, P_off, freq*Rel_speed_i, Th, sim_time, display_sim=False)

    Tj_diode = metrics["Tmean (degC)"]
    deltaT_D = metrics["DeltaT (K)"]

    # IGBT
    # losses for the IGBT
    # <factor 2 on losses : same explanation as for diodes>
    P_on = P_avg_Sa * 2      # W
    #P_on = P_rms_Sa * np.sqrt(2)

    P_off = 0.0      # W
    if log_losses:
        print("simulate thermal profile of IGBT")
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
        plt.title('(PWM sim) Thermal variation of semiconductor')
        plt.grid(True)
        plt.legend()
        plt.show()


    Tj_Q = metrics["Tmean (degC)"]
    deltaT_Q = metrics["DeltaT (K)"]

    #deltaD<delta_Tj_diode_mean 0.88 instead of 2.10 (max 2.25)
    #deltaT<delta_Tj_igbt_mean 1.08 instead of 2.75 (max 2.94)

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
def calc_powers_PWM(params, device_params: DeviceParameters, Rel_torque_i, Rel_speed_i, Tx,
                           plot_cond_currents_en=True,
                           log_losses=False):
        # input data
        """Calculate powers p w m."""
        Udc = params.get('Udc', 540)  # CDM DC link voltage <can be calculated as function as input voltage>

        if Rel_speed_i < 0.01:
            Rel_speed_i = 0.01  # can not be 0 (considered V/F control)
            print("Rel_speed_i adjusted to min value")

        # determination of operating point
        active_Pout = calc_active_power(Rel_torque_i,
                                        Rel_speed_i)  # shouln't be 0 if Rel_torque_i!=0 (even if Rel_speed_i=0) => torque hold consumes active power

        fsw = params.get('fsw', 2000)  # 4 000 for a CDM up to 90 kW / 2 000 for a CDM above 90 kW
        m = min(Rel_speed_i,
                1)  # >0 .. 1    modulation index, identical to the relative CDM output freq up to rated output freq

        PF = calc_PF(Rel_torque_i)  # output voltage power factor

        Vout_rms = 230 * m  # inverter phase to "neutral" output voltage (rms)
        Iout = calc_Iout(active_Pout, Vout_rms, PF, Udc)  # (current shared by power modules connected n //)
        nb_parallel_sw = params.get('nb_parallel_sw', 2)  # number of (half-bridge) power modules connected in //

        # creation of waveforms for the current operating point
        M = ModulationStrategy()

        # generates signals (in a DataFrame) considering current equally shared between nb_parallel_sw power modules)
        Iout_rms_module = (Iout / nb_parallel_sw)  # part of current handled by a SINGLE power module
        results = M.generate_waveforms(I_out_rms=Iout_rms_module, cos_phi=PF, f_out=50 * m, f_sw=fsw, NB_PERIODS=1)

        # for calculation of losses
        LM = LossModel(device_params)

        # first determines the conduction currents (in 3 x HB)
        results = LM.calculate_conduction_currents(results)

        if plot_cond_currents_en:
            # this plot does not work correctly
            plot_cond_currents(results)  # display (plot) the conduction currents flowing into the elements

        # calculate the losses

        # for this evaluation, temperature is supposed constant = Tx
        Tj_igbt = Tx
        Tj_diode = Tx

        results = LM.calculate_total_losses(data=results, f_sw=fsw, Tj_igbt=Tj_igbt,
                                            Tj_diode=Tj_diode)  # losses in 3 x HB

        P_avg_Da = np.mean(results['P_total_Da (W)'])  # average losses in a diode  (over full fout cycle)
        P_avg_Sa = np.mean(results['P_total_Sa (W)'])  # average losses in a switch "

        PL_on_T_HB = np.mean(results['P_cond_Sa (W)'])
        PL_on_D_HB = np.mean(results['P_cond_Da (W)'])
        PL_sw_T_HB = np.mean(results['P_sw_Sa (W)'])
        PL_sw_D_HB = np.mean(results['P_sw_Da (W)'])


        if log_losses:
            print("calc_Tj_values_PWM: IGBT losses: P_avg_Sa:", P_avg_Sa)  #
            print("calc_Tj_values_PWM: Diode losses: P_avg_Da:", P_avg_Da)  #

        semicond_powers = {
            "PL_avg_Q": P_avg_Sa,
            "PL_avg_D": P_avg_Da,
            "PL_on_T_HB": PL_on_T_HB,
            "PL_on_D_HB": PL_on_D_HB,
            "PL_sw_T_HB": PL_sw_T_HB,
            "PL_sw_D_HB": PL_sw_D_HB,
            #"total_loss": total_loss
        }
        return semicond_powers
