# -*- coding: utf-8 -*-
"""\brief Compute low-frequency and high-frequency capacitor bank ripple currents.

This module is part of the PELCA reliability evaluator.
"""
import numpy as np
import matplotlib.pyplot as plt
import math

# some improvements might be required: some parameters should come from Excel file ...

# ======================================================
# calculation of ripple within capacitor bank (LF + HF)
# ======================================================

# calculation of high frequency ripple at 8 kHz (Fsw=4 Khz)
# according to:
# Reference standard material for variable-speed drive efficiency calculations.
# rated real power      Pr,m   = Ir,out * sqrt(3) * U1.r,out * cosPhy * eta_nmotor
# apparent output power Sr,equ = sqrt(3) * U1.r,out * Ir,out
# Pout = Iout_rms*Vout_line_to_line*math.sqrt(3)*PF
def calc_bank_ripple_HF(Pout, Vout_rms, PF, Vdc):
    """Calculate bank ripple h f."""
    Vout_line_to_line = Vout_rms * math.sqrt(3)
    Iout_rms = Pout / (Vout_line_to_line*math.sqrt(3)*PF)
    V1m = Vout_rms*math.sqrt(2)
    V1m_6_step = 2*Vdc/math.pi
    Mi = V1m/V1m_6_step
    M = Mi*(4/math.pi)
    inverter_rms_current = Iout_rms*math.sqrt((2*math.sqrt(3)/math.pi)*M*(1/4+PF**2))
    Iout_rms = Pout / (Vout_line_to_line*math.sqrt(3)*PF)
    Iom = Iout_rms*math.sqrt(2) # Iout max (peak value)
    Iavg = (3/math.pi)*Mi*Iom*PF
    bank_ripple_HF = math.sqrt(inverter_rms_current**2-Iavg**2)
    return bank_ripple_HF

# ================================================================================
# calculation of low frequency ripple
# estimation sufficient <especially at high ripple current> to enable estimation of
#  losses due to low frequency ripple # in capacitor(s)
# ================================================================================

# ==================================
# capacitor bank ripple calculation
# =================================
# calculation of low frequency ripple at 300 Hz
# initially based on fitting of simulation data:
#   - above some power, ripple level is ~constant
#   - below, the fitting function applies

def calc_bank_ripple_LF(Pdc):
    """Calculate bank ripple l f."""
    if (Pdc<48204):
        bank_ripple_LF =  -0.00000001193*Pdc**2+  0.001858*Pdc +  3.343
    else:
        bank_ripple_LF =  65
    return bank_ripple_LF

calc_bank_ripple_LF_vec = np.vectorize(calc_bank_ripple_LF)  # Now this works on arrays

# now estimated using following function:
def calc_ripple_current_LF(Pdc):
    """Calculate ripple current l f."""
    V_dc = 514        # average DC bus voltage
    I_load = Pdc/V_dc # average output DC current (I0)

    Rload_equ = V_dc/I_load # equivalent load resistance

    # limit between DCM/CCM when I0 = Il_peak
    # Irect = Il = I0 + Il_ripple

    # Il_ripple = V6 / Ztot

    f1 = 50                          # input voltage fundamental freq (Hz)
    n = 6
    f6 = n * f1                      # 6th harmonic
    omega6 = 2 * np.pi * f6          # pulsation (rad/s)
    #PN=200000                        # nominal power

    # DC bus "filter"
    L = 200e-6                       # H
    C = 12e-3                        # F

    # VLL : line to line voltage input voltage (RMS)
    VLL=400
    Vp = VLL*np.sqrt(2)              # peak of rectified voltage

    # peak voltage amplitude of 6th harmonic (rectified voltage)

    A6 = 2*3*np.sqrt(3)*Vp/(35*np.pi*np.sqrt(2))
    # https://www.youtube.com/watch?v=WEVFsXgjvvc
    # https://beckassets.blob.core.windows.net/product/readingsample/425530/9780387293103_excerpt_001.pdf

    # appears higher than measured in simulation
    K=0.812 # correcting factor to better match with simulation...
    A6 = A6*K

    Z_L = 1j * omega6 * L               # impedance of DC reactor at 6th harmonic
    Z_C = 0.008 + 1 / (1j * omega6 * C) # strongly dominated by C (ESR neglectable)
    Z_RC = 1 / (1/Rload_equ + 1/Z_C)    # considering the load as a resistor in // with C
    Z_tot = Z_L + Z_RC                  # impedance seen by rectifier

    V_C = A6 * (Z_RC / Z_tot)           # voltage across capacitor
    I_C = V_C / Z_C

    I_C_rms_CCM = np.abs(I_C)/np.sqrt(2)

    # the ripple of current is quite sinusoidal, mainly dominated by h6 in CCM
    I_L_ripple_peak =  abs(A6/Z_tot)

    # if I_load = I_L_ripple_peak it is the limit of DCM/CCM
    # I_load = Pdc/V_dc =>
    Pdc_limit = I_L_ripple_peak*V_dc
    #print("Pdc_limit:", Pdc_limit)
    #print("Plimit for R=", 514**2/Pdc_limit)
    # the curve in DCM area can be approximated as a line between (Pdc=0, 0) & (Pdc_limit, I_C_rms_CCM)

    I_C_rms = I_C_rms_CCM * (Pdc/Pdc_limit)
    if I_C_rms>I_C_rms_CCM:
        return I_C_rms_CCM
    else:
        return I_C_rms


calc_ripple_current_LF_vec = np.vectorize(calc_ripple_current_LF)  # Now this works on arrays

def main():
    # Generate Pdc values
    """Run main."""
    Pdc = np.linspace(1, 200000, 400)

    # Plot the functions
    plt.plot(Pdc, calc_ripple_current_LF_vec(Pdc), label='calc_ripple_current_vec(Pdc)', color='blue')
    plt.plot(Pdc, calc_bank_ripple_LF_vec(Pdc), label='calc_bank_ripple_LF_vec(Pdc)', color='red')

    # Add labels and legend
    plt.title("Plot of calc_ripple_current(Pdc)")
    plt.xlabel("Pdc")
    plt.ylabel("calc_ripple_current(Pdc)")
    plt.legend()
    plt.grid(True)

    # Show the plot
    plt.show()

if __name__ == "__main__":
    main()




