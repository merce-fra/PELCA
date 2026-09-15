# -*- coding: utf-8 -*-
"""\brief Compare junction-temperature estimation methods.

This module is part of the PELCA reliability evaluator.
"""
import numpy as np

def check_Tj_estimations(Tj_D, Tj_D_pwm, Tj_Q, Tj_Q_pwm, deltaT_D, deltaT_D_pwm, deltaT_Q, deltaT_Q_pwm ):
    """
    used to compare temperatures estimations obtained by both methods (IEC & PWM level calculation)

    Parameters
    ----------
    Tj_D : float
        estimated junction temperature of diode using IEC formula
    Tj_D_pwm : float
        estimated junction temperature of diode using "PWM" calculation
    Tj_Q : float
        DESCRIPTION.
    Tj_Q_pwm : float
        DESCRIPTION.
    deltaT_D : float
        DESCRIPTION.
    deltaT_D_pwm : float
        DESCRIPTION.
    deltaT_Q : float
        DESCRIPTION.
    deltaT_Q_pwm : float
        DESCRIPTION.

    Returns
    -------
    None.

    """

    # calculation of relative errors between IEC loss calculation & "pwm" level simulation
    # <to check if IEC calculation is good enough for that task>
    err_Tj_D_IEC_vs_PWM = (Tj_D-Tj_D_pwm)/Tj_D_pwm # -6% -0.4%
    err_Tj_Q_IEC_vs_PWM = (Tj_Q-Tj_Q_pwm)/Tj_Q_pwm # -10% -1.4%
    err_deltaT_D_IEC_vs_PWM = (deltaT_D-deltaT_D_pwm)/deltaT_D_pwm # -28% -3.7%
    err_deltaT_Q_IEC_vs_PWM = (deltaT_Q-deltaT_Q_pwm)/deltaT_Q_pwm # -21% -8.8%

    # note relatively low difference between delta T:
        # deltaT_D-deltaT_D_pwm    : -0.5degC
        # deltaT_Q-deltaT_Q_pwm    : -0.8degC
        # more import error on estimation of Tj (avg temp)

    # debug
    # check of relative errors
    # display only if there are "significant" errors

    if np.abs(err_Tj_D_IEC_vs_PWM)>0.05:
        print("relative err_Tj_D_IEC_vs_PWM (%): ", err_Tj_D_IEC_vs_PWM)
        print("Tj_D: ",Tj_D, " Tj_D_pwm: ", Tj_D_pwm)
    if np.abs(err_Tj_Q_IEC_vs_PWM)>0.05:
        print("relative err_Tj_Q_IEC_vs_PWM (%): ", err_Tj_Q_IEC_vs_PWM)
        print("Tj_Q: ",Tj_Q, " Tj_Q_pwm: ", Tj_Q_pwm)
    if np.abs(err_deltaT_D_IEC_vs_PWM)>0.05:
        print("relative err_deltaT_D_IEC_vs_PWM (%): ", err_deltaT_D_IEC_vs_PWM)
        print(f"deltaT_D: {deltaT_D}degC ; deltaT_D_pwm: {deltaT_D_pwm}degC")
    if np.abs(err_deltaT_Q_IEC_vs_PWM)>0.05:
        print("relative err_deltaT_Q_IEC_vs_PWM (%): ", err_deltaT_Q_IEC_vs_PWM)
        print(f"deltaT_Q: {deltaT_Q} degC ; deltaT_Q_pwm: {deltaT_Q_pwm}")

    return
