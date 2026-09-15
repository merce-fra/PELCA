# -*- coding: utf-8 -*-
"""\brief Evaluate electrolytic capacitor random failure rates with FIDES equations.

This module is part of the PELCA reliability evaluator.
"""

import pandas as pd
import numpy as np

class ELcapacitorFIDES:
    """Represent e lcapacitor f i d e s behavior used by reliability calculations."""
    def __init__(self, filename, sheet_name, params):  # filename, sheet_name needed to load mission profile

        # to load Excel data
        # mission profiles are in dataframe all_data
        """Initialize the object with the provided configuration."""
        self.all_data = pd.read_excel(filename, sheet_name) # no need to close Excel file for that
        self.num_rows = len(self.all_data)

        # Find starting indices for each mission profile  (two formats...)
        # beginning of mission profiles (line indexes in all_data dataframe)
        if 'MP' in self.all_data.keys():
            self.mission_profile_ID = 'MP'
        else:
            self.mission_profile_ID = 'mission profile'

        self.profile_start_indices = self.all_data.index[self.all_data[self.mission_profile_ID].notna() &
                                                         pd.to_numeric(self.all_data[self.mission_profile_ID], errors='coerce').notna()]
        self.num_profiles = len(self.profile_start_indices) # number of profiles
        self.profile_data = self.all_data

        self.Vapplied      = params.get('Vapplied', 540/2)  # added in dictionary normally

        #self.Vdc = params.get('Vin', 230) * np.sqrt(2) * np.sqrt(3) *  (3 / np.pi)
        #self.Vapplied = self.Vdc * params.get('voltage_ratio', 0.5) # default configuration 2 cap in series pers tring

        self.Vrated        = params.get('Vrated', 450)      # added in Excel file
        self.nb_capacitors = params.get('nb_capacitors', 4) # in Excel file

    # Different constants required by FIDES model (constants defined as class variables)
    t_total = 8760     # one (normal) year express in hours (24 * 365)

    # FIDES parameters for EL capacitors used in DC link bank

    # based on a score process_grade that reflects the quality of the process
    Pi_process = 4     # L4 = the recommendation is fully applied ->  no significant reliability risk.

    # parameters extracted from FIDES tool (2009)
    #piPlacement=1.0    # not used in equations
    piPM = 1.6          # ?

    #PITHVAR1=0.4       # Pi_thermo_electrical
    #piThVar3=15.0      # not used

    LAMBDA0CAPACITOR=0.21 # (FIT) for liquid electrolyte aluminum capacitor
    GAMMATHEL=0.85     #
    GAMMATCY=0.14      #
    GAMMAMECH=0.01     #
    SREFERENCE=0.5     # Sreference
    CSENSITIVITY=6.4   #

    Grms=0.3           #

    # from part counts reliability prediction (Aluminum capacitor part)
    # thermal
    lambdaTh = 0.26    # not used
    Ea_Th=0.4          # activation energy (eV)
    #T0=20
    #deltaT=0
    #alpha=0

    # humidity [not considered in that case]
    #lambdaRh=0
    #Ea_Rh=0

    # thermal cycling
    #lambdaTcy_B=0
    #m_b=1
    #lambdaTcy_JB=0.043
    #m_jb=1.9

    # mechanical
    #lambdaM=0.031
    #n=1.5
    #El.Ch.Wr
    #lambdaECW=0

    # relative sensitivity (mark out of 10)
    #EOS=7 # electrical overstress
    #MOS=7 # mechanical overstress
    #TOS=1 # thermal overstress
    # =>
    #Csensitivity=6.4  # CSENSITIVITY

    internPiPlacement = 1.0 # intern? same as PiPlacement?
    internPiRuggedizing = 1.6046230816172982
    internPiApplication = 1.9
    internSensitivity = CSENSITIVITY


    # Containers for results
    all_lambda_constant_profile = []
    all_overall_cdf_time = []
    all_overall_cdf_values = []
    profile_names = []
    all_cdf_results = []
    all_mttf_random = []

    def get_profile_data(self, index_profile):
        """Read profile data."""
        num_rows = len(self.all_data)
        num_profiles = len(self.profile_start_indices)
        # profile_names = []

        # get profile_data
        profile_start_row = self.profile_start_indices[index_profile]
        #    profile_id = int(all_data.loc[start_row, mission_profile_ID])
        # profile_names.append(f"Mission Profile {profile_id}")

        profile_end_row = self.profile_start_indices[index_profile + 1] - 1 if index_profile < num_profiles - 1 else num_rows - 1

        profile_data = self.all_data.iloc[profile_start_row:profile_end_row + 1]
        profile_data = profile_data.dropna(how='all')  # default: axis=0 (line) => suppress line(s) complete of nan
        return profile_data

    # ******************************************************************************************************************************************
    # only for test

    # def calc_piTcy(self, N_cy, Tphase, theta_cy, delta_T_cycling, T_max_cycling):
    #     piTcy = self.GAMMATCY * ((12*N_cy)/Tphase) * (np.minimum(theta_cy,2)/2)**(1/3) * ((delta_T_cycling)/20)**1.9 * np.exp(1414 * ((1/313) -(1/(T_max_cycling+273))))
    #     return piTcy

    def calc_fit_Tx(self, Tx):
        """
        calculate the fit rate at temperature Tx and with operating parameter: Vapplied, Vrated
        <used only for comparison with simple interpolation between two given values of FIT rate at two different temperatures>
        """
        piMech       = self.GAMMAMECH * (self.Grms / 0.5)**1.5   # pi_mechanical
        piThermoElec = self.GAMMATHEL * ((1/self.SREFERENCE)*self.Vapplied/self.Vrated)**3 * np.exp(11604*self.Ea_Th*((1/273)-1/(Tx + 273)))
        piTcy=0  # neglected piTcy

        piInduced       = (self.internPiPlacement * self.internPiApplication * self.internPiRuggedizing)**(0.511 * np.log(self.internSensitivity))
        lambda_physical = self.LAMBDA0CAPACITOR * (piThermoElec + piTcy + piMech) * piInduced
        lambda_constant = lambda_physical * self.piPM * self.Pi_process # constant failure rate
        return lambda_constant

    # CapBank_FIDES_model.calc_fit_Tx(40) = 50 FIT   <compared to 12 considered in previous study>
    # CapBank_FIDES_model.calc_fit_Tx(85) = 322 FIT  <compared to 250 considered in previous study>
    # Tx = np.linspace(40, 85, 45)
    # CapBank_FIDES_model.calc_fit_Tx(Tx)
    # plt.plot(Tx, CapBank_FIDES_model.calc_fit_Tx(Tx)) # FIDES a bit more pessimistic than typical datasheet values used previously
   # ******************************************************************************************************************************************


    # note: the definition of mission profile is different from previous version
    def calc_fit_FIDES_for_random_part_mission_profile(self):
        # the mission profile must be constructed from data in profile_data

        # get parameters columns
        #life_ratio_i      = self.profile_data['life_ratio'].to_numpy() # not used since Hours_per_Year_i is used instead
                                                                  # Hours_per_Year_i = life_ratio_i * 8760 (t_total)

        #PN_i              = self.profile_data['PN'].to_numpy()      # no direct use in model <indirect effect on temperature..>
        """Calculate fit f i d e s for random part mission profile."""
        T_i               = self.profile_data['Tx'].to_numpy()       # Tboard_ambient: temperature close to capacitor (air flow temperature)
        Hours_per_Year_i  = self.profile_data['Operating_Hours_per_Year'].to_numpy() #  t_annual ? time associated with each operating phase over a year (hours)
                                                                                     # now called t_phase in FIDES 2022

        Pi_application_i  = self.profile_data['Pi_application'].to_numpy()  # ignored:  the constant internPiApplication is used instead in calculation of FIT rate

        delta_T_cycling_i = self.profile_data['delta_T_cycling'].to_numpy() # maximum board temperature (?) during a cycling phase (degC)
        T_max_cycling_i   = self.profile_data['T_max_cycling'].to_numpy()   #
        N_cy_i            = self.profile_data['N_cy'].to_numpy()            # N_annual_cy : number of cycles associated with each cycling phase over a year (cycles)
        theta_cy_i        = self.profile_data['theta_cy'].to_numpy()        # cycle duration (hours)
        G_RMS_i           = self.profile_data['G_RMS'].to_numpy()           # stress associated with each random vibration phase

        operating_phase = self.profile_data['operating_phase'].to_numpy()
        # during a non-operating phase piThermoElec = 0

        # <mission profile data now ready to use>

        # calculate failure rate of components

        # factors contributing to physical stresses
        # Pi_Thermique_i <Pi_thermo_electrical>
        Pi_th_i = self.GAMMATHEL * ((1 / self.SREFERENCE) * self.Vapplied / self.Vrated) ** 3 * np.exp(
            11604 * self.Ea_Th * ((1 / 273) - 1 / (T_i + 273)))  # piThermoElec

        # Apply mask: True keeps value, False becomes 0
        Pi_th_i = np.where(operating_phase, Pi_th_i, 0)

        # PiTcy
        Pi_Tcy_i = self.GAMMATCY * ((12*N_cy_i)/self.t_total) * (np.minimum(theta_cy_i,2)/2)**(1/3) * \
            ((delta_T_cycling_i)/20)**1.9 * np.exp(1414 * ((1/313) -(1/(T_max_cycling_i+273))))


        piMech_i = self.GAMMAMECH * (G_RMS_i / 0.5)**1.5   # pi_mechanical

        # Pi_RH_i = gamma_Rh * (RH_ambient_i / 70)**4.4 * np.exp(11604 * 0.8 * ((1 / 293) - (1 / (T_i + 273))))

        pi_induced = (self.internPiPlacement * self.internPiApplication * self.internPiRuggedizing)**(0.511 * np.log(self.internSensitivity))

        # Aggregate physical failure rate
        weighted_stress_sum_profile = np.sum((Hours_per_Year_i / self.t_total) *
                                             (Pi_th_i + Pi_Tcy_i + piMech_i))  # suppressed Pi_RH_i

        # lambda_physical = LAMBDA0CAPACITOR  * sum_phases(i, Phases)((t_phase/t_total)*(PITHVAR1 + piTCy + piMech) * pi_induced)
        lambda_physical_profile = self.LAMBDA0CAPACITOR * weighted_stress_sum_profile * pi_induced

        # lambda_capacitor  (of a single capacitor)
        lambda_constant_profile = lambda_physical_profile * self.piPM * self.Pi_process

        # *******************************************************
        # adaptation for capacitor bank
        # With N capacitors lambda must be multiplied by N=self.nb_capacitors  (at least for random part)
        lambda_constant_profile = lambda_constant_profile
        # but here the fit returned is for a single capacitor
        # <the fit for the bank is calculated when generating PELCA parameters for the RU>


        fit_eq = lambda_constant_profile # random part (fit for the the bank, considering only the N capacitors - for instance balancing resistors not included)
        # *******************************************************

        # MTTF and eta calculations
        mttf_random_profile = 1e9 / lambda_constant_profile       # in hours

        mttf_random_profile = 1e9 / lambda_constant_profile if np.isscalar(lambda_constant_profile) else 1e9 / lambda_constant_profile[0]
        MTBF_years_eq = mttf_random_profile / self.t_total

        return fit_eq, MTBF_years_eq



# evaluated when this file is executed
if __name__ == "__main__":
    # example use:
    params = {}
    # creation of needed parameters
    params['Vapplied'] =  540/2 # Vdc/2
    params['Vrated'] = 450
    params['nb_capacitors'] = 4

    CapBank_FIDES_model = ELcapacitorFIDES("cap_analysis2.xlsx",'mission_profile', params)

    start_row = CapBank_FIDES_model.profile_start_indices[0]
    profile_id = int(CapBank_FIDES_model.all_data.loc[start_row, CapBank_FIDES_model.mission_profile_ID])
    CapBank_FIDES_model.profile_names.append(f"Mission Profile {profile_id}")

    end_row = (
        CapBank_FIDES_model.profile_start_indices[0 + 1] - 2
        if 0 < CapBank_FIDES_model.num_profiles - 1
        else CapBank_FIDES_model.num_rows
    )
    CapBank_FIDES_model.profile_data = CapBank_FIDES_model.all_data.iloc[start_row:end_row + 1]

    if not CapBank_FIDES_model.profile_data.empty:
        fit_eq, MTBF_years_eq = CapBank_FIDES_model.calc_fit_FIDES_for_random_part_mission_profile()
        print(f"Cap failure rate:{fit_eq:.2f} FIT; MTBF_years: {MTBF_years_eq:.2f} years")

    print('fit eq: ', fit_eq)
    print('MTBF_years_eq: ',MTBF_years_eq)
