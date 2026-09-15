# -*- coding: utf-8 -*-
"""\brief Read key-value parameter tables from Excel workbooks.

This module is part of the PELCA reliability evaluator.
"""
import pandas as pd

# to get parameters from Excel sheet
# note: excel sheet read here and also in ExcelData.py
def read_parameters(excel_path, sheet_name):
    """Read parameters from an Excel sheet into a dictionary.
    Ignores numeric parameter names, which are assumed to be part of data tables."""
    df = pd.read_excel(excel_path, sheet_name=sheet_name, engine='openpyxl')

    # Find the column containing parameter names
    for col in df.columns:
        if (df[col].astype(str).str.contains('General parameters|PN|Vin', na=False).any()
            or  df[col].astype(str).str.contains('Options', na=False).any()):
            param_col = col # name of column where parameters names are found
            value_col = df.columns[df.columns.get_loc(param_col) + 1]  # Assume values are in the next column
            break
    else:
        raise ValueError("No parameter column found")

    # could ignore parameters with nan value
    # <table names, separators...>
    params = {row[param_col]: row[value_col] for _, row in df.iterrows() if pd.notna(row[param_col])}

    #
    params = {
        row[param_col]: row[value_col]
        for _, row in df.iterrows()
        if pd.notna(row[param_col]) and not str(row[param_col]).strip().isdigit()
    }
    return params
