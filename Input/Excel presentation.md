# Excel file

The Excel file is divided into 8 sheets that need to be filled out. **Cells highlighted in orange indicate areas that need to be modified.** :

- **`Inventory - Manufacturing`**

  This sheet follows the model of the Excel template used with the Brightway2 library. For more information, refer to the Brightway2 documentation.
  - You need to create one "activity" per Replacement Unit (RU).
  - Each activity should include "exchanges", which are the flows required for the manufacturing of the RU.
  -  **Note:** Do not forget to include the exchange representing the output flow. This exchange should be named same as the activity, with "amount" set to 1, "unit" set to "unit," and the database specified as the name of the database.

<p align="center">
    <img src="../Images/fonctionnement_excel.png?raw=true" width="800"/>
</p>


- **`Inventory - Use`**

  This sheet also follows the model of the Excel template used with the Brightway2 library. For more details, refer to the Brightway2 documentation.
  - You need to create one "activity" per Replacement Unit (RU). The activities represent the energy consumption during the use of the RU for one hour.
  - Each activity should include "exchanges", which are the flows required for the use of the RU for one hour.
  -  **Note:** Do not forget to include the exchange representing the output flow. This exchange should be named same as the activity, with "amount" set to 1, "unit" set to "unit," and the database specified as the name of the database.

- **`LCA`**

  Information related to the LCA (Life Cycle Assessment) calculations.

- **`LCIA`**

  Methods selected for environmental impact quantification over the life cycle.
  - In Brightway2, an LCIA (Life Cycle Impact Assessment) is defined with three parameters: "Method name," "Impact category," and "Specific context." Ensure these parameters are correctly specified to match the Brightway2 database.
  - To find the precise parameters for an LCIA, you can use the Activity Browser or directly query with the following Python code using the Brightway2 library:
    ```python
    import brightway2 as bw
    list(bw.methods)
    ```

- **`Staircase`**

  Information related to the creation of the staircase curve.

- **`Faults`**

  Modeling faults for each RU. You need one row per RU. For more details, refer to [Algorithm.md](/Details/Algorithm.md).

- **`Replac. Matrix`**

  Replacement matrix for modeling diagnostics. Ensure that the number of rows equals the number of columns and corresponds to the number of RUs. For more details, refer to [Algorithm.md](/Details/Algorithm.md).

- **`Licence (GNU LGPL)`**

  Information related to licensing under the GNU Lesser General Public License (LGPL).
