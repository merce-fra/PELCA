# -*- coding: utf-8 -*-
"""\brief Calculate semiconductor conduction and switching losses.

This module is part of the PELCA reliability evaluator.
"""

# to do: simplify names used to identify columns of DataFrame (no need for units..)

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Important note:
# At present, the losses are calculated considering phase currents present in dataframe
# => This is considered the current flowing in ONE power module
#
# The actual phase current is shared between parallel modules but this is not handled here!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


from inverter_reliability.igbt_reliability.components.DeviceParameters import DeviceParameters # loss parameters for reference_module

from typing import List, Tuple
import pandas as pd
import numpy as np


class LossModel:
    """Encapsulates all device loss calculations, dependent on T_j."""
    # Tj of each device... normally

    def __init__(self, params: DeviceParameters):
        """Initialize the object with the provided configuration."""
        self.P = params
        self.device_map = self._define_device_map()

    def _define_device_map(self) -> List[Tuple[str, str, str, bool]]:
        """Defines all 12 devices and their properties."""

        # note: we consider that temperatures / losses in 2 parallel HB modules are the same
        # (the 12 additional dies [6 IGBT + 6 diodes] in these modules are  the same as below)
        # => losses should be determined considering that half the current goes in a switch
        # => the loses of the 24 dies go to the heat sink though! (the total losses must be multiplied by 2 at the end)

        # Tuple format: (Prefix, Type, I_phase_Column, Is_Top_Switch)
        return [
            ('Sa',   'IGBT', 'i_a (A)', True),  ('Da',   'DIODE', 'i_a (A)', True),
            ('S\'a', 'IGBT', 'i_a (A)', False), ('D\'a', 'DIODE', 'i_a (A)', False),
            ('Sb',   'IGBT', 'i_b (A)', True),  ('Db',   'DIODE', 'i_b (A)', True),
            ('S\'b', 'IGBT', 'i_b (A)', False), ('D\'b', 'DIODE', 'i_b (A)', False),
            ('Sc',   'IGBT', 'i_c (A)', True),  ('Dc',   'DIODE', 'i_c (A)', True),
            ('S\'c', 'IGBT', 'i_c (A)', False), ('D\'c', 'DIODE', 'i_c (A)', False),
        ]

    def calculate_conduction_currents(self, data: pd.DataFrame) -> pd.DataFrame:
        """Applies the duty cycle logic to find I_cond for all 12 devices."""
        # it is an averaged (mean) current: phase current multiplied by corresponding duty cycle, when applicable
        # (used to determine the avg conduction losses per pwm switching interval)
        for phase in ['a', 'b', 'c']:
            i_phase = data[f'i_{phase} (A)']
            D_x     = data[f'Duty_{phase} (0-1)'] # duty cycle
            D_comp  = 1 - D_x                     # complementary duty cycle

            # (adds columns to DataFrame)
            # switches conduction currents
            # top switch avg current (only if i_phase>0)
            data[f'I_cond_S{phase} (A)']    = D_x * np.maximum(i_phase, 0)     # bottom switch
            # bottom switch avg current (only if i_phase<0)
            data[f'I_cond_S\'{phase} (A)']  = D_comp * np.maximum(-i_phase, 0) # bottom switch

            # diodes conduction currents
            # top diode avg current (during free-wheel, only if i_phase<0)
            data[f'I_diode_D{phase} (A)']   = D_x * np.maximum(-i_phase, 0)    # top diode conducts during duty off of bottom switch
            # bottom diode avg current (curing free-wheel, only if i_phase>0)
            data[f'I_diode_D\'{phase} (A)'] = D_comp * np.maximum(i_phase, 0)  # bottom diode conducts during duty off of top switch
        return data

    # conductions losses: (cond_current x R) + Duty_cycle x switched_current x V(switched_current)


    def calculate_total_losses(self, data: pd.DataFrame, f_sw: float, Tj_igbt: float, Tj_diode: float) -> pd.DataFrame:
        """
        Calculates instantaneous P_total (P_cond + P_sw) for all 12 devices,
        using Tj_igbt, Tj_diode for temperature-dependent parameter adjustment.
        (all diodes are supposed to have same avg temperature - same for IGBTs)
        <Those temperatures are fed back after evaluation of thermal models>

        Parameters
        ----------
        data : pd.DataFrame
            (DataFrame) table containing the different signals of interest for the calculation
        f_sw : float
            switching frequency (needed for switching losses calculation)
        Tj_igbt : float
            estimation of igbt junction temperature (thermoelectrical model)
        Tj_diode : float
            estimation of diode junction temperature

        Returns
        -------
        data : pd.DataFrame
            dataframe with additional data (losses of different devices)

        """

        # Calculate P_total for each device
        P_module_total = np.zeros_like(data['time (s)'])

        for prefix, d_type, I_phase_col, is_top_switch in self.device_map:
            # for each device (prefix: its name / d_type: device type / associated phase current / top switch?)

            I_cond_col = f'I_cond_{prefix} (A)' if d_type == 'IGBT' else f'I_diode_{prefix} (A)'
            I_cond  = data[I_cond_col]    # conduction current column
            i_phase = data[I_phase_col]   # associated phase current column
            I_comm  = np.abs(i_phase)     # commutated current (the current that flows in a device is considered positive)

            # note: here the time resolution of signal is (for instance) 10 points per PWM interval
            # (The time resolution is given by the resolution of modulation signal in generate_waveforms)
            # A single point would be sufficient... (current could be considered constant over PWM period)
            # <might simulate a ZOH each switching interval>

            # --- CONDUCTION LOSS ---
            # avg value over pwm interval
            if d_type == 'IGBT':
                #Vce_sat = self.P.Vce_sat(I_comm, Tj_igbt)  # Vce_sat function of current & junction temperature
                Vce_sat = self.P.T_Vce_datasheet(I_comm, Tj_igbt)
                P_cond = Vce_sat * I_cond
            else:
                # diode
                #Vce_term = self.P.Vce_term(I_comm, Tj_diode)
                Vce_term = self.P.Vce_datasheet(I_comm, Tj_diode)
                P_cond = Vce_term * I_cond

            # --- SWITCHING LOSS ---
            if d_type == 'IGBT':
                E_on_scaled  = self.P.eon(Tj_igbt,  self.P.Rg, self.P.DC_BUS_V, I_comm)*1e-3  # IGBT turn on energy
                E_off_scaled = self.P.eoff(Tj_igbt, self.P.Rg, self.P.DC_BUS_V, I_comm)*1e-3  # IGBT turn off energy

                switching_condition = (i_phase > 0) if is_top_switch else (i_phase < 0)
                P_sw = np.where(switching_condition, (E_on_scaled + E_off_scaled) * f_sw, 0)

            else: # DIODE (Reverse Recovery Loss)
                E_rec_scaled = self.P.err(Tj_diode, self.P.Rg, self.P.DC_BUS_V, I_comm)*1e-3  # translation in J...

                recovery_condition = (i_phase < 0) if is_top_switch else (i_phase > 0)  # same a FW condition?
                P_sw = np.where(recovery_condition, E_rec_scaled * f_sw, 0)

            P_total = P_cond + P_sw # total losses of evaluated device
            data[f'P_total_{prefix} (W)'] = P_total

            # to ease debug:
            if prefix == 'Da' or prefix == 'Sa':
                data[f'P_cond_{prefix} (W)'] = P_cond
                data[f'P_sw_{prefix} (W)'] = P_sw

            P_module_total += P_total

        data['P_module_avg (W)'] = P_module_total.mean() # (same value written to all lines)
        # power dissipated in 3 legs composed of one HB each (i.e. losses in 3 x HB)

        return data










