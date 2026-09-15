# -*- coding: utf-8 -*-
"""\brief Provide interpolation helpers used by reliability calculations.

This module is part of the PELCA reliability evaluator.
"""

import numpy as np

def interpolate_quadratic(points):
    # Extract t and coef values
    """Run interpolate quadratic."""
    t_values = np.array([p[0] for p in points])
    coef_values = np.array([p[1] for p in points])

    # Construct the system of equations
    A = np.vstack([t_values**2, t_values, np.ones_like(t_values)]).T

    # Solve for a, b, c
    a, b, c = np.linalg.solve(A, coef_values)

    return a, b, c

# if matrix not square
def interpolate_quadratic2(points):
    """Run interpolate quadratic2."""
    t_values = np.array([p[0] for p in points])
    coef_values = np.array([p[1] for p in points])

    # Construct matrix A
    A = np.vstack([t_values**2, t_values, np.ones_like(t_values)]).T

    # Solve by least-squares regression.
    # Use numpy.linalg.lstsq to obtain the best solution for an overdetermined system.
    a, b, c = np.linalg.lstsq(A, coef_values, rcond=None)[0]

    return a, b, c


# return the interpolated value of FIT rate
def interp_fit(T, FIT40, FIT85):
    """Run interp fit."""
    T40=273+40 # in Kelvin
    T85=273+85
    # below 40degC does the FIT rate reduces? maybe but no info... would better clamp to FIT40 value
    if T<40:
            return FIT40
    else:
        Ea_div_k = -np.log(FIT40/FIT85)/((1/T40)-(1/T85))
        interpolated_fit =  FIT85*(np.exp(-Ea_div_k*(1/(T+273)-1/(85+273))))
    return interpolated_fit


class LinearInterpolation:
    """Represent linear interpolation behavior used by reliability calculations."""
    def __init__(self, data_points):
        """
        Initialize the class with data points.

        :param data_points: List of data points provided as NumPy arrays or Python lists.
        """
        self.data_points = np.array(data_points)
        self.t_values = self.data_points[:, 0]  # Extraction des valeurs de t
        self.coef_values = self.data_points[:, 1]  # Extraction des valeurs de coef

    def interpolate(self, x_new):
        """
        Perform linear interpolation on the provided values.

        :param x_new: Array of new x values for interpolation.
        :return: Array of interpolated values corresponding to x_new.
        """
        return np.interp(x_new, self.t_values, self.coef_values)

    def plot_interpolation(self):
        """
        Plot the data points and the linear interpolation curve.
        """
        import matplotlib.pyplot as plt

        # Generate interpolation values across a t range.
        x_new = np.linspace(self.t_values.min(), self.t_values.max(), 500)
        y_new = self.interpolate(x_new)

        # Create the plot.
        plt.figure(figsize=(8, 6))

        # Plot the data points.
        plt.scatter(self.t_values, self.coef_values, color='red', label='Data Points')

        # Plot the linear interpolation curve.
        plt.plot(x_new, y_new, label='Linear interpolation', color='blue')

        # Ajouter des labels et un titre
        plt.xlabel('t')
        plt.ylabel('Coefficient')
        plt.title('Linear interpolation of data')
        plt.legend()

        # Affichage du graphique
        plt.grid(True)
        plt.show()
