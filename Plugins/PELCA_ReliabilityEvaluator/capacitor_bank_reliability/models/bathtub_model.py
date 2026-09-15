# -*- coding: utf-8 -*-
"""\brief Compute bathtub reliability metrics from early-life, random, and wear-out phases.

This module is part of the PELCA reliability evaluator.
"""
import numpy as np
import matplotlib.pyplot as plt
#from scipy.integrate import trapz #cumtrapz
# numpy.trapz - deprecated since NumPy 2.0 (2023-08-18). Use numpy.trapezoid or scipy.integrate functions instead.

class BathtubModel:
    """
    Compute & plot hazard, cdf, and reliability given parameters of three Weibull hazard functions
    representing early failure, useful life, and wear-out phases of a component.
    """
    def __init__(self, beta1, eta1, beta2, eta2, beta3, eta3, time_range=(0.01, 20), n_points=1000):
        """Initialize the object with the provided configuration."""
        self.beta1 = beta1  # Early-life
        self.eta1 = eta1
        self.beta2 = beta2  # Useful-life
        self.eta2 = eta2
        self.beta3 = beta3  # Wear-out
        self.eta3 = eta3
        self.t = np.linspace(time_range[0], time_range[1], n_points)

        self.compute_hazards()
        self.compute_cdf_and_reliability()


    def weibull_hazard(self, t, beta, eta):
        """Run weibull hazard."""
        return (beta / eta) * (t / eta)**(beta - 1)

    def compute_hazards(self):
        """Calculate hazards."""
        self.h1 = self.weibull_hazard(self.t, self.beta1, self.eta1)  # Early-life
        self.h2 = self.weibull_hazard(self.t, self.beta2, self.eta2)  # Useful-life
        self.h3 = self.weibull_hazard(self.t, self.beta3, self.eta3)  # Wear-out
        self.h_total = self.h1 + self.h2 + self.h3


    def compute_cdf_and_reliability(self):
        # calc cum. hazard functions
        #self.H1 = cumtrapz(self.h1, self.t, initial=0)
        # could be calculated analytically as well : (t/eta1)**beta1
       """Calculate cdf and reliability."""
       self.H1 = (self.t / self.eta1)**self.beta1

        #self.H2 = cumtrapz(self.h2, self.t, initial=0)
       self.H2 = (self.t / self.eta2)**self.beta2
       self.H3 = (self.t / self.eta3)**self.beta3

        #self.H_total = cumtrapz(self.h_total, self.t, initial=0)
       self.H_total = self.H1 + self.H2 + self.H3

        # calc CDFs
       self.F1 = 1 - np.exp(-self.H1)
       self.F2 = 1 - np.exp(-self.H2)
       self.F3 = 1 - np.exp(-self.H3)
       self.F_total = 1 - np.exp(-self.H_total)

        # calc reliabilities
       self.R1 = np.exp(-self.H1)
       self.R2 = np.exp(-self.H2)
       self.R3 = np.exp(-self.H3)
       self.R_total = np.exp(-self.H_total)

        # # survival functions (same as reliability...)
        # self.S1 = 1 - self.F1
        # self.S2 = 1 - self.F2
        # self.S_total = 1 - self.F_total

        # calf PDFs : f(t) = h(t)*R(t)
       self.f1 = self.h1 * self.R1
       self.f2 = self.h2 * self.R2
       self.f3 = self.h3 * self.R3
       self.f_total = self.h_total * self.R_total


    # def check_pdf_integrals(self):
    #     # Use trapezoidal rule to check area under each PDF
    #     area_f1 = trapz(self.f1, self.t)
    #     area_f2 = trapz(self.f2, self.t)
    #     area_f3 = trapz(self.f3, self.t)
    #     area_f_total = trapz(self.f_total, self.t)
    #     print(f"PDF area (early-life):     {area_f1:.6f}")
    #     print(f"PDF area (useful-life):    {area_f2:.6f}")
    #     print(f"PDF area (wear-out):       {area_f3:.6f}")
    #     print(f"PDF area (combined):       {area_f_total:.6f}")

    def check_pdf_integrals(self):
        # Use trapezoidal rule to check area under each PDF
        """Run check pdf integrals."""
        area_f1 = np.trapezoid(self.f1, self.t)
        area_f2 = np.trapezoid(self.f2, self.t)
        area_f3 = np.trapezoid(self.f3, self.t)
        area_f_total = np.trapezoid(self.f_total, self.t)

        print(f"PDF area (early-life):     {area_f1:.6f}")
        print(f"PDF area (useful-life):    {area_f2:.6f}")
        print(f"PDF area (wear-out):       {area_f3:.6f}")
        print(f"PDF area (combined):       {area_f_total:.6f}")

    def plot_pdfs(self, save=False):
        """Plot pdfs results."""
        plt.figure(figsize=(10, 6))
        plt.plot(self.t, self.f_total, label="Total PDF (Combined)", color='blue')
        plt.plot(self.t, self.f1, label="PDF from Early-life", linestyle='--', color='orange')
        plt.plot(self.t, self.f2, label="PDF from Useful-life", linestyle='--', color='green')
        plt.plot(self.t, self.f3, label="PDF from Wear-out", linestyle='--', color='red')
        plt.xlabel("Time (years)")
        plt.ylabel("Probability Density Function (PDF)")
        plt.title("PDFs: Early-life, Useful-life, Wear-out, and Combined")
        plt.grid(True)
        plt.legend()
        if save:
            plt.savefig("pdf_plot.png")
        plt.show()

    def plot_cdfs(self, save=False):
        """Plot cdfs results."""
        plt.figure(figsize=(10, 6))
        plt.plot(self.t, self.F_total, label="Total CDF (Combined)", color='blue')
        plt.plot(self.t, self.F1, label="CDF from Early-life", linestyle='--', color='orange')
        plt.plot(self.t, self.F2, label="CDF from Useful-life", linestyle='--', color='green')
        plt.plot(self.t, self.F3, label="CDF from Wear-out", linestyle='--', color='red')
        plt.xlabel("Time (years)")
        plt.ylabel("Cumulative Distribution Function (CDF)")
        plt.title("CDFs: Early-life, Useful-life, Wear-out, and Combined")
        plt.grid(True)
        plt.legend()
        if save:
            plt.savefig("cdf_plot.png")
        plt.show()

    def plot_reliability(self, save=False):
        """Plot reliability results."""
        plt.figure(figsize=(10, 6))
        plt.plot(self.t, self.R_total, label="Total Reliability", color='blue')
        plt.plot(self.t, self.R1, label="Reliability from Early-life", linestyle='--', color='orange')
        plt.plot(self.t, self.R2, label="Reliability from Useful-life", linestyle='--', color='green')
        plt.plot(self.t, self.R3, label="Reliability from Wear-out", linestyle='--', color='red')
        plt.xlabel("Time (years)")
        plt.ylabel("Reliability Function R(t)")
        plt.title("Reliability Functions")
        plt.grid(True)
        plt.legend()
        if save:
            plt.savefig("reliability_plot.png")
        plt.show()

    def plot_hazards(self, save=False):
        """Plot hazards results."""
        plt.figure(figsize=(10, 6))
        plt.plot(self.t, self.h_total, label="Total Hazard", color='blue')
        plt.plot(self.t, self.h1, label="Hazard from Early-life", linestyle='--', color='orange')
        plt.plot(self.t, self.h2, label="Hazard from Useful-life", linestyle='--', color='green')
        plt.plot(self.t, self.h3, label="Hazard from Wear-out", linestyle='--', color='red')
        plt.xlabel("Time (years)")
        plt.ylabel("Hazard Function h(t)")
        plt.title("Hazard Functions")
        plt.grid(True)
        plt.legend()
        if save:
            plt.savefig("hazard_plot.png")
        plt.show()

    def plot_all(self, save=False):
        """Plot all results."""
        self.plot_cdfs(save=save)
        self.plot_reliability(save=save)
        self.plot_hazards(save=save)
        self.plot_pdfs(save=save)

if __name__ == "__main__":
    # Example: Early failure (beta<1), Useful life (beta~1), Wear-out (beta>1)
    model = BathtubModel(
        beta1=0.5, eta1=1.5,     # Early-life
        beta2=1.0, eta2=15,      # Useful-life
        beta3=3.0, eta3=8        # Wear-out
    )
    model.plot_all(save=False)
    model.check_pdf_integrals()
