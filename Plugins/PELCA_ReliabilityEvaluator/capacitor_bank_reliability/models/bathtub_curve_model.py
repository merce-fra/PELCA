# -*- coding: utf-8 -*-
"""\brief Build and plot bathtub reliability curves from Weibull failure phases.

This module is part of the PELCA reliability evaluator.
"""
# ===============================================
# to draw bathtub(s) from weibull distributions
# including uncertainties
# ===============================================
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import weibull_min

class BathtubCurveModel:
    """Represent bathtub curve model behavior used by reliability calculations."""
    def __init__(self,
                 infant_shape=0.6, infant_scale=3424,
                 normal_rate=0.001,
                 wearout_shape=4, wearout_scale=15):
        """Initialize the object with the provided configuration."""
        self.infant_shape = infant_shape
        self.infant_scale = infant_scale
        self.normal_rate = normal_rate
        self.wearout_shape = wearout_shape
        self.wearout_scale = wearout_scale

    # Weibull hazard function
    #                              beta   eta
    def weibull_failure_rate(self, shape, scale, t):
        #pdf = weibull_min.pdf(t, shape, scale=scale)
        #cdf = weibull_min.cdf(t, shape, scale=scale)
        # return pdf / np.clip(1 - cdf, 1e-10, None)

        # calculated directly by using the analytical formula result
        """Run weibull failure rate."""
        return (shape/scale)*(t/scale)**(shape-1)


    # determine the bathtub function
    def compute_curve(self, t):

        # Infant mortality phase (infant_shape<1)
        """Calculate curve."""
        lambda1 = self.weibull_failure_rate(self.infant_shape, self.infant_scale, t)
        cdf1 = weibull_min.cdf(t, self.infant_shape, scale=self.infant_scale)

        # Normal life phase (exponential law - constant failure rate)
        lambda2 = self.normal_rate * np.ones_like(t) # constant failure rate
        cdf2 = self.normal_rate * t # linear increase with time

        # Wear-out phase (wearout_shape>1)
        lambda3 = self.weibull_failure_rate(self.wearout_shape, self.wearout_scale, t)
        cdf3 = weibull_min.cdf(t, self.wearout_shape, scale=self.wearout_scale)

        # Total failure rate
        failure_rate = lambda1 + lambda2 + lambda3

        # Inclusion-exclusion principle for CDF
        cdf_total =    (cdf1 + cdf2 + cdf3
                     - (cdf1 * cdf2 + cdf2 * cdf3 + cdf1 * cdf3)
                     + (cdf1 * cdf2 * cdf3))

        t_limited = t[cdf_total < 0.999]
        return failure_rate, cdf_total, t_limited


    def plot_curve(self, RU_name, t, comment):
        """Plot curve results."""
        failure_rate, cdf_total, t_limited = self.compute_curve(t)

        plt.figure(figsize=(12, 5))

        plt.subplot(1, 2, 1)
        plt.plot(t_limited, failure_rate[:len(t_limited)], label='Failure Rate', color='b')
        plt.xlabel('Time')
        plt.ylabel('Failure Rate')
        plt.title(RU_name + ' - Bathtub Curve - '+ comment)
        plt.grid()
        plt.legend()

        plt.subplot(1, 2, 2)
        plt.plot(t_limited, cdf_total[:len(t_limited)], label='Total CDF', color='r')
        plt.plot(t_limited, weibull_min.cdf(t_limited, self.infant_shape, scale=self.infant_scale),
                 '--', label='CDF: Infant Mortality', alpha=0.6)
        plt.plot(t_limited, self.normal_rate * t_limited, '--', label='CDF: Normal Life', alpha=0.6)
        plt.plot(t_limited, weibull_min.cdf(t_limited, self.wearout_shape, scale=self.wearout_scale),
                 '--', label='CDF: Wear-Out', alpha=0.6)
        plt.xlabel('Time')
        plt.ylabel('Cumulative Probability')
        plt.title('Cumulative Distribution Function (CDF)')
        plt.grid()
        plt.legend()

        plt.tight_layout()
        plt.show()


    def plot_with_uncertainty(self, t, comment, confidence=0.95):
        # Compute the failure rate curve and limited time range
        """Plot with uncertainty results."""
        failure_rate, _, t_limited = self.compute_curve(t)

        # Calculate the lower and upper bounds for the Weibull distribution "percent point function" (inverse of CDF)
        # These bounds represent the confidence interval for the failure rate
        lower_bound = weibull_min.ppf((1 - confidence) / 2, self.wearout_shape, scale=self.wearout_scale)
        upper_bound = weibull_min.ppf(1 - (1 - confidence) / 2, self.wearout_shape, scale=self.wearout_scale)

        # note:              shape scale
        # weibull_min.cdf(x,    c, scale) : gives the probability that a random variable is less than or equal to x
        # weibull_min.ppf(prob, c, scale) : gives the value of x such that the cumulative probability is prob
        # for confidence=0.95:
        #   lower bound lower_bound is the value below which 2.5% of data fall
        #    upper_bound is the value below which 97.5% of data fall
        # => define the range within which the true failure rate is expected to lie with 95% confidence.

        # Scale the failure rate to create the lower and upper confidence bounds
        failure_rate_lower = failure_rate * lower_bound / self.wearout_scale
        failure_rate_upper = failure_rate * upper_bound / self.wearout_scale

        # Create the plot
        plt.figure(figsize=(8, 5))

        # Plot the main failure rate curve
        plt.plot(t_limited, failure_rate[:len(t_limited)], label='Failure Rate', color='b')

        # Fill the area between lower and upper bounds to show the confidence interval
        plt.fill_between(
            t_limited,
            failure_rate_lower[:len(t_limited)],
            failure_rate_upper[:len(t_limited)],
            color='b',
            alpha=0.2,
            label=f'{confidence * 100:.0f}% Confidence Interval'
        )

        # Label the axes
        plt.xlabel('Time')
        plt.ylabel('Failure Rate')

        # Add a title with a custom comment
        plt.title('Bathtub Curve with Confidence Interval - ' + comment)

        # Display grid, legend, and the plot itself
        plt.grid()
        plt.legend()
        plt.show()


if __name__ == "__main__":
    # Define time axis
    t = np.linspace(1, 200, 1000)

    # Instantiate model with default parameters
    model = BathtubCurveModel()

    # Plot failure rate and CDF
    model.plot_curve("Check BathtubCurveModel", t, 'example')

    # Plot failure rate with confidence interval
    model.plot_with_uncertainty(t, "example", confidence=0.60)


# can be executed as:
#python bathtub_model.py
