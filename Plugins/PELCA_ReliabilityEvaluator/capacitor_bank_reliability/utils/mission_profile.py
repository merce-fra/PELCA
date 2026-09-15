# -*- coding: utf-8 -*-


"""\brief Read and display mission-profile blocks from Excel worksheets.

This module is part of the PELCA reliability evaluator.
"""
import pandas as pd
import collections

# desired enhancements: remove additional spaces in variable names...

# excel parameter reader

"""
This function reads an Excel file and structures the data into a hierarchical dictionary, where:
    Each block of data is identified by an incremental number in the first column or an empty row.
    Each block contains multiple lines of data.
    Each line within a block contains variable names and values, based on the column headers.
"""
def read_excel_to_dict(file_path, sheet_name=0):
    """Read excel to dict."""
    df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str)
    # dtype=str ensures that all values are read as strings to prevent unintended type conversions.

    data_dict = collections.defaultdict(lambda: collections.defaultdict(list))
    current_block = None
    # current_block keeps track of the current block number.

    for _, row in df.iterrows():
        first_value = str(row.iloc[0]).strip()

        if first_value == '' or first_value.isdigit():  # New block condition
            if first_value.isdigit():
                current_block = int(first_value)
            else:
                current_block = (current_block + 1) if current_block is not None else 1

        # Check that the row is not empty and not only NaN values.
        if not row.isna().all():

            block_dict = data_dict[current_block]

            #block_dict[len(block_dict) + 1] = row.to_dict()
            # len(block_dict) + 1 determines the line number within the block.
            # row.to_dict() converts the row into a dictionary {column_name: value}.
            # => The row is stored inside the block's dictionary under its line number.
            block_dict[len(block_dict) + 1] = row.to_dict()

    # data_dict is a nested dictionary where:
    # The first level keys are block numbers.
    # The second level keys are line numbers within a block.
    # The values are dictionaries storing the column names and their corresponding values.
    # =>
    # {
    #   block_number: {
    #       line_number: {column_name: value, column_name2: value2, ...},
    #       ...
    #   },
    #   ...
    # }
    return data_dict

def display_blocks(data_dict):
    """Display blocks."""
    for block, lines in data_dict.items():
        print(f"Block {block}:")
        for line, variables in lines.items():
            print(f"  Line {line}:")
            for key, value in variables.items():
                print(f"    {key}: {value}")
        print("\n")

# test
def get_block_variables(data_dict, block_number):
    """Read block variables."""
    if block_number not in data_dict:
        return []

    block_data = data_dict[block_number]
    def convert_to_number(value):
        """Convert to number."""
        if isinstance(value, (int, float)):
            return value  # Return as is if already numeric
        value = str(value).strip()  # Ensure value is treated as a string
        try:
            return float(value) if '.' in value else int(value)
        except ValueError:
            return value

    return [
        [convert_to_number(value) for key, value in variables.items() if key.lower() != "block"]
        for variables in block_data.values()
    ]

if __name__ == "__main__":
    excel_path = "../cap_analysis2.xlsx"  # "old/cap_analysis2.xlsx"
    data = read_excel_to_dict(excel_path, sheet_name='mission_profile')
    display_blocks(data)

    # number of blocks in data
    nb_blocks = len(data)

    for i in range(nb_blocks):
        block_number = i+1
        block_variables = get_block_variables(data, block_number)
        print(f"Variables in Block {block_number}: {block_variables}")


