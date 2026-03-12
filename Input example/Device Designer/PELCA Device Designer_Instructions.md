# How to use the **PELCA Device Designer** tools ?

## Introduction

Complementary to the PELCA software, which allows to simulate the environmental and economic impacts of power electronic (PE) systems throughout their life cycle, the PELCA Device Designer tools allow to compute the environmental impacts of the manufacturing phase of different semiconductor power devices, which are know to represent a significant share of the manufacturing impacts of PE systems. Once computed, the manufacturing impacts of the semiconductor power devices can then be reinjected into the PELCA tool to account for more accurate manufacturing impact assessment of PE systems.

The PELCA Device Designer tools address the following types of power semiconductors :
- Silicon-based insulated gate bipolar transistor (IGBT) ;
- Silicon power diode.

An open-source publication detailing the PELCA IGBT Designer tool is available online to get more acquainted with its structure and underlying impact assessment methodology : 

Guillemet, T.; Pichon, P.-Y.; Degrenne, N. An Open-Source Life Cycle Inventory (LCI) Model to Assess the Environmental Impacts of IGBT Power Semiconductor Manufacturing. Sustainability 2026, 18, 2663. https://doi.org/10.3390/su18052663

## Manufacturing model & impact assessment methodology

The PELCA Device Designer tools are based on a cradle-to-gate life cycle inventory (LCI) approach which includes :
- The production of the raw silicon wafers used as substrates ;
- The wafer process steps carried out to produce the power devices onto the wafers ;
- The cleanroom facilities & infrastructures operating to run the different utilities and maintain the production environment.

<p align="center">
    <img src="../Images/DeviceDesigner/Figure1.png" width="800"/>
    <br> Fig. 1 : System boundaries of PELCA Device Designer tools
</p>

In line with the PELCA software, the Device Designer tools are based on the Product Environmental Footprint (PEF) impact assessment method, allowing to assess the manufacturing impacts following 16 midpoint indicators. Figure 2 provides a schematic view of the software architecture of the PELCA Device Designer tools:

<p align="center">
    <img src="../Images/DeviceDesigner/Figure2.png" width="800"/>
    <br> Fig. 2 : Software architecture of the PELCA Device Designer tools and list of the impact categories of the PEF impact assessment method
</p>

Figure 3 provides a schematic view of the device on which is based the PELCA Device Designer tool dedicated to IGBT power transistors. The device is a vertical trench field-stop ultrathin IGBT power device, with voltage and current rating of 750 V and 270 A, respectively :

<p align="center">
    <img src="../Images/DeviceDesigner/Figure3.png" width="800"/>
    <br> Fig. 3 : Cross-section schematic of the trench field-stop IGBT power transistor used as reference device to build the PELCA IGBT Designer tool
</p>

The PELCA Device Designer tools allows the user to fine-tune the inventory to its own manufacturing use case through the following parameters :
- Die dimensions (length, width, thickness) (mm) ;
- Wafer diameter (150 mm, 200 mm, or 300 mm) ;
- Wafer 'killer defect' density (cm-2) and associated front-end yield model ;
- Probing yield (%) ;
- Dicing yield (%) ;
- Wafer fab location and associated local electricity mix ;
- Wafer fab cleanliness level (ISO class) ;
- Wafer fab throughput (wafers/month) ;
- Abatement efficiency of fluorinated gases (%) ;
- Wastewater recycling yield (%).

<p align="center">
    <img src="../Images/DeviceDesigner/Figure4a.png" width="800"/>
    <br> Fig. 4a : 'User inputs' sheet of the manufacturing inventory Excel file allowing the user to fine-tune the manufacturing inventory
</p>

The wafer process steps are splitted in the following 12 activites :
- Photolithography ;
- Wet clean ;
- Wet etch ;
- Dry etch ;
- Ion implant ;
- Thermal processes ;
- PVD ;
- CVD ;
- CMP ;
- Thinning ;
- Dicing ;
- Probing.

More details on how are modeled the production of the raw silicon wafer substrates, the wafer process steps, and the cleanroom facilites and infrastructures are available in the inventory Excel file and in the related published article.

Although the inventory model has been built based on a fixed device technology, the user is also able to fine-tune the manufacturing inventory by adjusting, in the 'Process Recap' sheet of the inventory Excel file, and for each sub-process step included in the model, the following parameters :
- Equipment nominal electrical power (kW) ;
- Power Correction Factor (PCF) ;
- Number of iterations along the wafer process flow.


## How to run the code ?

The PELCA Device Designer tools simply relies on an Excel file as the parametrizable manufacturing inventory and a Python script to connect the inventory to the ecoinvent database and assess the impacts using the Brightway library.

## Type of graphical outputs

### Contribution analyses

Contributions of raw wafer production, wafer process steps, and cleanroom facilities and infrastructures


### Sensitivity analyses

Impact of die size at constant wafer defect density

Impact of wafer defect density at constant die size

Impact of wafer fab location and associated electricity mix

### Impacts with respect to planetary bounds