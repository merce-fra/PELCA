# -*- coding: utf-8 -*-
"""\brief Compute converter operating points from speed and torque conditions.

This module is part of the PELCA reliability evaluator.
"""


import math
def calc_Iout(Pout, Vout_rms, PF, Vdc):
    """
    Parameters
    ----------
    Pout : float
        active output power
    Vout_rms : float
        line to neutral output voltage (rms)
    PF : float
        power factor (cos phy) (0 .. 1)
    Vdc : float
        DC bus voltage

    Returns
    -------
    Iout_rms : float
        rms output phase current
    """
    Vout_line_to_line = Vout_rms * math.sqrt(3)
    Iout_rms = Pout / (Vout_line_to_line*math.sqrt(3)*PF)
    return Iout_rms
# test:
# calc_Iout(200000,230,0.8,540)
# => 362.3188405797101


# to put in converter class
from inverter_reliability.igbt_reliability.converter.converter import Converter
converter_gpi = Converter(
    name="REFERENCE_CONVERTER",
    power_range=(245, 1209),
    # might be defined in Excel sheet
    torque_points_output={25: 0.39, 50: 0.56, 75: 0.77, 100: 1.0}, # torque_points_output: dict {percentage: value} for Iout/Ir_out
    torque_points_displacement={25: 0.57, 50: 0.78, 75: 0.85, 100: 0.87} # torque_points_displacement: dict {percentage: value} for cos_phi
)

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# not valid at very low freq... (rel_speed>0!)
# nor at very low torque:
# returns 0 also if torque < 0.25
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# def calc_active_power(rel_torque, rel_speed):
#     cos_phy = converter_gpi.get_displacement_factor(rel_torque*100)
#     rel_output_current = converter_gpi.get_rel_output_current(rel_torque*100)
#     m = rel_speed # because V/f = constant
#     rms_out_voltage = 230 * m   # under assumption that with m=1, output voltage (phase to "neutral") = 230V rms  (max possible <=> 400V input)
#     # pb: at 0 Hz, m=0 ... rms_out_voltage=0...
#     rms_out_current = 363 * rel_output_current # params['Ir_out'] = 363
#     active_Pout = 3 * rms_out_voltage * rms_out_current * cos_phy
#     return active_Pout


def _calc_active_power_scalar(rel_torque: float, rel_speed: float) -> float:
    """
    Original scalar computation (unchanged except for float casts).
    """
    cos_phy = converter_gpi.get_displacement_factor(rel_torque * 100.0)
    rel_output_current = converter_gpi.get_rel_output_current(rel_torque * 100.0)

    m = rel_speed  # V/f = constant => modulation index equals relative speed
    rms_out_voltage = 230.0 * m  # phase-to-neutral RMS at m=1 equals 230V
    rms_out_current = 363.0 * rel_output_current  # base Ir_out = 363 A
    active_Pout = 3.0 * rms_out_voltage * rms_out_current * cos_phy
    return active_Pout

def calc_active_power(rel_torque, rel_speed):
    """
    Vector-friendly wrapper around the scalar function.

    Accepts scalar or array-like inputs for rel_torque and rel_speed.
    If both are scalars, returns a scalar float.
    Otherwise, returns a numpy.ndarray with broadcasted shape.

    Parameters
    ----------
    rel_torque : float | array-like
        Relative torque (per unit).
    rel_speed : float | array-like
        Relative speed (per unit).

    Returns
    -------
    float | np.ndarray
        Active power at each operating point.
    """
    # Convert inputs to arrays for broadcasting
    rt = np.asarray(rel_torque, dtype=float)
    rs = np.asarray(rel_speed, dtype=float)

    # Broadcast to common shape
    try:
        rt_b, rs_b = np.broadcast_arrays(rt, rs)
    except ValueError as e:
        raise ValueError(f"rel_torque and rel_speed are not broadcastable: {e}")

    # Prepare output array
    out = np.empty(rt_b.shape, dtype=float)

    # Iterate over flat indices, call scalar function because converter_gpi expects scalars
    it = np.nditer([rt_b, rs_b, out], op_flags=[['readonly'], ['readonly'], ['writeonly']])
    for rt_i, rs_i, out_i in it:
        out_i[...] = _calc_active_power_scalar(float(rt_i), float(rs_i))

    # Return scalar if inputs were scalars
    if out.ndim == 0:
        return float(out)  # pure Python float
    return out


def calc_PF(Rel_torque):
    """Calculate p f."""
    return converter_gpi.get_displacement_factor(max(Rel_torque,0.25)*100)


import numpy as np
import matplotlib.pyplot as plt
def test_calc_active_power():

    """Run test calc active power."""
    active_power_0_25_speed = []
    active_power_0_50_speed = []
    active_power_0_75_speed = []
    active_power_full_speed = []
    rel_torque =[min(1, i) for i in np.arange(0.25,1.1,0.1)]
    for rel_torque_i in rel_torque:
        active_power_0_25_speed.append(calc_active_power(min(rel_torque_i,1),0.25))
        active_power_0_50_speed.append(calc_active_power(min(rel_torque_i,1),0.50))
        active_power_0_75_speed.append(calc_active_power(min(rel_torque_i,1),0.75))
        active_power_full_speed.append(calc_active_power(min(rel_torque_i,1),1))

    fig, ax1 = plt.subplots(1, 1, figsize=(12, 8), sharex=True)
    # Plot currents.
    ax1.plot(rel_torque, active_power_0_25_speed, label='speed=25%', color='r')
    ax1.plot(rel_torque, active_power_0_50_speed, label='speed=50%', color='g')
    ax1.plot(rel_torque, active_power_0_75_speed, label='speed=75%', color='b')
    ax1.plot(rel_torque, active_power_full_speed, label='speed=100%', color='black')
    ax1.set_ylabel('active power (W)')
    ax1.legend(loc='upper right')
    ax1.grid(True)
    ax1.set_xlabel('relative torque')

    plt.suptitle('active power vs rel torque at different speed')
    plt.tight_layout()
    plt.show()

def calc_op_point(Udc, Rel_speed_i, Rel_torque_i):

    """Calculate op point."""
    if Rel_speed_i < 0.01:
        Rel_speed_i = 0.01

    active_Pout = calc_active_power(Rel_torque_i, Rel_speed_i)
    # PF & m can be derived from rel_torque and speed
    m = min(Rel_speed_i,
            1)  # >0 .. 1 : modulation index, identical to the relative CDM output freq up to rated output freq
    PF = calc_PF(Rel_torque_i)  # output voltage power factor
    Vout_rms = 230 * m  # inverter phase to "neutral" output voltage   # output voltage rms for Mi ~ 0.7 >
    Iout = calc_Iout(active_Pout, Vout_rms, PF,
                     Udc)  # output phase current (rms value) shared by power modules connected n //

    return active_Pout, Iout, PF, Vout_rms


def calc_op_points(Udc, Rel_speed_i, Rel_torque_i):
    """
    Vectorized operating point calculation.

    Parameters
    ----------
    Udc : float
        DC link voltage (scalar only).
    Rel_speed_i : float or np.ndarray
        Relative speed (0..1), scalar or array-like. A minimum clamp of 0.01 is applied elementwise.
    Rel_torque_i : float or np.ndarray
        Relative torque, scalar or array-like.

    Returns
    -------
    active_Pout : np.ndarray or float
        Active output power, same shape as inputs (after broadcasting).
    Iout : np.ndarray or float
        Output phase current (RMS), same shape as inputs.
    PF : np.ndarray or float
        Power factor, same shape as inputs.
    Vout_rms : np.ndarray or float
        Output phase-to-neutral RMS voltage, same shape as inputs.
    """

    # Ensure array-like and broadcastable shapes
    Rel_speed_i = np.asarray(Rel_speed_i)
    Rel_torque_i = np.asarray(Rel_torque_i)

    # Broadcast to a common shape (this will raise a helpful error if shapes are incompatible)
    Rel_speed_i, Rel_torque_i = np.broadcast_arrays(Rel_speed_i, Rel_torque_i)

    # Apply elementwise minimum clamp: if Rel_speed_i < 0.01 => 0.01
    Rel_speed_i = np.maximum(Rel_speed_i, 0.01)

    # Modulation index m = min(Rel_speed_i, 1) elementwise
    m = np.minimum(Rel_speed_i, 1.0)

    # Output voltage PF from torque
    # Wrap scalar-only helper functions to support vector inputs
    v_calc_active_power = np.vectorize(calc_active_power, otypes=[float])
    v_calc_PF = np.vectorize(calc_PF, otypes=[float])
    v_calc_Iout = np.vectorize(calc_Iout, otypes=[float])

    PF = v_calc_PF(Rel_torque_i)

    # Vout_rms = 230 * m (elementwise)
    Vout_rms = 230.0 * m

    # Active power from torque & speed
    active_Pout = v_calc_active_power(Rel_torque_i, Rel_speed_i)

    # Output current (elementwise), Udc is scalar
    Iout = v_calc_Iout(active_Pout, Vout_rms, PF, Udc)

    # If the original inputs were scalars, return scalars for convenience
    def maybe_squeeze(x):
        # squeeze only if both inputs were scalars
        """Run maybe squeeze."""
        return x.item() if x.shape == () else x

    return (
        maybe_squeeze(active_Pout),
        maybe_squeeze(Iout),
        maybe_squeeze(PF),
        maybe_squeeze(Vout_rms),
    )
