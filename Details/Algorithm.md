# Explanation of the algorithm

## Table of Contents
- [General](#general)
- [Manufacture: quantifying Impacts](#manufacture-quantifying-impacts)
- [Use: quantifying Impacts](#use-quantifying-impacts)
- [Fault model](#fault_model)
- [Diagnosis: replacement matrix (RM)](#Diagnosis-replacement-matrix-(RM))
- [Fault generation](#Fault-generation)
- [Replacement: quantifying Impacts](#Replacement-quantifying-Impacts)

## General
In order to make the method more accessible, the general algorithm is presented in Figure 2. The parts colored in blue are developed in detail later.

The concept of a Replacement Unit (RU) is used. It represents the maximum level of modularity of the system that can be replaced; for example, a replacement unit can be an integrated module or a discrete component. When a UR is replaced, its age resets to zero. Consider the following example, Figure 2: In case (a), an inverter has 6 Replacement Units (RUs), allowing it to replace specific power chips individually. In contrast, case (b) consists of a single Replacement Unit, meaning that if a fault occurs, the entire system must be replaced.
<div align="center">
    <img src="../Images/RU.png" width="400"/>
    <p>Fig 1. Product life modelling with replacement and diagnostic.
</div> 

First, a list of faults is established (d), along with the failure parameters (σ and β) for each replacement unit (RUi), as well as the replacement matrix [RM]. Then, at t = 0, the environmental impacts of the entire system at the manufacturing stage are calculated. Next, for each RUi, the time of occurrence and type of fault are generated randomly. This results in a lifetime vector [t*] and a fault type vector [d*] containing the information for each RUi.

In the time loop, if at a given moment ti equals t, this means a fault appears. At t = t, a list of all faulty RUi, RU*, is established. Then, depending on the fault, RUi, and diagnostics, a replacement scenario is defined for the URs that will be replaced at t = t*, forming the vector RV*.

This allows the calculation of the environmental impacts at the replacement of the faulty RUi. Next, the impacts during use over the period are calculated. Finally, the time advances to t + 1. This loop is repeated until the end of the chosen usage period, with a Monte Carlo sub-loop until the final number of iterations is reached.

<div align="center">
    <img src="../Images/Algorithm.png" width="400"/>
    <p>Fig 2. Product life modelling with replacement and diagnostic.
</div>

## Manufacture: quantifying Impacts

##  Use: quantifying Impacts

## Fault model

##  Diagnosis: replacement matrix (RM)

##  Fault generation

##  Replacement: quantifying Impacts


