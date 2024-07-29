![](Images/first_image.png?raw=true)
PELCA (Power Electronics Life Cycle Assessment) est un projet open-source pour la quantification environnementale sur cycle de vie des systèmes d'électronique de puissance modulaire et diagnosticables. Ce projet fourni un outil qui permet de caculer les impacts environnementaux de la fabrication, de l'utilisation et d'u remplacement d'un produit d'électronique de puissance.
Ce travail


L’évolution des IE en fonction du temps peut être représentée comme ceci, appelé courbe en escalier:
![](Images/staircase.png?raw=true)
A t=0, il y a les IE à la fabrication du produit. Ensuite, la pente représente les IE à l’utilisation, c’est-à-dire les pertes à l’usage. Pour continuer, lors d’un défaut, les IE augmentent, cela correspond au remplacement de la partie défaillante. Le diagnostic et l’architecture (modularité) qui sont maintenant ajoutés influencent ce saut. Plus le diagnostic est précis et sélectif, plus le remplacement se fait uniquement sur le composant touché par le défaut, à condition d’avoir une modularité le permettant. Une architecture intégrée ne permet pas de séparer le composant en défaut du reste.


## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Contribution](#contribution)
- [License](#license)

## Installation


## Usage


## Example
An example of the code in action is detailed in the file [manualTutorial.md](manualTutorial.md)

## Contribution
We welcome all kinds of contributions! To contribute to the project, start by forking the repository, make your proposed changes in a new branch, and create a pull request. Make sure your code is readable and well-documented. Include unit tests if possible.

You can also contribute by submitting bug reports, feature requests, and following the issues.

## License
This project is licensed under the terms of the MIT license. By contributing to the project, you agree that your contributions will be licensed under its MIT license.

## Authors

- Baudais Briac: briac.baudais@ens-rennes.fr (Calculation Method Creator)
