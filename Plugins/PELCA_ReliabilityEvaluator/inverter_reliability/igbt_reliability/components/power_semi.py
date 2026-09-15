"""\brief Provide shared reliability logic for power semiconductor devices.

This module is part of the PELCA reliability evaluator.
"""
from abc import ABC, abstractmethod
import numpy as np
import math
from inverter_reliability.igbt_reliability.components.DeviceParameters import DeviceParameters
from inverter_reliability.igbt_reliability.calculations.calc_Tj_values_IEC import calc_Tj_values_IEC
from inverter_reliability.igbt_reliability.calculations.calc_Tj_values_PWM import calc_Tj_values_PWM

# from .DeviceParameters import DeviceParameters
# from calculations.calc_Tj_values_IEC import calc_Tj_values_IEC
# from calculations.calc_Tj_values_PWM import calc_Tj_values_PWM

from inverter_reliability.igbt_reliability.calculations.check_Tj_estimations import check_Tj_estimations

class PowerSemi(ABC):
    """
    Contains constants related to FIDES model of semiconductor (generic part for both IGBT / diode)
    Contains also parameters of converter (GPI) for calculation of currents/ output power
    Methods:
        * calc_TJ_components: to calculate junction temperatures, deltaT for both IGBT and diode

        for a given mission profile, using FIDES method:
          * fit_rate_calc(profile_data, params) : "                                                   (one IGBT AND one diode)
          <~ same thing with another format to describe mission profile...>

        * FIDES_semicond_calc_accel_factors: helper function used in fit_calc_rate
        * check_Tj_estimations: use to compared estimations of temperatures using two methods (also used in fit_calc_rate)

    """

    def __init__(self, device_params: DeviceParameters, Nb_dies: int = 3, lambda0_TH: float = 0.56, process_grade=1):

        # Constants
        """Initialize the object with the provided configuration."""
        self.device_params = device_params
        self.Nb_dies = Nb_dies
        self.lambda0_TH = lambda0_TH * math.sqrt(Nb_dies)  # for a single device (diode or igbt)
        # Note: multiplied by sqrt(N) if N elements (diode / transistors are installed in single package)
        # here: consider 3 dies / diode or IGBT (if part of reference_module)
        self.process_grade = process_grade #1 for diode / #2 for igbt

        # ===================================================================
        # package-related constants

        # note: the choice of package impacts considerably the reliability calculated
        # For instance ISOWATT is a much better package <but how does it compare to reference_module package?...>

        # ISOWATT package (failures rates expressed in FIT)
        self.lambda0_RH = 0.0589
        self.lambda0_Tcy_case = 0.00303
        self.lambda0_Tcy_solder_joints = 0.01515
        self.lambda0_Mechanical = 0.0003

        # ISOTOP (STO227, TO244, Half-pack) SMD, high power, screw, plastic
        #self.lambda0_RH = 0.99
        #self.lambda0_Tcy_case = 0.0303
        #self.lambda0_Tcy_solder_joints = 0.16665
        #self.lambda0_Mechanical = 0.0033
        # ===================================================================

        # Pi factors
        self.Pi_Mechanical = 0     # neglected mechanical stress (?)
        # Pi_Mech = (Grms/0.5)**1.5

        self.Pi_RH = 0             # neglected: humidity stress (?)
        # Pi_RH = (RHambient/7)**4.4 * np.exp(11604 * 0.9 * ((1 / 293   ) - (1 / (T_ambient_board + 273))))

        self.Pi_placement    = 1.6 # Analogue power non-interface function
        self.Pi_process = 4        # process factor (default value) # variation from 1 (best) to 8 (worst)
        self.Pi_PM = 1.25          # component/part manufacturing   # variation from 0.5 to 2 (worst case)
        self.Pi_ruggedising = 1.7  # default value

        self.Csensibiliy = 5.5
        self.Tref = 60 # degC

        # same parameters for diodes & IGBTs?

        # normally calculated using a formula to process an W audit questionnaire (10 questions)
        #self.ProcessGrade=1 # for diode

        # normally specific to IGBT
        self.Pi_PW = np.exp(3.401*(1-self.process_grade)-0) # p138 FIDES 2022 (alpha=0, delta=3.401)

        # should be overwritten to 1 for a diode (because process_grade=1)

        from inverter_reliability.igbt_reliability.converter.converter import Converter
        self.converter_gpi = Converter(
            name="REFERENCE_CONVERTER",
            power_range=(245, 1209),
            # might be defined in Excel sheet
            torque_points_output       = {25: 0.39, 50: 0.56, 75: 0.77, 100: 1.0},
            torque_points_displacement = {25: 0.57, 50: 0.78, 75: 0.85, 100: 0.87}
        )



    # for both IGBT and diode
    # <the simulation of losses in inverter stage determines the losses for both diode & IGBT :
    # => no need to separate the processing of losses in those components>
    # <note: simulation done for one particular operating point>
    # Tx should be the ambient air temperature for inverter heatsink
    # ...
    def calc_TJ_components(self, params, Rel_torque, Rel_speed,  Tx): # life_ratio, load_factor
        """
        For a given operating point (considered steady state), Performs the thermal simulation
        (i.e. calculation of  Tj, deltaT) of both diode & IGBT using two methods (IEC & "PWM")
        <comparison is to check if IEC method could be a substitute to PWM level sim..>

        Parameters
        ----------
        params : TYPE
            parameters
        Rel_torque : float
            relative torque (0 .. 1)
        Rel_speed : float
            relative speed (0.01 .. 1)
        Tx : float
            "ambient temperature" (avg temperature of air flow under heatsink)

        Returns
        -------
        Tj_D_iec     : float
        deltaT_D_iec : float
        Tj_D_pwm     : float
        deltaT_D_pwm : float
        Tj_Q_iec     : float
        deltaT_Q_iec : float
        Tj_Q_pwm     : float
        deltaT_Q_pwm : float

        """
        # rel_speed & rel_torque for each segment of mission profile now passed as parameter
        # => enables to calculate output power / losses in semiconductors (electrothermal simulation for a single phase of a mission profile)

        # losses calculated at using IEC  method
        #Tj_D_iec, Tj_Q_iec, deltaT_D_iec, deltaT_Q_iec = calc_Tj_values_IEC(params, self.device_params, Rel_torque, Rel_speed,  Tx, log_losses=True) # life_ratio, load_factor
        semicond_temperatures_IEC, semicond_powers = calc_Tj_values_IEC(params, self.device_params, Rel_torque, Rel_speed,  Tx, log_losses=True)
        Tj_D_iec     = semicond_temperatures_IEC["Tj_diode"]
        Tj_Q_iec     = semicond_temperatures_IEC["Tj_Q"]
        deltaT_D_iec = semicond_temperatures_IEC["deltaT_D"]
        deltaT_Q_iec = semicond_temperatures_IEC["deltaT_Q"]

        # calculation also using simulation at "pwm" level for comparison
        #Tj_D_pwm, Tj_Q_pwm, deltaT_D_pwm, deltaT_Q_pwm = calc_Tj_values_PWM(params, self.device_params,  Rel_torque, Rel_speed,  Tx, log_losses=True) # life_ratio, load_factor
        semicond_temperatures_pwm, semicond_powers = calc_Tj_values_PWM(params, self.device_params,  Rel_torque, Rel_speed,  Tx, log_losses=True) # life_ratio, load_factor
        Tj_D_pwm     = semicond_temperatures_pwm["Tj_diode"]
        Tj_Q_pwm     = semicond_temperatures_pwm["Tj_Q"]
        deltaT_D_pwm = semicond_temperatures_pwm["deltaT_D"]
        deltaT_Q_pwm = semicond_temperatures_pwm["deltaT_Q"]

        # should return a structure
        return Tj_D_iec, deltaT_D_iec, Tj_D_pwm, deltaT_D_pwm, Tj_Q_iec, deltaT_Q_iec, Tj_Q_pwm, deltaT_Q_pwm


    def FIDES_semicond_calc_accel_factors(self, TJ_component, T_ambient, N_cy_i, T_phase, theta_cy_i, Pi_application_i, Operating_Phase_i, delta_T_cycling_i, T_max_cycling_i, G_RMS_i, RH_ambient_i,
                                          debug_log=False, component_type='diode'):
        """
        helper function to calculate different acceleration factors for a phase [segment] of mission profile

        Parameters (from current phase of mission profile)
        ----------
        TJ_component : float
            DESCRIPTION.
        T_ambient : float
            DESCRIPTION.
        N_cy_i : float
            DESCRIPTION.
        T_phase : float
            DESCRIPTION.
        theta_cy_i : float
            Duration of a cycle in hours.
        Pi_application_i : float
            FIDES parameter, related to application.
        Operating_Phase_i : boolean
            True if operating phase / False otherwise
        delta_T_cycling_i : float
            variation of ambient temperature during a cycle
        T_max_cycling_i : float
            max ambient temperature reached during cycle
        G_RMS_i : float
            acceleration value (related to vibrations)
        RH_ambient_i : float
            relative humidity (in %).

        Returns
        -------
        Pi_therm : float
            thermal accel factor.
        Pi_TcyCase : TYPE
            related to case.
        Pi_Tcy_solder_joints: TYPE
            related to solders.
        Pi_Mechanical : float
            (not returned at present).
        Pi_RH : float
            (not returned at present).

        """
        # note: input parameters might be part of segment structure
        # TJ_component, T_ambient, N_cy_i, T_phase, theta_cy_i, Pi_application_i, Operating_Phase_i, delta_T_cycling_i, T_max_cycling_i, G_RMS_i, RH_ambient_i

        # acceleration factors
        #   thermal <Arrhenius>
        if Operating_Phase_i:
            if component_type=='diode':
                Pi_therm = np.exp(11604 * 0.7 * ((1 / 293) - (1 / (TJ_component + 273))))  # diode
            else:
                Pi_therm = np.exp(11604 * 0.7 * ((1 / (60+273)) - (1 / (TJ_component + 273)))) # igbt
        else:
            # in non-operating phase  Pi_therm = 0 [according to param On/Off]
            # debug
            # print("non-operating phase: Pi_therm = 0")
            Pi_therm = 0

        # Refs: https://www.cff-fiabilite.fr/wp-content/uploads/sites/12/2020/12/Les-Rendez-vous-Faibilite-du-CFF-2020-12-FIDES-DGA-Presentation.pdf
        # FIDeS guide 2022!!!!!!

        #   case <Norris-Landsberg>
        # note: slightly different formula in https://www.cff-fiabilite.fr/wp-content/uploads/sites/12/2020/12/Les-Rendez-vous-Faibilite-du-CFF-2020-12-FIDES-DGA-Presentation.pdf
        # 12 x N_cy_annual / t_annual) * ...
        # Pi_Tcy <very small value...>
        # T_phase: duration of phase (in hours)
        Pi_TcyCase = (
            (12 * N_cy_i / T_phase) *
            ((delta_T_cycling_i / 20)**4) *
            np.exp(1414 * ((1 / 313) - (1 / (T_max_cycling_i + 273))))
        )

        #   solder joints  <Norris-Landsberg>
        Pi_Tcy_solder_joints = (
            (12 * N_cy_i / T_phase) *
            (np.minimum(theta_cy_i, 2) / 2)**(1/3) *
            ((delta_T_cycling_i / 20)**1.9) *
            np.exp(1414 * ((1 / 313) - (1 / (T_max_cycling_i + 273))))
        )
        if debug_log:
            print(f"FIDES_semicond_calc_accel_factors: TJ_component={TJ_component}")
            print("FIDES_semicond_calc_accel_factors: N_cy_i",N_cy_i,"T_phase",T_phase,"delta_T_cycling_i",delta_T_cycling_i,"T_max_cycling_i",T_max_cycling_i)
            print("FIDES_semicond_calc_accel_factors: Pi_therm", Pi_therm)
            print("FIDES_semicond_calc_accel_factors: Pi_TcyCase", Pi_TcyCase)
            print("FIDES_semicond_calc_accel_factors: Pi_Tcy_solder_joints", Pi_Tcy_solder_joints)

        # =============================================================================================================
        # not used

        # for each phase of the profile
        # (note: Pi_application_i comes from Excel sheet but is expected to be constant for the whole mission profile)
        Pi_induced_i = (self.Pi_placement * Pi_application_i * self.Pi_ruggedising) ** (0.511 * math.log(self.Csensibiliy))
        # from 1 to 100 (1=best case)

        # <might be neglected>
        # mechanical stress
        Pi_Mechanical = (G_RMS_i/0.5)**1.5

        # humidity stress
        Pi_RH = (RH_ambient_i/70)**44 * np.exp(11604 * 0.7 * ((1 / 293) - (1 / (T_ambient + 273)))) # T_i "T_ambient_board"
        # =============================================================================================================

        return Pi_therm, Pi_TcyCase, Pi_Tcy_solder_joints # , Pi_Mechanical, Pi_RH

    # ====================================================================================================

    # LF _ 05/12/2025 : change of encoding of mission profile (a DataFrame is passed as argument)
    # determines the FIT rate of one IGBT  OR one Diode of the inverter part for a given mission profile
    # (using FIDES method)

    # <or should it return on the fit or either diode or igbt?>
    # ideally yes, but thermal simulation is performed for both IGBT & diode...
    # ... while it might be done only once.


    # *******************************************************************************************************
    # not used in final code
    def fit_rate_calc(self, profile_data, params, debug_log=True, use_iec_temp=True):
        """
        determines the FIT rate of one IGBT  AND one Diode of the inverter part for a given mission profile
        (using FIDES method)

        Parameters
        ----------
        profile_data : TYPE
            one mission profile
        params : TYPE
            parameters

        Returns
        -------
        lambda_D : float
            failure rate of one diode (in FIT).
        lambda_T : float
            failure rate of one IGBT (in FIT).
        deltaT_D_count_list
            list of deltaT_D (one value per segment of mission profile)
        deltaT_Q_count_list
            list of deltaT_Q ( " )
        """
        # ============================================
        # reliability calculation using FIDES formulas
        # ============================================

        # diode
        lambda_D_physical = 0
        weighted_D_stress_sum_profile = 0
        deltaT_D_count_list = []

        # igbt
        lambda_T_physical = 0 # igbt
        weighted_T_stress_sum_profile = 0
        deltaT_Q_count_list = []

        # for each segment of mission profile:
        for idx in range(len(profile_data)):

            if debug_log:
                # debug msg
                print(f"\nfit_rate_calc: processing segment {idx} of mission profile")

            # *** get parameters for current segment of mission profile ***
            # suppressed: can be calculated
            #life_ratio_i      = profile_data['life_ratio'].to_numpy()[idx] # related to Hours_per_Year_i
            #                                                               # Hours_per_Year_i = life_ratio_i * 8760 (t_total)
            life_ratio_i = profile_data['Operating_Hours_per_Year'].to_numpy()[idx] / 8760

            Operating_Phase_i =  profile_data['Operating_Phase'].to_numpy()[idx]

            if not Operating_Phase_i:
                if debug_log:
                    print("fit_rate_calc: this segment is not an operating phase")
                # no active deltaT of dies during operation : no thermal simulation to do
                # only the slow passive deltaT specified in mission profile are considered (delta_T_cycling, T_max_cycling, N_cy)
                # impact on lifetime?
                # deltaT = deltaT_cycling
                # temp_min = T_max_cycling - delta_T_cycling
                # and normally, Tx = (temp_min + T_max_cycling)/2 = T_max_cycling - delta_T_cycling/2


            #WT_phase           = life_ratio_i*8760 # what if sum of active phases is different from 8760 (5000h for instance) ?
            #T_phase (duration of a phase in hours) is directly available from mission profile: parameter Operating_Hours_per_Year

            Rel_speed_i       =  profile_data['Rel_speed'].to_numpy()[idx]
            # Rel_speed_i must not be too low
            if Rel_speed_i<0.01:
                if debug_log:
                    print(f"fit_rate_calc: Rel_speed_i ({Rel_speed_i}) too small! Limited to 1%")
                Rel_speed_i=0.01 # limited to 1%

            Rel_torque_i      =  profile_data['Rel_torque'].to_numpy()[idx]

            T_i = profile_data['Tx'].to_numpy()[idx] # ambient temperature for power modules (considered heatsink air temperature here)
            # heatsink temperature will be calculated using this parameter

            delta_T_cycling_i = profile_data['delta_T_cycling'].to_numpy()[idx]  # variation of ambient temperature    during a cycle within current phase (here called segment of mission profile)
            T_max_cycling_i   = profile_data['T_max_cycling'].to_numpy()[idx]    # maximum ambient temperature reached during a cycle ...

            Hours_per_Year_i  = profile_data['Operating_Hours_per_Year'].to_numpy()[idx]      #  t_annual ? time associated with each operating phase over a year (hours)
            T_phase = Hours_per_Year_i

            N_cy_i            = profile_data['N_cy'].to_numpy()[idx]            # N_annual_cy : number of cycles assocated with each cycling phase over a year (cycles)
            theta_cy_i        = profile_data['theta_cy'].to_numpy()[idx]        # cycle duration (hours)
                                                                                # now called t_phase in FIDES 2022 (?)

            Pi_application_i  = profile_data['Pi_application'].to_numpy()[idx]  #
            #Pi_type?

            RH_ambient_i      = profile_data['RH_ambient'].to_numpy()[idx]      # ... always the same value = 0.3 (30%)
            G_RMS_i           = profile_data['G_RMS'].to_numpy()[idx]           # stress associated with each random vibration phase .. always the same value = 0.3 G

            # determine the avg junction temperature (t_m) & deltaT ("HF") during the segment of mission profile
            # at present, calculate losses using formula of IEC_TC_22_calc_losses

            # note: T_i is supposed to be "ambient temperature" => at present considered air flow temperature for heatsink
            # for calculation of junction temperature, we need to estimate the elevation of temperature of heatsink
            # (with respect to ambient temperature) and then junction temperature with respect to its case temperature.
            # => this is determined by evaluating a thermal model fed by losses of semiconductor

            if Operating_Phase_i:
                # ================================================================
                # 1 - determination of inverter output active power
                #active_Pout =  self.calc_active_power(Rel_torque_i, Rel_speed_i) # 0 if Rel_speed_i=0 (but still causes losses normally...)

                # from output power we can determine the losses within the semi-conductors & the increase of junctions temperatures

                # estimation of variations of temperature during operation (ripple at Fout frequency)
                # "electro-thermal" simulation => losses depends on Tj / which depends on losses... => equilibrium must be found

                # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                #PN = 200000  # PN = params.get('PN', 200000)
                # load_factor = active_Pout / PN  # to keep previous function interface for now (load_factor can be >1 now)

                if debug_log:
                    print("fit_rate_calc: calculation of the Tj of the components")
                # (calculated by two methods: pwm & IEC)
                Tj_D_iec, deltaT_D_iec, Tj_D_pwm, deltaT_D_pwm, Tj_Q_iec, deltaT_Q_iec, Tj_Q_pwm, deltaT_Q_pwm = self.calc_TJ_components(params, Rel_torque_i, Rel_speed_i, T_i) # life_ratio_i, load_factor

                # Tj_D_iec, Tj_Q_iec, or Tj_D_pwm,  Tj_Q_pwm, are the avg temperatures needed for the reliability calculation
                # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

                # calculation of relative errors between IEC loss calculation & "pwm" level simulation
                # <to check if IEC calculation is good enough for that task>
                check_Tj_estimations(Tj_D_iec, Tj_D_pwm, Tj_Q_iec, Tj_Q_pwm, deltaT_D_iec, deltaT_D_pwm, deltaT_Q_iec, deltaT_Q_pwm )

                # choice of Tj value
                if use_iec_temp:
                    Tj_D = Tj_D_iec
                    Tj_Q = Tj_Q_iec
                    deltaT_D = deltaT_D_iec
                    deltaT_Q = deltaT_Q_iec
                else:
                    Tj_D = Tj_D_pwm
                    Tj_Q = Tj_Q_pwm
                    deltaT_D = deltaT_D_pwm
                    deltaT_Q = deltaT_Q_pwm

                # estimation of number of HF thermal cycles <not needed actually for FIDES model, only for lifetime model>
                # as a simplification, can convert the whole segment in a number of cycles, at a given delta T

                # duration of a thermal cycle at output frequency
                theta_HF_cy = 1/(Rel_speed_i * 50) / 3600    # in hours considering nominal output frequency = 50 Hz

                N_HF_cy     = (N_cy_i*theta_cy_i)/theta_HF_cy  # number of HF cycles for the current segment phase (per year)

                # <for lifetime calculation>
                # append to list of deltaT count : (Ni, deltaTj_i, T_m_i) "short" cycles due to fout of inverter

                if use_iec_temp:
                    deltaT_D_count_list.append((round(N_HF_cy,0), round(deltaT_D_iec,1), round(Tj_D_iec,1) )) # same number of thermal cycles for IGBT and diode
                    deltaT_Q_count_list.append((round(N_HF_cy,0), round(deltaT_Q_iec,1), round(Tj_Q_iec,1) ))
                else:
                    deltaT_D_count_list.append((round(N_HF_cy,0), round(deltaT_D_pwm,1), round(Tj_D_pwm,1) )) # same number of thermal cycles for IGBT and diode
                    deltaT_Q_count_list.append((round(N_HF_cy,0), round(deltaT_Q_pwm,1), round(Tj_Q_pwm,1) ))

                # ?????????????????????????????????????????????????????????????????????????????????????????????????
                # to add contribution of lower freq deltaT (passive cycling imposed by mission profile)
                # !!! need normally to consider the variations at COMPONENT LEVEL caused by "system" level changes !!!
                #deltaT_D_count_list.append((round(N_cy_i,0), round(delta_T_cycling_i,1), round(Tj_D,1) ))
                #deltaT_Q_count_list.append((round(N_cy_i,0), round(delta_T_cycling_i,1), round(Tj_D,1) ))
                # ?????????????????????????????????????????????????????????????????????????????????????????????????

            # ================================================================
            # else:
            if not Operating_Phase_i:
                Tj_D_iec = Tj_D_pwm = T_i # passive cycling only
                deltaT_D_iec = deltaT_D_pwm = 0 # or delta_T_cycling_i ? should be considered maybe for lifetime model...
                Tj_Q_iec = Tj_Q_pwm = T_i
                deltaT_Q_iec = deltaT_Q_pwm = 0 # or delta_T_cycling_i ?

                # choice of Tj value
                if use_iec_temp:
                    Tj_D = Tj_D_iec
                    Tj_Q = Tj_Q_iec
                    deltaT_D = deltaT_D_iec
                    deltaT_Q = deltaT_Q_iec
                else:
                    Tj_D = Tj_D_pwm
                    Tj_Q = Tj_Q_pwm
                    deltaT_D = deltaT_D_pwm
                    deltaT_Q = deltaT_Q_pwm

                # Ni, deltaT, Tj : no "hf" cycles
                if use_iec_temp:
                    deltaT_D_count_list.append((round(N_HF_cy,0), round(deltaT_D_iec,1), round(Tj_D_iec,1) )) # same number of thermal cycles for IGBT and diode
                    deltaT_Q_count_list.append((round(N_HF_cy,0), round(deltaT_Q_iec,1), round(Tj_Q_iec,1) ))
                else:
                    deltaT_D_count_list.append((round(N_HF_cy,0), round(deltaT_D_pwm,1), round(Tj_D_pwm,1) )) # same number of thermal cycles for IGBT and diode
                    deltaT_Q_count_list.append((round(N_HF_cy,0), round(deltaT_Q_pwm,1), round(Tj_Q_pwm,1) ))

                # to add (small!) contribution of limited number of large deltaT due to mission profile (day / night variation)
                # ambient deltaT, Tx <=> same as experienced by components
                deltaT_D_count_list.append((round(N_cy_i,0), round(delta_T_cycling_i,1), round(T_i,1) )) # Tj_D supposed to be T_i (no power)
                deltaT_Q_count_list.append((round(N_cy_i,0), round(delta_T_cycling_i,1), round(T_i,1) )) # Tj_Q supposed to be T_i (no power)

            # ================================================================

            # theoretical partial lifetime might be calculated here
            # Nf = number of cycles to failure at that avg temperature, delta_T_cyclage_i
            # (actual number of cycles)
            # partial lifetime consumed: actual number of cycles / Nf


            # for each phase of the profile

            # (note: Pi_application_i comes from Excel sheet but is expected to be constant for the whole mission profile)
            Pi_induced_i = (self.Pi_placement * Pi_application_i * self.Pi_ruggedising) ** (0.511 * math.log(self.Csensibiliy))
            # from 1 to 100 (1=best case)

            # diode & igbt differ by the lambda0_TH
            # they differ also by the process grade (1 for diode / 2 for IGBT)
            # both components have the same number of dies (3)


            # *** diode ***

            # calculation of stress factors (evaluated in each phase of mission profile)
            if not Operating_Phase_i:
                Pi_therm = 0
            else:
                Pi_therm = np.exp(11604 * 0.7 * ((1 / 293) - (1 / (Tj_D + 273))))  # Arrhenius

            # =========================================================
            # same factors for both diode and igbt
            Pi_TcyCase = (
                (12 * N_cy_i / T_phase) *
                ((delta_T_cycling_i / 20)**4) *
                np.exp(1414 * ((1 / 313) - (1 / (T_max_cycling_i + 273))))
            )

            #lambda0_Tcy_solder_joints : constant

            #Pi_RH         : could possibly be neglected
            if Operating_Phase_i:
                self.Pi_RH = 0
            else:
                self.Pi_RH = (RH_ambient_i/7)**4.4 * np.exp(11604 * 0.9 * ((1 / 293   ) - (1 / (T_i + 273))))

            #Pi_Mechanical : could be neglected
            self.Pi_Mech = (G_RMS_i/0.5)**1.5
            # ==========================================================

            Pi_therm, Pi_TcyCase, Pi_Tcy_solder_joints = self.FIDES_semicond_calc_accel_factors(Tj_D, T_i, N_cy_i, T_phase, theta_cy_i, Pi_application_i, Operating_Phase_i, delta_T_cycling_i, T_max_cycling_i, G_RMS_i, RH_ambient_i)
            weighted_D_stress_sum_profile = ( ((0.1574 * Pi_therm) # self.lambda0_TH
                                           + (self.lambda0_Tcy_case * Pi_TcyCase)
                                           + (self.lambda0_Tcy_solder_joints * Pi_Tcy_solder_joints)
                                           + (self.lambda0_RH * self.Pi_RH)
                                           + (self.lambda0_Mechanical * self.Pi_Mechanical))*life_ratio_i
                                           + weighted_D_stress_sum_profile)

            # *** igbt ***

            # thermal stress factor for IGBT
            if not Operating_Phase_i:
                Pi_therm = 0
            else:
                Pi_therm = np.exp(11604 * 0.7 * ((1 / 293) - (1 / (Tj_Q + 273))))  # Arrhenius

            # other factors are identical (as diode)

            Pi_therm, Pi_TcyCase, Pi_Tcy_solder_joints = self.FIDES_semicond_calc_accel_factors(Tj_Q, T_i, N_cy_i, T_phase, theta_cy_i, Pi_application_i, Operating_Phase_i, delta_T_cycling_i, T_max_cycling_i, G_RMS_i, RH_ambient_i)
            weighted_T_stress_sum_profile = ( ((0.56 * Pi_therm) # self.lambda0_TH
                                           + (self.lambda0_Tcy_case * Pi_TcyCase)
                                           + (self.lambda0_Tcy_solder_joints * Pi_Tcy_solder_joints)
                                           + (self.lambda0_RH * self.Pi_RH)
                                           + (self.lambda0_Mechanical * self.Pi_Mechanical))*life_ratio_i
                                           + weighted_T_stress_sum_profile)


        # debug
        # deltaT_D_count_list, delta_T_count_list
        # or self.delta_T_count_list ? <to avoid passing this information with arguments of this function ...>
        # create a method get_delta_T_count_list...
        #print("delta_T_count_list: ", delta_T_count_list)


        # <Pi_induced_i constant for all mission profile>
        lambda_D_physical =  weighted_D_stress_sum_profile * Pi_induced_i
        lambda_T_physical =  weighted_T_stress_sum_profile * Pi_induced_i

        # final calculation
        lambda_D = lambda_D_physical * self.Pi_PM * self.Pi_process
        lambda_T = lambda_T_physical * self.Pi_PM * self.Pi_process * self.Pi_PW  # (specific to IGBT)


        return lambda_D, lambda_T, deltaT_D_count_list, deltaT_Q_count_list



    # # not used anymore
    # # <should be put in a class module that integrate both diode and igbt...>
    # def calc_lambda_semiconductors(self, profile_data, params, debug_log=True):
    #
    #     """
    #     determines the FIT rate of one IGBT  AND one Diode of the inverter part for a given mission profile
    #     (using FIDES method)
    #
    #     Parameters
    #     ----------
    #     profile_data : TYPE
    #         one mission profile
    #     params : TYPE
    #         parameters
    #
    #     Returns
    #     -------
    #     lambda_D : float
    #         failure rate of one diode (in FIT).
    #     lambda_T : float
    #         failure rate of one IGBT (in FIT).
    #     deltaT_D_count_list
    #         list of deltaT_D (one value per segment of mission profile)
    #     deltaT_Q_count_list
    #         list of deltaT_Q ( " )
    #     """
    #     # ============================================
    #     # reliability calculation using FIDES formulas
    #     # ============================================
    #
    #     # diode
    #     lambda_D_physical = 0
    #     weighted_D_stress_sum_profile = 0
    #
    #     # igbt
    #     lambda_T_physical = 0 # igbt
    #     weighted_T_stress_sum_profile = 0
    #
    #     # for each segment of mission profile:
    #     for idx in range(len(profile_data)):
    #
    #         if debug_log:
    #             # debug msg
    #             print(f"\ncalc_lambda_semiconductors: processing segment {idx} of mission profile")
    #
    #         # *** get parameters for current segment of mission profile ***
    #         life_ratio_i      = profile_data['life_ratio'].to_numpy()[idx] # related to Hours_per_Year_i
    #                                                                        # Hours_per_Year_i = life_ratio_i * 8760 (t_total)
    #
    #         Operating_Phase_i =  profile_data['Operating_Phase'].to_numpy()[idx]
    #
    #         if not Operating_Phase_i:
    #             if debug_log:
    #                 print("calc_lambda_semiconductors: this segment is not an operating phase")
    #             # no active deltaT of dies during operation : no thermal simulation to do
    #             # only the slow passive deltaT specified in mission profile are considered (delta_T_cycling, T_max_cycling, N_cy)
    #             # impact on lifetime?
    #             # deltaT = deltaT_cycling
    #             # temp_min = T_max_cycling - delta_T_cycling
    #             # and normally, Tx = (temp_min + T_max_cycling)/2 = T_max_cycling - delta_T_cycling/2
    #
    #
    #         #WT_phase           = life_ratio_i*8760 # what if sum of active phases is different from 8760 (5000h for instance) ?
    #         #T_phase (duration of a phase in hours) is directly available from mission profile: parameter Operating_Hours_per_Year
    #
    #         Rel_speed_i       =  profile_data['Rel_speed'].to_numpy()[idx]
    #         # Rel_speed_i must not be too low
    #         if Rel_speed_i<0.01:
    #             if debug_log:
    #                 print(f"fit_rate_calc: Rel_speed_i ({Rel_speed_i}) too small! Limited to 1%")
    #             Rel_speed_i=0.01 # limited to 1%
    #
    #
    #         # Rel_torque_i      =  profile_data['Rel_torque'].to_numpy()[idx]
    #
    #         T_i = profile_data['Tx'].to_numpy()[idx] # ambient temperature for power modules (considered heatsink air temperature here)
    #         # heatsink temperature will be calculated using this parameter
    #
    #         delta_T_cycling_i = profile_data['delta_T_cycling'].to_numpy()[idx]  # variation of ambient temperature    during a cycle within current phase (here called segment of mission profile)
    #         T_max_cycling_i   = profile_data['T_max_cycling'].to_numpy()[idx]    # maximum ambient temperature reached during a cycle ...
    #
    #         Hours_per_Year_i  = profile_data['Operating_Hours_per_Year'].to_numpy()[idx]      #  t_annual ? time associated with each operating phase over a year (hours)
    #         T_phase = Hours_per_Year_i
    #
    #         N_cy_i            = profile_data['N_cy'].to_numpy()[idx]            # N_annual_cy : number of cycles associated with each cycling phase over a year (cycles)
    #         theta_cy_i        = profile_data['theta_cy'].to_numpy()[idx]        # cycle duration (hours)
    #                                                                             # now called t_phase in FIDES 2022 (?)
    #
    #         Pi_application_i  = profile_data['Pi_application'].to_numpy()[idx]  #
    #         #Pi_type?
    #
    #         RH_ambient_i      = profile_data['RH_ambient'].to_numpy()[idx]      # ... always the same value = 0.3 (30%)
    #         G_RMS_i           = profile_data['G_RMS'].to_numpy()[idx]           # stress associated with each random vibration phase .. always the same value = 0.3 G
    #
    #
    #         # determine the avg junction temperature (t_m) & deltaT ("HF") during the segment of mission profile
    #         # at present, calculate losses using formula of IEC_TC_22_calc_losses
    #
    #         # note: T_i is supposed to be "ambient temperature" => at present considered air flow temperature for heatsink
    #         # for calculation of junction temperature, we need to estimate the elevation of temperature of heatsink
    #         # (with respect to ambient temperature) and then junction temperature with respect to its case temperature.
    #         # => this is determined by evaluating a thermal model fed by losses of semiconductor
    #
    #
    #
    #         # theoretical partial lifetime might be calculated here
    #         # Nf = number of cycles to failure at that avg temperature, delta_T_cyclage_i
    #         # actual number of cycles
    #         # partial lifetime consumed: actual number of cycles / Nf
    #
    #
    #         # for each phase of the profile
    #
    #         # (note: Pi_application_i comes from Excel sheet but is expected to be constant for the whole mission profile)
    #         Pi_induced_i = (self.Pi_placement * Pi_application_i * self.Pi_ruggedising) ** (0.511 * math.log(self.Csensibiliy))
    #         # from 1 to 100 (1=best case)
    #
    #         # diode & igbt differ by the lambda0_TH
    #         # they differ also by the process grade (1 for diode / 2 for IGBT)
    #         # both components have the same number of dies (3)
    #
    #
    #         # get temperatures estimated for this segment
    #         Tj_D = profile_data['Tj_D'].to_numpy()[idx]  # avg temperature of diode determined in that phase
    #         Tj_Q = profile_data['Tj_Q'].to_numpy()[idx]  # avg temperature of igbt determined in that phase
    #
    #
    #         # *** diode ***
    #
    #         # calculation of stress factors (evaluated in each phase of mission profile)
    #         if not Operating_Phase_i:
    #             Pi_therm = 0
    #         else:
    #             Pi_therm = np.exp(11604 * 0.7 * ((1 / 293) - (1 / (Tj_D + 273))))  # Arrhenius
    #
    #         # =========================================================
    #         # same factors for both diode and igbt
    #         Pi_TcyCase = (
    #             (12 * N_cy_i / T_phase) *
    #             ((delta_T_cycling_i / 20)**4) *
    #             np.exp(1414 * ((1 / 313) - (1 / (T_max_cycling_i + 273))))
    #         )
    #
    #         #lambda0_Tcy_solder_joints : constant
    #
    #         #Pi_RH         : could possibly be neglected
    #         if Operating_Phase_i:
    #             self.Pi_RH = 0
    #         else:
    #             self.Pi_RH = (RH_ambient_i/7)**4.4 * np.exp(11604 * 0.9 * ((1 / 293   ) - (1 / (T_i + 273))))
    #
    #         #Pi_Mechanical : could be neglected
    #         self.Pi_Mech = (G_RMS_i/0.5)**1.5
    #         # ==========================================================
    #
    #         Pi_therm, Pi_TcyCase, Pi_Tcy_solder_joints = self.FIDES_semicond_calc_accel_factors(Tj_D, T_i, N_cy_i, T_phase, theta_cy_i, Pi_application_i, Operating_Phase_i, delta_T_cycling_i, T_max_cycling_i, G_RMS_i, RH_ambient_i)
    #         weighted_D_stress_sum_profile = ( (((0.1574 * Pi_therm) # self.lambda0_TH
    #                                              + (self.lambda0_Tcy_case * Pi_TcyCase)
    #                                              + (self.lambda0_Tcy_solder_joints * Pi_Tcy_solder_joints)
    #                                              + (self.lambda0_RH * self.Pi_RH)
    #                                              + (self.lambda0_Mechanical * self.Pi_Mechanical))
    #                                            * life_ratio_i*Pi_induced_i)
    #                                          + weighted_D_stress_sum_profile)
    #
    #         # *** igbt ***
    #
    #         # thermal stress factor for IGBT
    #         if not Operating_Phase_i:
    #             Pi_therm = 0
    #         else:
    #             Pi_therm = np.exp(11604 * 0.7 * ((1 / 293) - (1 / (Tj_Q + 273))))  # Arrhenius
    #
    #         # other factors are identical (as diode)
    #
    #         Pi_therm, Pi_TcyCase, Pi_Tcy_solder_joints = self.FIDES_semicond_calc_accel_factors(Tj_Q, T_i, N_cy_i, T_phase, theta_cy_i, Pi_application_i, Operating_Phase_i, delta_T_cycling_i, T_max_cycling_i, G_RMS_i, RH_ambient_i)
    #         weighted_T_stress_sum_profile = ( (((0.56 * Pi_therm) # self.lambda0_TH
    #                                             + (self.lambda0_Tcy_case * Pi_TcyCase)
    #                                             + (self.lambda0_Tcy_solder_joints * Pi_Tcy_solder_joints)
    #                                             + (self.lambda0_RH * self.Pi_RH)
    #                                             + (self.lambda0_Mechanical * self.Pi_Mechanical))
    #                                            * life_ratio_i * Pi_induced_i)
    #                                          + weighted_T_stress_sum_profile)
    #
    #
    #     # debug
    #     # deltaT_D_count_list, delta_T_count_list
    #     # or self.delta_T_count_list ? <to avoid passing this information with arguments of this function ...>
    #     # create a method get_delta_T_count_list...
    #     #print("delta_T_count_list: ", delta_T_count_list)
    #
    #
    #     # <Pi_induced_i constant for all mission profile>
    #     lambda_D_physical =  weighted_D_stress_sum_profile
    #     lambda_T_physical =  weighted_T_stress_sum_profile
    #
    #     # final calculation
    #     lambda_D = lambda_D_physical * self.Pi_PM * self.Pi_process
    #     lambda_T = lambda_T_physical * self.Pi_PM * self.Pi_process * self.Pi_PW  # (specific to IGBT)
    #
    #
    #     return lambda_D, lambda_T


    #  *******************************************************************************************************
    # for one component (IGBT or diode)
    #  *******************************************************************************************************
    # Now considers the stress parameters related to case temperature (not ambient of heatsink...)
    def calc_lambda_common(self, profile_data, params, lambda0_TH, process_grade, component_type='diode', debug_log=True, use_iec_temp=True ):

        """
        determines the FIT rate of one IGBT  or one Diode of the inverter part for a given mission profile
        (using FIDES method)

        Parameters
        ----------
            :param profile_data: one mission profile
            :param params: parameters
            :param lambda0_TH: float    specific value for diode or IGBT
            :param component_type: str  'diode' / 'igbt'
            :param process_grade: integer   (1 or 2) diode / IGBT
            :param debug_log: boolean => disable/enable debug log
            :param use_iec_temp: boolean : losses calculation method used => True: IEC / False: PWM

        Returns
        -------
        lambda_component : float
            failure rate of one diode or one IGBT (in FIT).


        """
        # ============================================
        # reliability calculation using FIDES formulas
        # ============================================

        # Note: for considered component
            # diode & igbt differ by the lambda0_TH
            # they differ also by the process grade (1 for diode / 2 for IGBT)
            # both components have the same number of dies (3)

        lambda_physical = 0
        weighted_stress_sum_profile = 0


        # for each phase (segment) of mission profile:
        for idx in range(len(profile_data)):

            if debug_log:
                # debug msg
                print(f"calc_lambda: processing segment {idx} of mission profile")

            # *** get parameters for current segment of mission profile ***
            # suppressed: can be calculated
            #life_ratio_i      = profile_data['life_ratio'].to_numpy()[idx] # related to Hours_per_Year_i
            #                                                               # Hours_per_Year_i = life_ratio_i * 8760 (t_total)
            life_ratio_i = profile_data['Operating_Hours_per_Year'].to_numpy()[idx] / 8760

            Operating_Phase_i =  profile_data['Operating_Phase'].to_numpy()[idx]

            if not Operating_Phase_i:
                if debug_log:
                    print("calc_lambda: this segment is not an operating phase")
                # no active deltaT of dies during operation : no thermal simulation to do
                # only the slow passive deltaT specified in mission profile are considered (delta_T_cycling, T_max_cycling, N_cy)
                # impact on lifetime?
                # deltaT = deltaT_cycling
                # temp_min = T_max_cycling - delta_T_cycling
                # and normally, Tx = (temp_min + T_max_cycling)/2 = T_max_cycling - delta_T_cycling/2

            Rel_speed_i       =  profile_data['Rel_speed'].to_numpy()[idx]
            # Rel_speed_i must not be too low
            if Rel_speed_i<0.01:
                if debug_log:
                    print(f"calc_lambda: Rel_speed_i ({Rel_speed_i}) too small! Limited to 1%")
                Rel_speed_i=0.01 # limited to 1%

            # Rel_torque_i      =  profile_data['Rel_torque'].to_numpy()[idx]

            T_i = profile_data['Tx'].to_numpy()[idx] # ambient temperature for power modules (considered heatsink air temperature here)
            # heatsink temperature will be calculated using this parameter

            delta_T_cycling_i = profile_data['delta_T_cycling'].to_numpy()[idx]  # variation of ambient temperature    during a cycle within current phase (here called segment of mission profile)
            T_max_cycling_i   = profile_data['T_max_cycling'].to_numpy()[idx]    # maximum ambient temperature reached during a cycle ...

            Hours_per_Year_i  = profile_data['Operating_Hours_per_Year'].to_numpy()[idx]      #  t_annual ? time associated with each operating phase over a year (hours)
            T_phase = Hours_per_Year_i

            N_cy_i            = profile_data['N_cy'].to_numpy()[idx]            # N_annual_cy : number of cycles assocated with each cycling phase over a year (cycles)
            theta_cy_i        = profile_data['theta_cy'].to_numpy()[idx]        # cycle duration (hours)
                                                                                # now called t_phase in FIDES 2022 (?)

            Pi_application_i  = profile_data['Pi_application'].to_numpy()[idx]  #

            RH_ambient_i      = profile_data['RH_ambient'].to_numpy()[idx]      #
            G_RMS_i           = profile_data['G_RMS'].to_numpy()[idx]           # stress associated with each random vibration phase .. always the same value = 0.3 G


            # (note: Pi_application_i comes from Excel sheet but is expected to be constant for the whole mission profile)
            Pi_induced_i = (self.Pi_placement * Pi_application_i * self.Pi_ruggedising) ** (0.511 * math.log(self.Csensibiliy))
            # from 1 to 100 (1=best case)

            # temperatures have been evaluated by previous electro-thermal simulation

            # note: T_i is supposed to be "ambient temperature" of component =>
            # in mission profile it is the air flow temperature for heatsink...

            # update with case temperature parameters to evaluate reliability
            T_i               = profile_data['Tc'].to_numpy()[idx]
            delta_T_cycling_i = profile_data['delta_Tc_cycling'].to_numpy()[idx]
            T_max_cycling_i   = profile_data['Tc_max_cycling'].to_numpy()[idx]

            # get temperatures estimated for this segment
            # at present temperatures are those estimated using IEC losses formulas
            if component_type=='diode':
                # <might be deduced by other means>
                if use_iec_temp:
                    Tj = profile_data['Tj_D_iec'].to_numpy()[idx]  # avg temperature of diode determined in that phase Tj_D_iec
                else:
                    #temperatures estimated using "pwm" simulation
                    Tj = profile_data['Tj_D_pwm'].to_numpy()[idx]  # avg temperature of diode determined in that phase Tj_D_pwm
            else:
                # 'igbt'
                if use_iec_temp:
                    Tj = profile_data['Tj_Q_iec'].to_numpy()[idx]  # avg temperature of igbt determined in that phase Tj_Q_iec
                else:
                    #temperatures estimated using "pwm" simulation
                    Tj = profile_data['Tj_Q_pwm'].to_numpy()[idx]  # avg temperature of igbt determined in that phase Tj_Q_pwm

            # *** considered component ***

            # # calculation of stress factors (evaluated in each phase of mission profile)
            # if not Operating_Phase_i:
            #     Pi_therm = 0
            # else:
            #     Pi_therm = np.exp(11604 * 0.7 * ((1 / 293) - (1 / (Tj + 273))))  # Arrhenius
            # # Pi_therm not used ...
            #
            # # =========================================================
            # # same factors are the same for both diode and igbt
            # Pi_TcyCase = (
            #     (12 * N_cy_i / T_phase) *
            #     ((delta_T_cycling_i / 20)**4) *
            #     np.exp(1414 * ((1 / 313) - (1 / (T_max_cycling_i + 273))))
            # )

            #lambda0_Tcy_solder_joints : constant

            #Pi_RH         : could possibly be neglected
            if Operating_Phase_i:
                self.Pi_RH = 0
            else:
                self.Pi_RH = (RH_ambient_i/7)**4.4 * np.exp(11604 * 0.9 * ((1 / 293   ) - (1 / (T_i + 273))))

            #Pi_Mechanical : could probably be neglected
            self.Pi_Mechanical = (G_RMS_i/0.5)**1.5
            # ==========================================================

            # add param component_type
            Pi_therm, Pi_TcyCase, Pi_Tcy_solder_joints = self.FIDES_semicond_calc_accel_factors(Tj, T_i, N_cy_i, T_phase, theta_cy_i, Pi_application_i, Operating_Phase_i, delta_T_cycling_i, T_max_cycling_i, G_RMS_i, RH_ambient_i, component_type=component_type)

            weighted_stress_sum_profile = ( (((lambda0_TH * Pi_therm) # self.lambda0_TH
                                                 + (self.lambda0_Tcy_case * Pi_TcyCase)
                                                 + (self.lambda0_Tcy_solder_joints * Pi_Tcy_solder_joints)
                                                 + (self.lambda0_RH * self.Pi_RH)
                                                 + (self.lambda0_Mechanical * self.Pi_Mechanical))
                                               * life_ratio_i*Pi_induced_i)
                                             + weighted_stress_sum_profile)


        # <Pi_induced_i constant for all mission profile>
        lambda_physical =  weighted_stress_sum_profile


        # final calculation
        lambda_component = lambda_physical * self.Pi_PM * self.Pi_process * self.Pi_PW
        # note:  Pi_PW is specific to IGBT (=1 for diode)



        return lambda_component
