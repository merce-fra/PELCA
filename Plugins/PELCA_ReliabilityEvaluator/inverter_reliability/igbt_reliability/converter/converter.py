# -*- coding: utf-8 -*-
"""\brief Represent converter operating characteristics used by reliability models.

This module is part of the PELCA reliability evaluator.
"""


import numpy as np

class Converter:
    """Represent converter behavior used by reliability calculations."""
    def __init__(self, name, power_range, torque_points_output, torque_points_displacement):
        """
        Initializes a converter with its characteristics.

        :param name: Converter name (str)
        :param power_range: Tuple (min_kVA, max_kVA)
        :param torque_points_output: dict {percentage: value} for Iout/Ir_out
        :param torque_points_displacement: dict {percentage: value} for cos_phi
        """
        self.name = name
        self.power_range = power_range
        self.torque_points_output = torque_points_output
        self.torque_points_displacement = torque_points_displacement

    # rel_output_current = get_rel_output_current(rel_torque_current)
    # error if rel_torque_current>100% or rel_torque_current<0%
    def get_rel_output_current(self, rel_torque_current):
        """
        Returns the relative output current as a function of the relative torque.
        <=> output phase current (rms) = 363 x rel_output_current
        """
        if rel_torque_current < 0 or rel_torque_current > 100:
            raise ValueError("rel_torque_current must be between 0 and 100%.")

        x = np.array(sorted(self.torque_points_output.keys()))
        y = np.array([self.torque_points_output[k] for k in x])

        if rel_torque_current < x[0]:
            return 0.0

        return float(np.interp(rel_torque_current, x, y))

    # cos_phy = get_displacement_factor(rel_torque_current)
    # error if rel_torque_current>100% or rel_torque_current<0%
    def get_displacement_factor(self, rel_torque_current):
        """
        Returns the displacement factor (cos phi) as a function of the relative torque.
        """
        if rel_torque_current < 0 or rel_torque_current > 100:
            raise ValueError("rel_torque_current must be between 0 and 100%.")

        x = np.array(sorted(self.torque_points_displacement.keys()))
        y = np.array([self.torque_points_displacement[k] for k in x])

        if rel_torque_current < x[0]:
            return 0.0

        return float(np.interp(rel_torque_current, x, y))


    # def calc_active_power(self, rel_torque, rel_speed):
    #     cos_phy = self.get_displacement_factor(rel_torque*100)
    #     rel_output_current = self.get_rel_output_current(rel_torque*100)
    #     m = rel_speed
    #     rms_out_voltage = 230 * m   # under assumption that with m=1, output voltage (phase to "neutral") = 230V rms
    #     rms_out_current = 360 * rel_output_current
    #     active_Pout = 3 * rms_out_voltage * rms_out_current * cos_phy
    #     return active_Pout

# test
if __name__ == "__main__":

    # usage example
    # relative output current (Iout/Ir_out) as function of relative torque current
    # for 200KW GPI (reference converter) 245 kVA-1209 kVA (200kW-1000kW)
    # power_range_low (kVA) 245
    # power_range_high (kVA) 1209
    # torque_current_25%  0.39
    # Torque_current_50%  0.56
    # Torque_current_75%  0.77
    # Torque_current_100% 1

    # cos_phy (load displacement factor) as function of relative torque current
    # for 200KW GPI (reference converter) 245 kVA-1209 kVA (200kW-1000kW)
    # power_range_low (kVA) 245
    # power_range_high (kVA) 1209
    # torque_current_25%  0.39
    # Torque_current_50%  0.56
    # Torque_current_75%  0.77
    # Torque_current_100% 1

    converter_gpi = Converter(
        name="REFERENCE_CONVERTER",
        power_range=(245, 1209),
        torque_points_output={25: 0.39, 50: 0.56, 75: 0.77, 100: 1.0},
        torque_points_displacement={25: 0.57, 50: 0.78, 75: 0.85, 100: 0.87}
    )

    print("rel_output_current (at rel_torque_current=50%):", converter_gpi.get_rel_output_current(50))  # 0.56
    print("output displacement factor (at rel_torque_current=75%):", converter_gpi.get_displacement_factor(75)) # 0.85
