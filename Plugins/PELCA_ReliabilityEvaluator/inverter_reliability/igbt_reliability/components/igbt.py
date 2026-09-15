
"""\brief Define IGBT reliability behavior for power semiconductor calculations.

This module is part of the PELCA reliability evaluator.
"""
from inverter_reliability.igbt_reliability.components.power_semi import PowerSemi
from inverter_reliability.igbt_reliability.calculations.calc_Tj_values_IEC import calc_Tj_values_IEC
from inverter_reliability.igbt_reliability.calculations.calc_Tj_values_PWM import calc_Tj_values_PWM

# an IGBT is a power semi with specific lambda0_TH and process_grade values
class IGBT(PowerSemi):
    """Represent i g b t behavior used by reliability calculations."""
    def __init__(self, device_params, Nb_dies=3, lambda0_TH=0.56):
        """Initialize the object with the provided configuration."""
        super().__init__(device_params=device_params, Nb_dies=Nb_dies, lambda0_TH=lambda0_TH, process_grade=2)

    # calc_TJ_components defined here returns also values related to diode
    # <the same calculation is actually made to find diode related values>

    # life_ratio = Operating_hours_per_year/8760
    # Tx: ambient temperature during this segment of mission profile
    # load_factor: % of output power (specification of operating point)
    # def calc_TJ_component(self, params, life_ratio, load_factor, Tx):
    # change of parameters!
    def calc_TJ_component(self,
                          params, Rel_torque_i, Rel_speed_i,  Tx,
                          display_sim_IEC=True,
                          plot_cond_currents_en_IEC=True,
                          display_sim_pwm=True,
                          plot_cond_currents_en_pwm=True,
                          plot_tj_en_pwm=True):
        """
        supposed to be specific to IGBT - but actually calculate both igbt & diode TJ
        (while only igbt Tj param are returned)

        Parameters
        ----------
        params : TYPE
            DESCRIPTION.
        Rel_torque_i : TYPE
            DESCRIPTION.
        Rel_speed_i : TYPE
            DESCRIPTION.
        Tx : TYPE
            DESCRIPTION.
        display_sim_IEC : TYPE, optional
            DESCRIPTION. The default is True.
        plot_cond_currents_en_IEC : TYPE, optional
            DESCRIPTION. The default is True.
        display_sim_pwm : TYPE, optional
            DESCRIPTION. The default is True.
        plot_cond_currents_en_pwm : TYPE, optional
            DESCRIPTION. The default is True.
        plot_tj_en_pwm : TYPE, optional
            DESCRIPTION. The default is True.

        Returns
        -------
        Tj_Q : TYPE
            DESCRIPTION.
        deltaT_Q : TYPE
            DESCRIPTION.
        Tj_Q_pwm : TYPE
            DESCRIPTION.
        deltaT_Q_pwm : TYPE
            DESCRIPTION.

        """

        # the calculation might be specific to diodes
        # _, Tj_Q, _, deltaT_Q = calc_Tj_values(params, self.device_params,  life_ratio, load_factor, Tx)
        # losses calculated at present using IEC  method
        # parameters have changed!
        semicond_temperatures, semicond_powers = calc_Tj_values_IEC(params, self.device_params, Rel_torque_i, Rel_speed_i, Tx,
                                                  display_sim=display_sim_IEC,
                                                  plot_cond_currents_en=plot_cond_currents_en_IEC)

        Tj_Q     = semicond_temperatures["Tj_Q"]
        deltaT_Q = semicond_temperatures["deltaT_Q"]

        # calculation also using simulation at "pwm" level for comparison
        # _, Tj_Q_pwm, _, deltaT_Q_pwm = calc_Tj_values_PWM(params, self.device_params,  life_ratio, load_factor, Tx)
        # parameters have changed!
        semicond_temperatures, semicond_powers = calc_Tj_values_PWM(params, self.device_params, Rel_torque_i, Rel_speed_i,  Tx,
                                                          display_sim=display_sim_pwm,
                                                          plot_cond_currents_en=plot_cond_currents_en_pwm,
                                                          plot_tj_en=plot_tj_en_pwm)
        Tj_Q_pwm     = semicond_temperatures["Tj_Q"]
        deltaT_Q_pwm = semicond_temperatures["deltaT_Q"]

        #return Tj_Q, deltaT_Q
        return Tj_Q, deltaT_Q, Tj_Q_pwm, deltaT_Q_pwm

    def calc_lambda(self, profile_data, params, debug_log=True, use_iec_temp=True):
        """
        determines the FIT rate of one IGBT  of the inverter part for a given mission profile
        (using FIDES method)

        Parameters
        ----------
            :param profile_data: one mission profile
            :param params: parameters
            :param debug_log: boolean => disable/enable debug log
            :param use_iec_temp: boolean : losses calculation method used => True: IEC / False: PWM

        Returns
        -------
        lambda_component : float
            failure rate of one IGBT (in FIT).


        """
        lambda_igbt = self.calc_lambda_common(profile_data, params, self.lambda0_TH, self.process_grade, component_type='igbt',  debug_log=debug_log, use_iec_temp=use_iec_temp)
        return lambda_igbt

# note: can not be evaluated within the components subdirectory (not possible to perform the imports)
