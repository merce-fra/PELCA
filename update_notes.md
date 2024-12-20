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


# Pull Request: Fix Plot Widget (#20)

## Date 
06/12/2024 - 09/12/2024

## Description  
This pull request introduces several improvements and fixes to the plot widget functionality:

1. **Widget Improvements:**  
   - Moved `ImageButtonsWidget` to `PlotWidget` for easier rendering of plot thumbnails under the plot.

2. **Plot Display Updates:**  
   - Implemented dynamic switching between `WebEngine` and `canvas` for plot rendering.

3. **Data Structure Update:**  
   - Changed the plot data structure to support multiple plot types, starting with `matplotlib` and transitioning to `plotly`.

4. **Grid Addition:**  
   - Added a grid to the Cumulative Distribution Plot for improved readability.

5. **Code Cleanup:**  
   - Removed the `matplotlib` version of the plot and the Manufacturing environment impact plot.
   - Deleted the `matplotlib` dependencies from the interface and streamlined the plot widget.

6. **UI Improvements:**  
   - Updated the plot thumbnail button to display the `plotly` plot.
   - Removed switch logic from the control widget for better simplicity.

## Impact
- Provides dynamic rendering options between `WebEngine` and `canvas` for greater flexibility.
- Enhanced the structure to support diverse plot types and improved the UI for a more intuitive experience.

## Testing
- Functional tests on dynamic switching (passed).  
- Verified plot grid addition (successfully added).  
- Confirmed functionality with `plotly` (working as expected).  
- Ensured the eco impact plot integration with other plots is seamless (completed).  
- Checked UI changes, including the thumbnail button update (successful).


# Pull Request: Fix Export Image (#21)

## Date 
10/12/2024

## Description  
This pull request addresses issues with saving plots:

1. **Save Current Plot:**  
   - Fixed the "Save Current Plot" button to save the plot with the title from `plotting.py`.

2. **Save All Plots:**  
   - Fixed the "Save All Plots" button to allow saving all plots with the appropriate titles.

## Impact
- Ensures users can save individual and all plots correctly, with proper titles based on the plot data.

## Testing
- Verified functionality of both "Save Current Plot" and "Save All Plots" buttons.  
- Confirmed saved images have the correct titles from `plotting.py`.


# Pull Request: Move Monte Carlo Plotting Class and Update Bar Chart (#22)

## Date 
10/12/2024

## Description  
This pull request refactors the Monte Carlo plotting logic and updates the bar chart functionality:

1. **Refactor Monte Carlo Plotting:**  
   - Moved the Monte Carlo plotting class to a new file `plotting_MC.py` for better organization.

2. **Bar Chart Update:**  
   - Updated the bar chart functionality to enhance performance and visualization.

## Impact
- Improved the code organization by separating the Monte Carlo plotting logic into its own module.
- Enhanced the bar chart plotting for better visual representation.

## Testing
- Verified that the Monte Carlo plotting logic works after refactor.  
- Tested bar chart updates for visual correctness.


# **Pull Request: Fix Various Bug Fixes and Improvements for v1.2.0-rc1 (#23)**

## **Date**  
17/12/2024  

## **Description**  
This pull request includes multiple bug fixes, refactorings, and enhancements aimed at improving plot functionality, performance, and clarity in the interface.  

## **Changes**  
1. **Plot Saving Enhancements**  
   - Added **HTML export** functionality for plots.  
   - Improved folder structure for saved plots.  
   - Added titles to plots for better context and clarity.  

2. **Refactoring and Performance Improvements**  
   - Refactored `PLOT_MC` class to enhance radar chart visualization.  
   - Migrated staircase plots to **Plotly** for improved interactivity.  
   - Removed unused **Matplotlib** methods and plots from the `PLOT` class.  
   - Streamlined plotting functions and configurations for enhanced performance.  

3. **User Interface Updates**  
   - Updated x-axis and y-axis labels for clarity (e.g., adding currency to the y-axis).  
   - Renamed "Save Data" button for improved clarity in `ControlsWidget`.  
   - Improved trace naming and hover templates in plot layouts for better readability.  
   - Hid unused stream redirection in `ScriptWidget`.

4. **Plot Conversion and Layout Improvements**  
   - Integrated **Plotly conversion** for Matplotlib figures.  
   - Enhanced layout configurations for better visual results and interactivity.  
   - Added a grid to plots where applicable for improved readability.

## **Impact**  
- Improved plot saving functionality with additional export options.  
- Enhanced performance by removing unused methods and optimizing plotting logic.  
- Improved visual clarity and user experience across the interface.  

## **Testing**  
- Verified HTML export and folder structure for saved plots.  
- Tested radar chart and staircase plot visualizations in **Plotly**.  
- Confirmed layout updates, including axis labels and hover templates.  
- Tested the "Save Data" button and ensured consistent labeling.  
- Checked performance improvements after removing deprecated methods.