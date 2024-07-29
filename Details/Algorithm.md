# Explanation of the algorithm

## General
In order to make the method more accessible, the general algorithm is presented in Figure 1. The parts colored in blue are developed in detail later.

First, a list of faults is established (d), along with the failure parameters (σ and β) for each replacement unit (RUi), as well as the replacement matrix [RM]. Then, at t = 0, the environmental impacts of the entire system at the manufacturing stage are calculated. Next, for each RUi, the time of occurrence and type of fault are generated randomly. This results in a lifetime vector [t*] and a fault type vector [d*] containing the information for each RUi.

In the time loop, if at a given moment ti equals t, this means a fault appears. At t = t, a list of all faulty RUi, RU*, is established. Then, depending on the fault, RUi, and diagnostics, a replacement scenario is defined for the URs that will be replaced at t = t*, forming the vector RV*.

This allows the calculation of the environmental impacts at the replacement of the faulty RUi. Next, the impacts during use over the period are calculated. Finally, the time advances to t + 1. This loop is repeated until the end of the chosen usage period, with a Monte Carlo sub-loop until the final number of iterations is reached.

<div align="center">
    <img src="../Images/Algorithm.png" alt="Staircase Curve" width="600"/>
    <p>Fig 1. Product life modelling with replacement and diagnostic.
</div> 

