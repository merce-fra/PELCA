# -*- coding: utf-8 -*-
"""\brief Calculate wear-out lifetime from thermal cycling stress.

This module is part of the PELCA reliability evaluator.
"""

import numpy as np
import matplotlib.pyplot as plt
import math

# Ageing law.
# Empirical lifetime model based on thermal-cycling fatigue literature.
class AgeingModel:
    """Represent ageing model behavior used by reliability calculations."""
    def __init__(self, Ea: float = 9.89e-20, C: float = 302500, alpha: float = -5.039  ):
        """Initialize the object with the provided configuration."""
        self.k_B   = 1.38e-23 # Boltzman constant (J/K)

        self.Ea    = Ea     # (J)
        # 1 J = 6,242e+18 eV => Ea = 0.617 eV

        self.C     = C      # K**-alpha
        self.alpha = alpha

    # could be also a Coffin-Manson / Norris-Landzberg variant
    # Assumed to take into account thermo-mechanical fatigue due to junction temperature variations:
    # - solders (chip-substrate, substrate-baseplate),
    # - bonding wires,
    # - thermal interfaces.

    # Here only the amplitude of thermal cycle (variation max-min around avg value) and avg value is considered for
    # determination of cycles to failure

    # (duration of termal cycles is not considered)
    # * fast cycles (< 1s), small deltaT (& .. 10K), important thermal gradient locally => impact mostly on wirebonds  typically for deltaT > 5K
    # * Average cycles (acceleration/deceleration, torque variation, partial start/stop...) mission profile related
    #   deltaT can be more important / number of cycles important (duration of cycles from seconds to minutes)
    # * long cycles (cycles day/night, cold start ) MP related = large deltaT, long durations hours... : impact on solders...

    def calc_Nf(self, deltaTj, T_m):
        """  "ageing" model for semiconductor (diode or IGBT)
         returns the number of cycles to failure for a device (IGBT or diode die)
         operating at avg junction temp T_m, with tempeature cycles=deltaTjc """

        # temperature T_m is in degC => converted in K in formula
        if deltaTj==0:
            Nf = math.inf
        else:
            Nf = self.C*(deltaTj)**self.alpha * np.exp(self.Ea/(self.k_B*(T_m+273)))
        return Nf

    # model used by : Nb_Of_Cycles=@(x) (x^-5)*(10.^15); % N_f (PoF Model)
    # <behaves similarly for Tm=50degC>

    # the lower number of cycles between diode and IGBT will be considered the lifetime

    # note: how to convert number of cycles in number of hours of operation?
    # => one must define a number of cycles per year of usage (considering off time also, ...)


    def plot_lifetime_graph(self):
        """ to display curves Nf vs deltaT, for different t_m values """

        fig, ax1 = plt.subplots(1, 1, layout='constrained')
        deltaTj_vect = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50] # in degC
        for t_m in (25,50,75,100): # in degC
            N_f_vect = []
            for deltaTj in deltaTj_vect:
                N_f_vect.append(self.calc_Nf(deltaTj, t_m))

            # should plot on log-log scale?
            #ax1.semilogy(deltaTj_vect, N_f_vect, 'o--', label=f"T_m={t_m}")
            ax1.loglog(deltaTj_vect, N_f_vect, 'o--', label=f"T_m={t_m}")

            ax1.grid()
            ax1.grid(which="minor", color="0.9")

        ax1.legend(loc="upper right")
        fig.show()






    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # <normally there should be one tuple list per device:
    # 6 x IGBT, 6 diodes => or at least one IGBT, once diode if we consider that each device of a particular type has the same avg thermal stress
    # Maybe preferable to put them in a DataFrame (instead of a list)>
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    # simplication assumptions:
    # there is only one deltaT and t_m par segment (neglect transient duration for t_m; deltaT assumed constant)
    def calc_lifetime_mission_profile(self, mission_profile, tuple_list):
        """
        calculate the lifetime for a given device


        Parameters
        ----------
        mission_profile : TYPE
            needed to get the life_ratio spent in each segment

        tuple_list : TYPE
            The list contains the tuples required to estimate lifetime in each segment of mission profile.
            Each tuple contains: (Ni, deltaTj_i, T_m_i) with:
                Ni: number of cycles with thermal variation deltaTj_i at averaged junction temperature T_m_i

        Returns
        -------
        Lifetime_years : TYPE
            lifetime estimated (in years).

        """

        if str(type(mission_profile))=="<class 'pandas.DataFrame'>":  # "<class 'pandas.core.frame.DataFrame'>":
            #print("unsupported mission profile format right now")
            named_args = True
        else:
            named_args = False


        total_inverse_life = 0 # sum of (life_ratio / Lx_hours) for all the segments

        # <note: life_ratio might be recalculated: Ni / total number of cycle>

        if not named_args:
            DA = 0 # total damage accumulation
            for idx, segment in enumerate(mission_profile):
                life_ratio, _, Tx = segment[:3] # variables assignment with 3 first values of segment read

                curr_tuple = tuple_list[idx]
                N_i        = curr_tuple[0]
                deltaTj_i  = curr_tuple[1]
                T_m_i      = curr_tuple[2]

                # check if one of the variables is NaN
                if any(math.isnan(val) for val in (life_ratio, Tx)):
                    print(f"Ignored segment #{idx} (invalid values) : {segment}")
                    continue

                # number of cycles to failure
                Nfi = self.calc_Nf(deltaTj_i, T_m_i)

                # damage calculation
                Di = N_i / Nfi   # number of thermal cycles during ti (duration of segment i)

                # damage accumulation
                DA = DA + Di

                # total_inverse_life += life_ratio / Lx_hours
                Lx_hours = ((life_ratio * 8760)/Di) # expected lifetime under these conditions: ref duration/degradation level
                total_inverse_life += (life_ratio / Lx_hours)
        else:
           # mission profile as a dataframe
           DA = 0 # total damage accumulation
           for idx in range(len(mission_profile)):
               life_ratio=mission_profile.iloc[idx]['life_ratio']
               #print("life_ratio:",life_ratio)
               Tx = mission_profile.iloc[idx]['Tx']

               # the remaining is identical
               curr_tuple = tuple_list[idx]
               N_i        = curr_tuple[0] # number of thermal cycles par year
               deltaTj_i  = curr_tuple[1] # corresponding temperature deltaT
               T_m_i      = curr_tuple[2] # and avg Tj temperature

               # check if one of the variables is NaN
               if any(math.isnan(val) for val in (life_ratio, Tx)):
                   print(f"Ignored phase #{idx} (invalid values) : {mission_profile.iloc[idx]}")
                   continue

               if mission_profile.iloc[idx]['Operating_Phase']:

                   # number of cycles to failure
                   Nfi = self.calc_Nf(deltaTj_i, T_m_i) # very large at low deltaTj_i...

                   # damage calculation
                   Di = N_i / Nfi   # number of thermal cycles during ti (duration of segment i)

                   # damage accumulation
                   DA = DA + Di # once DA=1 lifetime is supposed to be finished

                   # total_inverse_life += life_ratio / Lx_hours
                   Lx_hours = ((life_ratio * 8760)/Di) # expected lifetime under these conditions: (ref duration)/degradation level
                   total_inverse_life += (life_ratio / Lx_hours)
               else:
                   Di = 0 # assumption: no damage during  non operating phase



        # DA represent the total degradation for one year
        # the lifetime in hours is thus : 8760/DA
        # in years it is : 1/DA


        # total_inverse_life unit : (1 / number of cycles)
        # convert in (1/hours) by dividing by 8760?


        # global lifetime calculation
        Lifetime_hours = 1 / total_inverse_life
        # should theoretically the same as : 8760 x (1 / DA)

        Lifetime_years = Lifetime_hours / (365 * 24) # convert in years (considering 8760 h/year)

        return Lifetime_years


    # wearout calculated considering the N_cy variation of Tc (delta_TC_cycling) + N_fout_cy * deltaT_D (or deltaT_Q)
    def calc_wearout_mission_profile(self, mission_profile, component_type, use_iec_temp=True):
        """
        calculate the lifetime for a given device


        Parameters
        ----------
        mission_profile : dataframe
            copy of current mission profile enriched with thermal data obtained from electro-thermal simulation
            (we will need information such as: Ni, deltaTj_i, T_m_i with:
                Ni: number of cycles with thermal variation deltaTj_i at averaged junction temperature T_m_i)

        component_type : str
            'diode' / 'igbt'  (to indicate which thermal data to use)

        Returns
        -------
        Lifetime_years : TYPE
            lietime estimated (in years).

        """

        total_inverse_life = 0 # sum of (life_ratio / Lx_hours) for all the segments

        # <note: life_ratio might be recalculated: Ni / total number of cycle>

        # mission profile as a dataframe
        DA = 0 # total damage accumulation
        for idx in range(len(mission_profile)):
            # suppressed: can be calculated
            #life_ratio=mission_profile.iloc[idx]['life_ratio']
            life_ratio = mission_profile.iloc[idx]['Operating_Hours_per_Year'] / 8760
            #print("life_ratio:",life_ratio)

            # number of "short cycles" due to generation of output current
            N_i        = mission_profile['N_fout_cy'].to_numpy()[idx]  # number of thermal cycles per year (number of fout periods)
            # temperature cycles / avg temperature (of igbt or diode) due to f_out

            # the number of "long cycles" (duration theta_i) : N_cy_i
            N_cy_i     = mission_profile['N_cy'].to_numpy()[idx]

            if component_type=='diode':
                if use_iec_temp:
                    # use iec temp
                    # parameters for "short cycles" / low deltaT
                    deltaTj_i  = mission_profile['deltaT_D_iec'].to_numpy()[idx]   # corresponding temperature deltaT
                    T_m_i      = mission_profile['Tj_D_iec'].to_numpy()[idx]       # and avg Tj temperature
                else:
                    #use pwm temp
                    deltaTj_i  = mission_profile['deltaT_D_pwm'].to_numpy()[idx]   # corresponding temperature deltaT
                    T_m_i      = mission_profile['Tj_D_pwm'].to_numpy()[idx]       # and avg Tj temperature

                # parameters for "long cycles" / large deltaT
                deltaTj_phase = mission_profile['deltaTj_D_phase'].to_numpy()[idx]  # no distinction done in choice of temp model
                Tjm_phase     = mission_profile['Tj_D_phase'].to_numpy()[idx]
            else:
                # igbt
                if use_iec_temp:
                    deltaTj_i  = mission_profile['deltaT_Q_iec'].to_numpy()[idx]   # corresponding temperature deltaT
                    T_m_i      = mission_profile['Tj_Q_iec'].to_numpy()[idx]       # and avg Tj temperature
                else:
                    # use pwm temp
                    deltaTj_i  = mission_profile['deltaT_Q_pwm'].to_numpy()[idx]   # corresponding temperature deltaT
                    T_m_i      = mission_profile['Tj_Q_pwm'].to_numpy()[idx]       # and avg Tj temperature

                # parameters for "long cycles"
                deltaTj_phase = mission_profile['deltaTj_Q_phase'].to_numpy()[idx]  # no distinction done in choice of temp model
                Tjm_phase     = mission_profile['Tj_Q_phase'].to_numpy()[idx]

            # # check if one of the variables is NaN
            # if any(math.isnan(val) for val in (life_ratio)):
            #     print(f"Ignored phase #{idx} (invalid values) : {mission_profile.iloc[idx]}")
            #     continue

            #if math.isnan(life_ratio):
            #    print(f"Ignored phase #{idx} (invalid values) : {mission_profile.iloc[idx]}")
            #    continue

            if mission_profile.iloc[idx]['Operating_Phase']:

                # "short cycles"
                # number of cycles to failure
                Nfi = self.calc_Nf(deltaTj_i, T_m_i) # VERY large at low deltaTj_i...

                # damage calculation
                Di = N_i / Nfi   # number of thermal cycles during ti (duration of segment i)

                # damage accumulation
                DA = DA + Di # once DA=1 lifetime is supposed to be finished

                if Di==0:
                    Lx_hours1  = np.inf
                else:
                    Lx_hours1 = ((life_ratio * 8760)/Di) # expected lifetime under these conditions: (ref duration)/degradation level

                # ==============================================================================
                # "long cycles"
                # number of cycles to failure
                Nfi = self.calc_Nf(deltaTj_phase, Tjm_phase)  # limited number of large deltaT

                # damage calculation
                Di = N_cy_i / Nfi  # number of thermal cycles during ti (duration of segment i)

                # damage accumulation
                DA = DA + Di  # once DA=1 lifetime is supposed to be finished
                # ==============================================================================

                if Di==0:
                    Lx_hours2  = np.inf
                else:
                    Lx_hours2 = ((life_ratio * 8760)/Di) # expected lifetime under these conditions: (ref duration)/degradation level

                total_inverse_life += (life_ratio / Lx_hours1) + (life_ratio / Lx_hours2)
            else:
                Di = 0 # assumption: no damage during  non operating phase

        # DA represent the total degradation for one year
        # the lifetime in hours is thus : 8760/DA
        # in years it is : 1/DA

        # total_inverse_life unit : (1 / number of cycles)
        # convert in (1/hours) by dividing by 8760?

        # global lifetime calculation
        if total_inverse_life==0:
            Lifetime_hours = np.inf
        else:
            Lifetime_hours = 1 / total_inverse_life
        # should theoretically the same as : 8760 * (1 / DA)

        Lifetime_years = Lifetime_hours / (365 * 24) # convert in years (considering 8760 h/year)

        return Lifetime_years


# test
if __name__ == "__main__":
    IGBT_LifetimeModel =  AgeingModel()
    IGBT_LifetimeModel.plot_lifetime_graph()

    # check lifetime calculation
    # Ni, deltaTj_i, T_m_i <should be calculated during el-thermal simu & stored in dataframe...>
    # approx here: Ni = ti / 0.02 = life_ratio_i x 8760 x 3600 / 0.02

    # example values - nothing realistic

    tuple_list = [(1261440000, 3, 80), (157680000, 1, 50), (157680000, 1, 45)]
    mission_profile = [[0.8, 1,    70, 0.92, 7008, 1, 0.3, 15, 40, 3650, 1.92, 0.3],
                       [0.1, 1,    50, 0.92, 876,  1, 0.3, 25, 65, 365,  2.4,  0.3],
                       [0.1, 0.01, 45, 0.92, 876,  1, 0.3, 25, 65, 10,   87.6, 0.3]]
    Lifetime_years = IGBT_LifetimeModel.calc_lifetime_mission_profile(mission_profile, tuple_list)
    print("lifetime_years:", Lifetime_years, " (years)")
