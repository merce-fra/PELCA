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

For a detailed explanation of the algorithmic functioning of the tool, refer to [Algorithm.md](/Details/Algorithm.md).

The tool was developed using the Brightway2 library in Python.

## Table of Contents
- [Installation Guide](#installation-guide)
- [Usage](#usage)
- [Example](#example)
- [Contribution](#contribution)
- [License](#license)

## Installation Guide

### Initial Setup

1. **Install Miniconda**: Miniconda helps manage programming environments. You can download it from the [Miniconda Documentation](https://docs.conda.io/en/latest/miniconda.html).

2. **Create a Virtual Environment**: Open Miniconda. You will be in the "base" environment. Create a new virtual environment with the following command:
    ```bash
    conda create -n <your_environment_name>
    ```

3. **Activate the Environment**: Use the command below to activate the newly created environment:
    ```bash
    conda activate <your_environment_name>
    ```

4. **Install Required Python Libraries**: To use this project, you need to install certain Python libraries. Execute the following commands in Miniconda:
    ```bash
    conda install conda-forge::brightway2  # Version 2.4.6 - ACV library
    conda install conda-forge::spyder    # Version 5.5.5 - IDE environment
    conda install  bioconda::customtkinter # Version 5.2.2 - GUI
    conda install  conda-forge::pillow     # Version 10.4.0 - GUI
    ```

5. **Launch the IDE**: Start Spyder by running:
    ```bash
    spyder
    ```

6. **Open and Run Code**: Open your project code in Spyder and run it.

### Using the Project After Initial Setup

1. **Activate the Environment**: Open Miniconda. You will be in the "base" environment. Activate your virtual environment with:
    ```bash
    conda activate <your_environment_name>
    ```

2. **Launch Spyder**: Start Spyder by running:
    ```bash
    spyder
    ```

3. **Open and Run Code**: Open your project code in Spyder and run it.

## Usage

To use the tool:

- You need to download the Python `.py` files from the [src](/src) and place them in the same directory. To start the tool, execute the file `main_PELCA_GUI.py`.
- You must work with a specific Excel input file. You can find the general template in [Input](/Input) (Input - template.xlsx).



## Example
An example is detailed in the file [Example](/Example/Example.md).

## Contribution
We welcome all kinds of contributions! To contribute to the project, start by forking the repository, make your proposed changes in a new branch, and create a pull request. Make sure your code is readable and well-documented. Include unit tests if possible.

You can also contribute by submitting bug reports, feature requests, and following the issues.

## License
LGPL-3.0-only ou LGPL-3.0-or-later

## Authors
- Baudais Briac: baudaisbriac@gmail.com
