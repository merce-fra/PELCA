<p align="center">
    <img src="Images/first_image.png?raw=true" alt="Staircase Curve" width="600"/>
</p>
PELCA (Power Electronics Life Cycle Assessment) is an open-source project aimed at assessing the environmental impact over the life cycle of modular and diagnosable power electronics systems. The integration of modularity and diagnosability aligns with circular economy principles, promoting practices such as repair and reuse. This project provides a tool to calculate the environmental impacts associated with the manufacturing, usage, and replacement of power electronics products.

This work began as part of the PhD thesis (collaboration between Mitsubishi Electric R&D Centre Europe and SATIE):
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
 
1. Initially, the curve shows the environmental impacts associated with the manufacturing of the product. 
2. The slope of the curve represents the impacts during usage, specifically the operational losses incurred. 
3. When a failure occurs, the impacts rise, reflecting the need to replace the faulty component. This increase is influenced by the accuracy of diagnostics and the system's architecture (modularity). More precise and selective diagnostics allow for more targeted replacements, assuming the modularity supports it. In contrast, an integrated architecture does not facilitate the separation of the faulty component from the rest of the system. The impact of diagnostics and modularity can be explained by the Replacement Rate (RR). An RR of 100% indicates a low-precision diagnosis, which provides no specific information when a fault occurs, leading to the replacement of the entire system or also no modularity. Conversely, an RR of 10% represents a more precise and selective diagnosis, where only 10% of the system is replaced. Thus, RR is directly related to the type of diagnostics and modularity.

For a detailed explanation of the algorithmic functioning of the tool, refer to [Algorithm.md](/Details/Algorithm.md).

The tool was developed using the Brightway2 library in Python.

## Table of Contents
- [Installation Guide](#installation-guide)
- [Usage](#usage)
- [Example](#example)
- [Contribution](#contribution)
- [Disclaimer](#disclaimer)
- [License](#license)

## Installation Guide

There are two options for installation: 

1. You can use the `PELCA.zip` file found in the `releases` to directly install the application on your computer.
2. If you prefer to have control over the code using an IDE, please follow the installation instructions below.

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

4. **Install Required Python Libraries**: To use this project, you need to install Python libraries. Execute the following commands in Miniconda:

   Brightway2 (Version 2.4.6 - ACV library)
   ```bash
    conda install -c conda-forge brightway2 numpy=1.26.4 scipy=1.13.1
    ```
    Spyder (Version 5.5.5 - IDE environment)
    ```bash
    conda install conda-forge::spyder
    ```
    Customtkinter (Version 5.2.2 - GUI)
    ```bash
    conda install bioconda::customtkinter
    ```
    Pillow (Version 10.4.0 - GUI)
    ```bash
    conda install conda-forge::pillow
    ```

6. **Launch the IDE**: Start Spyder by running:
    ```bash
    spyder
    ```

7. **Open and Run Code**: Open your project code in Spyder and run it (information in Usage part below), PELCA will open.

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
If you are using PELCA with an IDE :
- Click on `clone`, you can either clone the repository or download the .zip file directly (and then extract it). Inside PELCA folder you get Python `.py` files in the folder `src`. To start the tool, execute the file `main_PELCA_GUI.py` in your integrated development environment (IDE).

If you are using directly PELCA application :
- Download `PELCA.zip` file found in the `releases`, unzip the file and launch ...\PELCA\PELCA\main_PELCA_GUI.exe

To use the tool :
- You must work with a specific Excel input file. You can find the general template in [Input](/Input) (Input - template.xlsx) and an explanation of the Excel in the file [Excel presentation.md](/Input/Excel%20presentation.md).

### Uncertainty : Monte Carlo Simulation
It is also possible to perform uncertainty analyses using the Monte Carlo method with Pelca. To do this, you need to change line 12 from "Analysis" to "Monte Carlo" in the Excel sheet named "LCA", choose also the number of iterations, as shown in the following image:

<p align="center">
    <img src="Images/montecarlochoice.png?raw=true" alt="montecarlochoice" width="1000"/>
</p>

**IMPORTANT:** Currently, the results obtained using this method are not accurate. This appears to be due to an issue with Brightway2 and the handling of uncertainties related to biosphere flows, because same results are obtained in activity browser.


## Example
An example is detailed in the file [Example](/Example/Example.md).

## Contribution
We welcome all kinds of contributions! To contribute to the project, start by forking the repository, make your proposed changes in a new branch, and create a pull request. Make sure your code is readable and well-documented. Include unit tests if possible.

You can also contribute by submitting bug reports, feature requests, and following the issues.

## Disclaimer
This code is intended for use in a research environment only. We disclaim any responsibility for the results obtained and any subsequent use of them.

## License
 This code is licensed under LGPL-3.0-only or LGPL-3.0-or-later, and also uses other python libraries which also have their own licenses.
 
## Authors
- Baudais Briac: baudaisbriac@gmail.com
