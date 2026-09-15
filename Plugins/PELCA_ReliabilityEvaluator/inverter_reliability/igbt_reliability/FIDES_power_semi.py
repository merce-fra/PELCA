# -*- coding: utf-8 -*-
"""\brief Prototype FIDES reliability calculations for power semiconductor replacement units.

This module is part of the PELCA reliability evaluator.
"""

"""
used to evaluate the fit rate of power conductor (diode or IGBT)

Question: what version of FIDES should we consider...? 2009 as excel sheet or 2022 since most recent?

TODO:  construct tuple_list (e.g. [(1261440000, 3, 80), (157680000, 1, 50), (157680000, 1, 45)] )
for each mission profle. (to construct with data determined during electro-thermal simulations)

"""

from utils.get_mission_profile import read_excel_to_dict #, display_blocks, get_block_variables
from utils.read_parameters import read_parameters

import math

# calculation of parameters for the RU

# for inverter we have 6 power modules, composed of 2 igbts + 2 diodes
# - for random part, failure rate of all components considered.
# - for ageing part (end of life determination), only the components that fail earlier are considered (?)

# - since we have N (6) modules in inverter, considering that each failure leads to system failure,
# lambda should be multiplied by N: (derived from product of reliabilities of modules)
# Rmod1(t)*Rmod2(t)*...*Rmod6(t)=(exp(-lambda*t))**6=exp(-6*lambda*t) => lamda_eq =6*lambda (module)
#
# On the other hand (for wearout), lifetime of bank  = lifetime of the weakest component.
# Since all modules are expected to age rather similarly (same lambda_wearout for each module),
# the lifetime of the RU is expected to be close (?) to the lifetime of one module:

# (under assumption that reliability of ageing module follows a weibull law)
# slightly less maybe... R = exp(-N*(lambda_wearout*t)**beta_wearout) = exp(-(lambda_eq*t)**beta_wearout)
# lambda_eq = lambda_wearout * N**(1/beta_wearout)
# with N=6
#   - at low beta_wearout  (2 for instance) : lambda_eq = 2.45 x lambda_wearout <slow ageing>
#   - at large beta_wearout (8?):             lambda_eq = 1.25 x lambda_wearout <fast ageing>


# reliability of one module: composed of two IGBTs + 2 diodes
# under assumption that all IGBTs in system has the same thermal stress (same for diode):
#  - all IGBT (of inverter) have the same lamda_igbt
#  - all diodes (of inverter) have the same lambda_diode

# the reliability of one module is thus: <effect of package included in calculation>
# lambda_mod = 2 x lambda_igbt + 2_lambda_diodes

# the lamnda all all inverter stage is thus : lambda_mod x 6 (number of modules)



def RU_wearout_scaling_factor(N, beta_wearout):
    # eta = Lx / (gamma(1+1/beta)) for a single module
    # eta = Lx / (gamma(1+1/beta) * N**(1/beta)) for N modules
    """Run r u wearout scaling factor."""
    scaling_factor = 1/(math.gamma(1 + 1/beta_wearout)*N ** (1/beta_wearout))
    return scaling_factor

def calc_Weibull_parameters_for_inverter_RU(params, lifetime, eta_random):

    """Calculate weibull parameters for inverter r u."""
    PELCA_params = {}
    params['nb_parallel_modules'] = 2 # non existant parameter at present
    # nb_components of same type to be considered for ageing part (12 IGBTs or 12 diodes depending on which one fails earlier)
    # => 12 components in both cases
    nb_components = 6 * params['nb_parallel_modules']

    # determination of parameters for PELCA (specification of bathtub model for a replacement unit, i.e. the inverter RU)

    # early life not evaluated
    # if information is available, this must be updated manually in PELCA input
    # constant default values considered here
    PELCA_params['beta_early']=0.6
    PELCA_params['eta_early']=3424

    # random part:
    PELCA_params['beta_random']=1
    PELCA_params['eta_random']=[eta / nb_components for eta in eta_random] #  list of characteristic life (random) - beta random=1

    # wearout part:
    # beta_wearout = 1.5 or 2 for instance for slow ageing
    # 3 to 4 for faster ageing
    PELCA_params['beta_wearout'] = 3
    PELCA_params['eta_wearout']=[Lx * RU_wearout_scaling_factor(nb_components,PELCA_params['beta_wearout'] ) for Lx in lifetime] # list of characteristic life for wearout part
    # eta_wearout = scaling_factor * lifetime

    return PELCA_params



if __name__ == '__main__':
    # check

#    from igbt_reliability.utils.get_mission_profile import read_excel_to_dict #, display_blocks, get_block_variables
#    from igbt_reliability.utils.read_parameters import read_parameters

    # Load Excel data
    excel_path  = 'old/inverter_stage_data.xlsx'  # old format of mission profiles
    param_sheet = 'parameters'      # Sheet where parameters are stored
    #result_sheet = 'results'        # Sheet where results are written

    # get mission profiles from Excel sheet
    mission_profile_dict = read_excel_to_dict(excel_path, sheet_name='mission_profile')

    params = read_parameters(excel_path, param_sheet)  # build dictionary with parameters

    # debug
    print("=> params from excel file are read")

    from components.DeviceParameters import DeviceParameters
    from components.diode import Diode
    from components.igbt import IGBT

    reference_module_params = DeviceParameters(params) # component parameters to enable calculation of losses (conduction & switching)
    reference_module_diode  = Diode(device_params=reference_module_params) # PowerSemi with specific lambda0_TH (for FIDES model)
    reference_module_igbt   = IGBT(device_params=reference_module_params)  # "

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # here perform evaluation on a single mission profile
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # get first mission profile
    # block_number = 1
    block_data = mission_profile_dict[1]
    def convert_to_number(value):
        """Convert to number."""
        if isinstance(value, (int, float)):
            return value  # Return as is if already numeric
        value = str(value).strip()  # Ensure value is treated as a string
        try:
            return float(value) if '.' in value else int(value)
        except ValueError:
            return value
    mission_profile = [
        [convert_to_number(value) for key, value in variables.items() if key.lower() != "mission profile"]
        for variables in block_data.values() ]

    # note: mission_profile here is just a list or ordered parameters

    # debug
    print("=> mission profile are read")

    # Note: Tj, deltaT must be part of mission profile (completed after electro-thermal simulation)
    # reference_module_diode_reliab_model.reliab_calc(mission_profile, params)
    # reference_module_igbt_reliability_model.reliab_calc(mission_profile, params)

    print("\n\ndetermine fit rate of diode")
    diode_MTTF = reference_module_diode.reliab_calc(mission_profile, params)
    diode_FITrate = 1/(diode_MTTF/1e9)

    print("\n\ndetermine fit rate of igbt")
    igbt_MTTF = reference_module_igbt.reliab_calc(mission_profile, params)
    igbt_FITrate  = 1/(igbt_MTTF/1e9)

    # <both calculations might be done simultaneously>

    print("Diode MTTF (h):", diode_MTTF)
    print("IGBT MTTF (h):", igbt_MTTF)

    # fit rate total for one module:
    # 2 x IGBT + 2 x diodes
    moduleFit_rate =  2*diode_FITrate + 2*igbt_FITrate

    # for 2 modules in // => 2 x moduleFit_rate

    # 3 legs => 3 x 2 x moduleFit_rate
    inverterFit_rate = 6 * moduleFit_rate

    # final report
    print("diode_FITrate: ", diode_FITrate )
    print("igbt_FITrate: ", igbt_FITrate )
    print("moduleFit_rate: ", moduleFit_rate )
    print("inverterFit_rate: ", inverterFit_rate )

    print("MTTF (year) inverter:", (1/inverterFit_rate)*1e9/8760)

    # to add: ageing model
    from lifetime.AgeingModel import AgeingModel
    IGBT_LifetimeModel =  AgeingModel()

    # Nfi = IGBT_LifetimeModel.calc_Nf( deltaTj, T_m)
    # determine for each segment the theoretical number of cycles to failures : Nfi

    # accumulate the total number of cycles applied : Ncycles
    # for each interval the fraction of cycles applied is Ki = Ni/Ncycles

    # derive equivalent damage (%) for the number of cycles applied (Ni) : Ni/Nfi
    # accumulate the partial damages

    # in the end derive equivalent lifetime (in cycles) = 1 / sum (Ki/Nfi)


    # calc lifetime IGBT
    # calc lifetime diode
    # shortest_lifetime = min(life_time_igbt, life_time_diode)


    # calculate parameters for PELCA
    # determination of parameters for PELCA (specification of bathtub model for a replacement unit, i.e. inverter RU)
    #print("Calculation of parameters for PELCA (for the replacement unit, i.e. the 6 power modules of the inverter block)")
    #PELCA_params = calc_Weibull_parameters_for_inverter_RU(params, lifetime, eta_random)




