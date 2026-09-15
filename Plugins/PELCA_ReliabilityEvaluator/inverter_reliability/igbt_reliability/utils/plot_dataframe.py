# -*- coding: utf-8 -*-
"""\brief Plot waveform, current, loss, and thermal DataFrame results.

This module is part of the PELCA reliability evaluator.
"""

import matplotlib.pyplot as plt
#plt.ion()
#plt.ioff()


# import matplotlib
# matplotlib.use("TkAgg")  # ou "Qt5Agg"
# import matplotlib.pyplot as plt

# displays some curves from dataframe passed as argument
def plot_current_and_modulation_functions(results):

    #plt.figure()
    """Plot current and modulation functions results."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Plot currents.
    ax1.plot(results['time (s)'], results['i_a (A)'], label='i_a (A)', color='r')
    ax1.plot(results['time (s)'], results['i_b (A)'], label='i_b (A)', color='g')
    ax1.plot(results['time (s)'], results['i_c (A)'], label='i_c (A)', color='b')
    ax1.set_ylabel('Courant (A)')
    ax1.legend(loc='upper right')
    ax1.grid(True)

    # Plot modulation functions.
    ax2.plot(results['time (s)'], results['Duty_a (0-1)'], label='Duty_a', color='r')
    ax2.plot(results['time (s)'], results['Duty_b (0-1)'], label='Duty_b', color='g')
    ax2.plot(results['time (s)'], results['Duty_c (0-1)'], label='Duty_c', color='b')
    ax2.set_xlabel('Temps (s)')
    ax2.set_ylabel('Duty (0-1)')
    ax2.legend(loc='upper right')
    ax2.grid(True)

    plt.suptitle('Courants et fonctions de modulation en fonction du temps')
    plt.tight_layout()
    plt.show()
    #plt.show(block=False)
    #fig.show()
    #return fig

def plot_cond_currents(results):

    #plt.figure()
    """Plot cond currents results."""
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

    # Current flow through semiconductors of leg A
    ax1.plot(results['time (s)'], results['I_cond_Sa (A)'], label='i_cond_Sa (A)', color='r')
    ax1.plot(results['time (s)'], results['I_diode_D\'a (A)'], label='i_diode_D\'a (A)', color='g')
    ax1.plot(results['time (s)'], results['I_cond_S\'a (A)'], label='i_cond_S\'a (A)', color='b')
    ax1.plot(results['time (s)'], results['I_diode_Da (A)'], label='i_diode_Da (A)', color='black')
    ax1.set_ylabel('Courant (A)')
    ax1.legend(loc='upper right')
    ax1.grid(True)

    # # Current flow through semiconductors of leg B
    ax2.plot(results['time (s)'], results['I_cond_Sb (A)'], label='i_cond_Sb (A)', color='r')
    ax2.plot(results['time (s)'], results['I_diode_D\'b (A)'], label='i_diode_D\'b (A)', color='g')
    ax2.plot(results['time (s)'], results['I_cond_S\'b (A)'], label='i_cond_S\'b (A)', color='b')
    ax2.plot(results['time (s)'], results['I_diode_Db (A)'], label='i_diode_Db (A)', color='black')
    ax2.set_ylabel('Courant (A)')
    ax2.legend(loc='upper right')
    ax2.grid(True)

    # # Current flow through semiconductors of leg C
    ax3.plot(results['time (s)'], results['I_cond_Sc (A)'], label='i_cond_Sc (A)', color='r')
    ax3.plot(results['time (s)'], results['I_diode_D\'c (A)'], label='i_diode_D\'c (A)', color='g')
    ax3.plot(results['time (s)'], results['I_cond_S\'c (A)'], label='i_cond_S\'c (A)', color='b')
    ax3.plot(results['time (s)'], results['I_diode_Dc (A)'], label='i_diode_Dc (A)', color='black')
    ax3.set_ylabel('Courant (A)')
    ax3.legend(loc='upper right')
    ax3.grid(True)

    ax3.set_xlabel('Time (s)')

    plt.suptitle('conduction of diode and IGBT as function of time')
    plt.tight_layout()
    plt.show()
    #fig.show()
    #return fig



def plot_P_total_semicond(results):

    #plt.figure()
    """Plot p total semicond results."""
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

    # Plot of the power dissipated in the semiconductors of leg A
    ax1.plot(results['time (s)'], results['P_total_Sa (W)'], label='P_total_Sa (W)', color='r')
    ax1.plot(results['time (s)'], results['P_total_D\'a (W)'], label='P_total_D\'a (W)', color='g')
    ax1.plot(results['time (s)'], results['P_total_S\'a (W)'], label='P_total_S\'a (W)', color='b')
    ax1.plot(results['time (s)'], results['P_total_Da (W)'], label='P_total_Da (W)', color='black')
    ax1.set_ylabel('Power (W)')
    ax1.legend(loc='upper right')
    ax1.grid(True)

    # # Plot of the power dissipated in the semiconductors of leg B
    ax2.plot(results['time (s)'], results['P_total_Sb (W)'], label='P_total_Sb (W)', color='r')
    ax2.plot(results['time (s)'], results['P_total_D\'b (W)'], label='P_total_D\'b (W)', color='g')
    ax2.plot(results['time (s)'], results['P_total_S\'b (W)'], label='P_total_S\'b (W)', color='b')
    ax2.plot(results['time (s)'], results['P_total_Db (W)'], label='P_total_Db (W)', color='black')
    ax2.set_ylabel('Power (W)')
    ax2.legend(loc='upper right')
    ax2.grid(True)

    # # Plot of the power dissipated in the semiconductors of leg C
    ax3.plot(results['time (s)'], results['P_total_Sc (W)'], label='P_total_Sc (W)', color='r')
    ax3.plot(results['time (s)'], results['P_total_D\'c (W)'], label='P_total_D\'c (W)', color='g')
    ax3.plot(results['time (s)'], results['P_total_S\'c (W)'], label='P_total_S\'c (W)', color='b')
    ax3.plot(results['time (s)'], results['P_total_Dc (W)'], label='P_total_Dc (W)', color='black')
    ax3.set_ylabel('Power (W)')
    ax3.legend(loc='upper right')
    ax3.grid(True)

    ax3.set_xlabel('Time (s)')

    plt.suptitle('losses of diode and IGBT as function of time')
    plt.tight_layout()
    plt.show()
    #fig.show()
    #return fig

# not used
def plot_P_avg_semicond(results):
    """Plot p avg semicond results."""
    plt.figure()
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

    # Plot of the average power dissipated in the semiconductors of leg A (during their conduction)
    ax1.plot(results['time (s)'], results['P_avg_Sa (W)'],   label='P_avg_Sa (W)', color='r')
    ax1.plot(results['time (s)'], results['P_avg_D\'a (W)'], label='P_avg_D\'a (W)', color='g')
    ax1.plot(results['time (s)'], results['P_avg_S\'a (W)'], label='P_avg_S\'a (W)', color='b')
    ax1.plot(results['time (s)'], results['P_avg_Da (W)'],   label='P_avg_Da (W)', color='black')
    ax1.set_ylabel('Courant (A)')
    ax1.legend(loc='upper right')
    ax1.grid(True)

    # Plot of the average power dissipated in the semiconductors of leg B
    ax2.plot(results['time (s)'], results['P_avg_Sb (W)'],   label='P_avg_Sb (W)', color='r')
    ax2.plot(results['time (s)'], results['P_avg_D\'b (W)'], label='P_avg_D\'b (W)', color='g')
    ax2.plot(results['time (s)'], results['P_avg_S\'b (W)'], label='P_avg_S\'b (W)', color='b')
    ax2.plot(results['time (s)'], results['P_avg_Db (W)'],   label='P_avg_Db (W)', color='black')
    ax2.set_ylabel('Courant (A)')
    ax2.legend(loc='upper right')
    ax2.grid(True)

    # Plot of the average power dissipated in the semiconductors of leg C
    ax3.plot(results['time (s)'], results['P_avg_Sc (W)'],   label='P_avg_Sc (W)', color='r')
    ax3.plot(results['time (s)'], results['P_avg_D\'c (W)'], label='P_avg_D\'c (W)', color='g')
    ax3.plot(results['time (s)'], results['P_avg_S\'c (W)'], label='P_avg_S\'c (W)', color='b')
    ax3.plot(results['time (s)'], results['P_avg_Dc (W)'],   label='P_avg_Dc (W)', color='black')
    ax3.set_ylabel('Courant (A)')
    ax3.legend(loc='upper right')
    ax3.grid(True)

    ax3.set_xlabel('Time (s)')

    plt.suptitle('losses of diode and IGBT as function of time')
    plt.tight_layout()
    plt.show(block=False)
    #fig.show()
    #return fig




def plot_deltaT_devices(results):
    #plt.figure()
    """Plot delta t devices results."""
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

    # Plotting of delta TJ of the semiconductors of leg A
    ax1.plot(results['time (s)'], results['Delta_Tj_Sa (K)'],   label='Delta_Tj_Sa (K)', color='r')
    ax1.plot(results['time (s)'], results['Delta_Tj_D\'a (K)'], label='Delta_Tj_D\'a (K)', color='g')
    ax1.plot(results['time (s)'], results['Delta_Tj_S\'a (K)'], label='Delta_Tj_S\'a (K)', color='b')
    ax1.plot(results['time (s)'], results['Delta_Tj_Da (K)'],   label='Delta_Tj_Da (K)', color='black')
    ax1.set_ylabel('temperature (degC)')
    ax1.legend(loc='upper right')
    ax1.grid(True)

    # Plot of power dissipated in the semiconductors of leg B
    ax2.plot(results['time (s)'], results['Delta_Tj_Sb (K)'],   label='Delta_Tj_Sb (K)', color='r')
    ax2.plot(results['time (s)'], results['Delta_Tj_D\'b (K)'], label='Delta_Tj_D\'b (K)', color='g')
    ax2.plot(results['time (s)'], results['Delta_Tj_S\'b (K)'], label='Delta_Tj_S\'b (K)', color='b')
    ax2.plot(results['time (s)'], results['Delta_Tj_Db (K)'],   label='Delta_Tj_Db (K)', color='black')
    ax2.set_ylabel('temperature (degC)')
    ax2.legend(loc='upper right')
    ax2.grid(True)

    # Plot of power dissipated in the semiconductors of leg C
    ax3.plot(results['time (s)'], results['Delta_Tj_Sc (K)'],   label='Delta_Tj_Sc (K)', color='r')
    ax3.plot(results['time (s)'], results['Delta_Tj_D\'c (K)'], label='Delta_Tj_D\'c (K)', color='g')
    ax3.plot(results['time (s)'], results['Delta_Tj_S\'c (K)'], label='Delta_Tj_S\'c (K)', color='b')
    ax3.plot(results['time (s)'], results['Delta_Tj_Dc (K)'],   label='Delta_Tj_Dc (K)', color='black')
    ax3.set_ylabel('temperature (degC))')
    ax3.legend(loc='upper right')
    ax3.grid(True)

    ax3.set_xlabel('Temps (s)')

    plt.suptitle('calculated deltaT of diodes and IGBTs')
    plt.tight_layout()
    plt.show()
    #fig.show()
    #return fig

# can be close later on as:  plt.close(fig)
