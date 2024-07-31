# Explanation of the algorithm

## Table of Contents
- [General](#general)
- [Manufacture & Use: quantifying Impacts](#manufacture-and-use-quantifying-impacts)
- [Fault model](#fault-model)
- [Diagnosis: replacement matrix (RM)](#Diagnosis-replacement-matrix-RM)
- [Fault generation](#Fault-generation)
- [Replacement: quantifying Impacts](#Replacement-quantifying-Impacts)

## General
In order to make the method more accessible, the general algorithm is presented in Figure 2. The parts colored in blue are developed in detail later.

The concept of a Replacement Unit (RU) is used. It represents the maximum level of modularity of the system that can be replaced; for example, a replacement unit can be an integrated module or a discrete component. When a UR is replaced, its age resets to zero. Consider the following example, Figure 2: In case (a), an inverter has 6 Replacement Units (RUs), allowing it to replace specific power chips individually. In contrast, case (b) consists of a single Replacement Unit, meaning that if a fault occurs, the entire system must be replaced.
<div align="center">
    <img src="../Images/RU.png" width="400"/>
    <p>Fig 1. Example of Replacement Unit (RU) representation.
</div> 

First, a list of faults is established (d), along with the failure parameters (σ and β) for each replacement unit (RUi), as well as the replacement matrix [RM]. Then, at t = 0, the environmental impacts of the entire system at the manufacturing stage are calculated. Next, for each RUi, the time of occurrence and type of fault are generated randomly. This results in a lifetime vector [t*] and a fault type vector [d*] containing the information for each RUi.

In the time loop, if at a given moment ti equals t, this means a fault appears. At t = t, a list of all faulty RUi, RU*, is established. Then, depending on the fault, RUi, and diagnostics, a replacement scenario is defined for the URs that will be replaced at t = t*, forming the vector RV*.

This allows the calculation of the environmental impacts at the replacement of the faulty RUi. Next, the impacts during use over the period are calculated. Finally, the time advances to t + 1. This loop is repeated until the end of the chosen usage period, with a Monte Carlo sub-loop until the final number of iterations is reached.

<div align="center">
    <img src="../Images/Algorithm.png" width="400"/>
    <p>Fig 2. Product life modelling with replacement and diagnostic.
</div>

## Manufacture & Use: quantifying Impacts
To quantify the impacts related to both manufacturing and use, an inventory for both aspects must be provided. As outlined in the README.md, the tool has been developed using the Python library Brightway2. Therefore, the input Excel file must follow a specific template for the inventory sections (sheets "Inventory - Manufacturing" and "Inventory - Use"). This template is the Brightway template; for more details, please refer to the specific library documentation.

For each inventory sheet, you need to create as many activities as there are unit processes (RUs). For instance, in the "Inventory - Manufacturing" sheet, the first activity represents the manufacturing of RU1, contructed with the "exchanges" flows. In the "Inventory - Use" sheet, each activity corresponds to the energy consumption of each RU during 1 hour of operation.

The tool, using the Brightway library, then enables the environmental impact quantification based on the selected impacts in the "LCIA" sheet.


## Fault model
Il a été remarqué que la dynamique du taux de défaillance dans le domaine de l'électronique suit une tendance illustrée par ce que l'on nomme communément la "courbe en baignoire", figure 3. Cette courbe caractérise les différentes phases de défaillance au cours de la DDV d'un dispositif, englobant ainsi la phase "jeunesse" (liée à des problèmes de conception ou de fabrication insuffisamment maîtrisés), la période de fonctionnement "vie utile" (où les défaillances surviennent de manière aléatoire) ainsi que le stade du "vieillissement" (résultant de l'usure).
<div align="center">
    <img src="../Images/bathcurve.png" width="400"/>
    <p>Fig 3. Bathtub curve.
</div>
Pour évaluer la fiabilité des composants, des lois statistiques sont couramment utilisées. La fonction de Weibull est celle sélectionnée dans l'outil, car elle permet de reproduire la "courbe en baignoire". Elle est définie par deux paramètres σ and β le paramètre de forme. Le paramètre β est lié à une période de la vie du composant. C’est-à-dire, les défaillances liées à la jeunesse ont un paramètre β<1, les défaillances aléatoires β=1, et les défaillances fin de vie β>1. L’addition des trois fonctions de Weibull correspondant aux défauts jeunesse, de vie utile et de fin de vie permet de recréer la courbe en baignoire comme illustrée dans la figure 4
<div align="center">
    <img src="../Images/ERW.png" width="400"/>
    <p>Fig 4. Modélisation de la courbe en baignoire à partir de trois fonctions défaut..
</div>
Chaque RU a donc 3 fonctions de défaut, les paramètres à sélectionnés sont dans la feuille "Faults".
    
##  Diagnosis: replacement matrix (RM)
The tool allows models the diagnosis associated with the system, specifically detailing the replacement scenarios when a fault occurs. This includes identifying what components are replaced within the system, To achieve this, this sheet constructs the Replacement Matrix (RM). The numbers in the matrix represent the average proportion of each component replaced when a fault occurs in a specific RU, with values ranging from 0 to 1. Row indices represent faults in a specific RU (e.g., Fault RU1), while column indices represent the RUs to be replaced (e.g., RU1).
To clarify, consider an example with 2 RUs, resulting in a 2x2 matrix. In this example, if the value in the first row, first column (Fault RU1 ; RU1) is 1, and the value in the first row, second column (Fault RU1 ; RU2) is 0.6, this means that when a fault occurs in RU1, 100% of RU1 and 60% of RU2 are replaced according to the diagnosis.

##  Fault generation

Dans cette section, nous allons détailler comment nous déterminons à la fois le moment d'apparition des défauts et le type de défaut pour chaque $RU$ avec les défauts du vecteur $(d)$.
La figure \ref{algodiag} illustre l'algorithme de détermination du type de défaut, cela se fait en deux étapes principales, la génération d'un défaut et la sélection du type de défaut. La génération du défaut reprend les mêmes principes qu'au chapitre \ref{ch3}, figure \ref{genedef7}.\par

<div align="center">
    <img src="../Images/algo_fault.png" width="400"/>
    <p>Fig 5.  Algorithme de génération des défauts et de sélection du type de défaut.
</div>
Dans un premier temps, il faut trouver la fonction de répartition globale de l'UR.  Il est nécessaire d'associer les défauts au sein d'une unité de remplacement. Les défauts peuvent être associés comme au chapitre \ref{ch3}, c'est-à-dire association série ; tous les sous-systèmes doivent fonctionner pour que le système global soit opérationnel. L'équation \ref{eq_serie_def} donne la fonction de répartition d'une UR.\par
\begin{equation}
	F_{i}(t) =1-\prod_{k=1}^{\textrm{n}}(1-f_{k\textrm{, }i}(t))
	\label{eq_serie_def}
\end{equation}
Avec $f_{k\textrm{, }i}$ la fonction de répartition du défaut $k$ de l'UR $i$ et $n$ le nombre de défauts total pour l'UR.\par
Une fois la fonction de répartition établie, elle est comparée à un nombre aléatoire compris entre 0 et 1, généré selon une distribution uniforme. Cela permet de déterminer le temps du défaut ($t_i^*$) de l'$UR_i$, si ce nombre est inférieur à la fonction de répartition, cela indique le temps du défaut $t_i^*$.\par
Ensuite, un second nombre aléatoire est employé pour sélectionner le type de défaut ($d_{k,i}^*=d_{j}^*$), en fonction des probabilités associées à chaque défaut à l'instant $t_i^*$ où a lieu le défaut.\par
Cet algorithme permet pour chaque UR, à la fois de déterminer le temps pour lequel un défaut a lieu ($t^*_i$) mais aussi, quel est le type de défaut ($d^*_i$). Cela permet de générer deux vecteurs $t^*$ et $d^*$ de taille $m$ représentant respectivement les temps d'apparition d'un et le type de défaut pour chaque UR.
##  Replacement: quantifying Impacts


