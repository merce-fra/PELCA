# -*- coding: utf-8 -*-
"""\brief Convert inverter reliability results into PELCA Weibull parameters.

This module is part of the PELCA reliability evaluator.
"""


import math
def inv_wearout_scaling_factor(N, beta_wearout):
    # eta = Lx / (gamma(1+1/beta)) for a single capacitor
    # eta = Lx / (gamma(1+1/beta) * N**(1/beta)) for N capacitor
    """Run inv wearout scaling factor."""
    scaling_factor = 1/(math.gamma(1 + 1/beta_wearout)*N ** (1/beta_wearout))
    return scaling_factor


def calc_Weibull_parameters_for_inverter(params, lifetime, eta_random_HB):
    # determination of parameters for PELCA
    """Calculate weibull parameters for inverter."""
    nb_parallel_sw = params['nb_parallel_sw']
    nb_HB_modules = 3 * nb_parallel_sw

    PELCA_params = {}

    # determination of parameters for PELCA (specification of bathtub model for a replacement unit, i.e. the capacitor bank)

    # early life not evaluated
    # if information is available, this must be updated manually in PELCA input
    # constant default values considered here
    # early stage (default values - no data)
    beta_early = 0.6
    eta_early_years = 3424
    eta_early_system_years = eta_early_years / ((3*nb_parallel_sw) ** (1.0 / beta_early))
    #scale_early_system_years = eta_early_system_years
    #shape_early_system = beta_early

    PELCA_params['beta_early']=beta_early
    PELCA_params['eta_early']=eta_early_system_years

    # random part:
    PELCA_params['beta_random']=1
    PELCA_params['eta_random']=[eta / nb_HB_modules for eta in eta_random_HB] #  list of characteristic life (random) - beta random=1

    # wearout part:
    # beta_wearout = 1.5 or 2 for instance for slow ageing
    # 3 to 4 for faster ageing
    PELCA_params['beta_wearout'] = 3
    PELCA_params['eta_wearout']=[Lx * inv_wearout_scaling_factor(nb_HB_modules, PELCA_params['beta_wearout'] ) for Lx in lifetime] # list of characterisitic life for wearout part
    # eta_wearout = scaling_factor * lifetime

    return PELCA_params
