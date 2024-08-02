<p align="center">
    <img src="Images/first_image.png?raw=true" alt="Staircase Curve" width="600"/>
</p>
PELCA (Power Electronics Life Cycle Assessment) is an open-source project aimed at assessing the environmental impact over the life cycle of modular and diagnosable power electronics systems. The integration of modularity and diagnosability aligns with circular economy principles, promoting practices such as repair and reuse. This project provides a tool to calculate the environmental impacts associated with the manufacturing, usage, and replacement of power electronics products.

This work began as part of the PhD thesis:
Baudais, Briac. *Eco-design in power electronics. Impacts of sizing,
modularity, and diagnosticability*. Electronique. Université Paris-Saclay, 2024. Français. ⟨NNT : 2024UPAST092⟩. ⟨tel-04659788⟩.
[Consult the thesis](https://theses.hal.science/tel-04659788)

The evolution of environmental impacts over time can be illustrated with a staircase curve:
<p align="center">
    <img src="Images/staircase_black.png?raw=true" alt="Staircase Curve" width="600"/>
</p>
<p align="center">
    Fig 1. Staircase curve.
 </p> 
Initially, the curve shows the environmental impacts associated with the manufacturing of the product. The slope of the curve represents the impacts during usage, specifically the operational losses incurred. When a failure occurs, the impacts rise, reflecting the need to replace the faulty component. This increase is influenced by the accuracy of diagnostics and the system's architecture (modularity). More precise and selective diagnostics allow for more targeted replacements, assuming the modularity supports it. In contrast, an integrated architecture does not facilitate the separation of the faulty component from the rest of the system.
The impact of diagnostics and modularity can be explained by the Replacement Rate (RR). An RR of 100% indicates a low-precision diagnosis, which provides no specific information when a fault occurs, leading to the replacement of the entire system or also no modularity. Conversely, an RR of 10% represents a more precise and selective diagnosis, where only 10% of the system is replaced. Thus, RR is directly related to the type of diagnostics and modularity.

L'outil a été développé à l'aide de la bibliothèque Brightway2 en python.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Contribution](#contribution)
- [License](#license)

## Installation

Comment l'utiliser 1ère installation :
1) Installer miniconda (permet la gestion des environnements en programmation): Miniconda — Anaconda documentation
2) Ouvrir miniconda, vous êtes dans l'environnement "base", créer un environnement virtuel, voici la ligne de code : `conda create -n nomenvironnement`
3) Activer l'environnement : `conda activate nomenvironnement`

Pour utiliser le projet certaine bibliothèques pythons sont nécéssaire dans votre environnement python. voici les lignes de code a mettre dans miniconda :
4) `conda install conda-forge::brightway2` (bibliothèse pour la partie ACV)
5) `conda install conda-forge::spyder` 
6) `conda install bioconda::customtkinter`
7) 

## Usage


## Example

## Contribution
We welcome all kinds of contributions! To contribute to the project, start by forking the repository, make your proposed changes in a new branch, and create a pull request. Make sure your code is readable and well-documented. Include unit tests if possible.

You can also contribute by submitting bug reports, feature requests, and following the issues.

## License
LGPL-3.0-only ou LGPL-3.0-or-later

## Authors
- Baudais Briac: baudaisbriac@gmail.com
