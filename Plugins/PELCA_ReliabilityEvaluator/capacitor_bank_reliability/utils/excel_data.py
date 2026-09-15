# -*- coding: utf-8 -*-
"""\brief Extract named two-column tables from Excel worksheets.

This module is part of the PELCA reliability evaluator.
"""
import pandas as pd
import numpy as np

# ===============================================
# to read parameters of a 2D table in excel sheet
# ===============================================
class ExcelData:
    """Represent excel data behavior used by reliability calculations."""
    def __init__(self, file_path, table_name, sheet_name='parameters'):
        """Initialize the object with the provided configuration."""
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.table_name = table_name
        self.data = self._extract_table()

    def _extract_table(self):
        # Load sheet with no headers so we can scan everything
        """Internal helper for extract table."""
        df = pd.read_excel(self.file_path, sheet_name=self.sheet_name, header=None)

        # Locate the cell with the table_name
        for row_idx in range(len(df)):
            for col_idx in range(len(df.columns)):
                if str(df.iat[row_idx, col_idx]).strip() == self.table_name:
                    # Assume table starts right below, and spans 2 columns
                    start_row = row_idx + 1
                    start_col = col_idx
                    end_col = col_idx + 2
                    # Now extract data until we hit an empty row
                    table_data = []
                    for r in range(start_row, len(df)):
                        row_vals = df.iloc[r, start_col:end_col]
                        if row_vals.isnull().all():
                            break
                        table_data.append(row_vals.to_list())
                    return np.array(table_data)

        raise ValueError(f"Table '{self.table_name}' not found in sheet '{self.sheet_name}'")

