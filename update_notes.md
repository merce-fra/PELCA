# Pull Request: New Features in **PELCA v 1.4.0**

## Date 
Date: 07 July 2025

## Overview
Version 1.4 of the PELCA software fixes several bugs — especially for economic-cost modeling during the use phase and the application of the inventory scaling factor — while introducing several new features.

## Change Log
### New Example: DC-Breaker
- Added the **Microchip MSCDR-EFUSE-006** E-Fuse model in the Input example folder.

### Economic Impact Modeling
- **Energy-cost fix**: hourly consumption of the Replacement Units (RUs) is now read from the **Inventory – Use** sheet of the input Excel file.

More details about the assessment of the economic impact can be found at [Example Overview](Input%20example/ExampleOverview.md).

### Scaling Factor in Inventory Sheets
- The Scaling Factor column is now present in the **Inventory – Manufacturing** and **Inventory – Use** sheets of the input Excel files.
    A Replacement Unit (RU) can include multiple elementary units. When an RU contains N identical items, the cell in the 'scaling factor' column and in the last row of the inventory displays 1/N. All flows defined for one elementary unit are therefore multiplied by N to obtain flows for the RU.


### UI/UX Enhancements
- **Version** field moved to `main.py` for easier maintenance.
- New **Contact Us** button that opens a pre-addressed e-mail to the PELCA team.
- **Export**: users can now save generated plots to **any chosen directory**.
- Display of the energy consumption of individual replacement units.

### Minor Fixes & Example Excel Files
- Updated colour scheme in the example spreadsheets to highlight columns used by Brightway:
  - **Red text**: data ingested by Brightway.
  - **Yellow cells**: user-editable values.
  - **Red cells**: values that must be corrected.

- Removed warnings for unused columns C and D of the 'Cost - Price' sheet.