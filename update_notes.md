# Pull Request: Debug strcase (#18)
## Date 

06/12/2024

## Description

This pull request addresses an issue with the `strcase` and `plotting` file.


## Changes
1. **Bug Fixes**  
    - Corrected strcase eco impact
    - Corrected eco impact plot

## Impact
- Eco impact plot is filled with correct data

## Testing
- Manual test to check if economical impact plot is correct


# Pull Request: Update Script Widget with New Functionality and Validation (#19)

## Date 

06/12/2024

## Description
This pull request introduces several updates and improvements to the script widget:

1. **Disable Parameters Form**  
   - The parameters form on the script widget is now disabled when not needed.

2. **Added New Buttons**  
   - **"Run LCA + Staircase"** button.  
   - **"Run Staircase Only"** button.

3. **Script Buttons Visibility**  
   - Script buttons are now hidden if no Excel file is loaded in the app.

4. **Main Panel Button Replacement**  
   - Replaced the "Run Script" button on the main display panel with the new **"Run LCA + Staircase"** and **"Run Staircase Only"** buttons.

## Error Handling
If the **"Run Staircase Only"** button is used and the LCA result file (sheet `LCA`, cell `B3`) is not found in the expected result path (sheet `LCA`, cell `B2`), the app will display the following error message:  
> **Error:** The LCA result `[content of B3]` was not found in the LCA result path `[content of B2]`.

## Impact
These changes enhance usability by:
- Clarifying options for users.
- Restricting invalid actions.
- Providing clear and actionable error feedback when necessary.

## Testing
- Verified that the parameters form is disabled appropriately.  
- Confirmed that the new buttons appear and function as intended.  
- Tested the visibility toggle for script buttons when an Excel file is (or isn’t) loaded.  
- Simulated scenarios where the LCA result file or path is missing to ensure proper error handling.

