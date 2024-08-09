## Example Overview

This example is inspired by the case study presented in the thesis:
[Consult the thesis](https://theses.hal.science/tel-04659788)

The example is based on a two-Replacement Unit (RU) system:
- An IGBT power module (750V; 820A)
- A DC bus filtering capacitor

The data used are provided in the `Input - Example.xlsx` file. In the Excel file, modify the red-highlighted cells in the 'LCA' sheet to ensure the example works correctly.

### Running the Tool

Upon launching the tool, you will see the following interface:

<div align="center">
    <img src="../Images/exemple2.png" width="1000"/>
</div> 

Click on `Browse` to select the `Input - Example.xlsx` file, then press the `Run Script` button.

The terminal on the left will show the script execution process. When the calculation is complete, you will see the message "PELCA executed successfully". Additionally, various plots will be displayed as follows:

<div align="center">
    <img src="../Images/exemple1.png" width="1000"/>
</div>

Calculation results will be located in the `Results PELCA` folder.

<div align="center">
    <img src="../Images/exemple3.jpg" width="200"/>
</div>


### Saving Data

You can navigate between plots using the `Next` and `Previous` buttons or by clicking directly on the plot image. To save a specific plot, display the chosen plot and click the `Save` button. To save all plots, click the `Save All` button. The plots will be saved in the same directory as `Input - Example.xlsx`.

You can also choose to save lifecycle data for all RUs across all Monte Carlo iterations. The data options include total impacts, manufacturing-only impacts, usage-only impacts, faluts causes or RU age. Select the data you wish to save and click the `Save Data` button. This will open a folder selector, allowing you to save the data in your chosen location.

To reuse the data in Python, you can use the following code (the `recover_data.py` function can be found in the example folder):

```python
import recover_data
data_example=recover_data._rd_np(path_example,"data_example.npy")
```
