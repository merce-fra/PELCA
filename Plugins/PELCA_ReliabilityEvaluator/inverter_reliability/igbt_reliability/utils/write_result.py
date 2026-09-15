# -*- coding: utf-8 -*-
"""\brief Write reliability results and replacement cost data to Excel.

This module is part of the PELCA reliability evaluator.
"""

from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter

# adapted for inverter
# TO DO: should be modified to completely rewrite result sheet (to avoid old data...)
def write_result(params, excel_path, sheet_name, lifetime, PELCA_params):
    """Write the result to the specified sheet."""
    book = load_workbook(excel_path)

    # if sheet_name not in book.sheetnames:
    #     book.create_sheet(sheet_name)

    # sheet = book[sheet_name]

    # --- Remove sheet if it already exists ---
    if sheet_name in book.sheetnames:
        ws_to_delete = book[sheet_name]
        book.remove(ws_to_delete)

    # --- Recreate empty sheet ---
    sheet = book.create_sheet(sheet_name)

    # first line
    sheet['B'+str(1)] = '(inverter_reliability)'
    sheet['D'+str(1)] = 'Parameters for PELCA (inverter modules)'
    sheet['D'+str(1)].font = Font(
        name='Calibri',
        bold=True,
        italic=False,
        size=11,
        color="000000" # black
    )
    sheet['F'+str(1)] = 'to copy into \'Faults & Prev. Maint.\' sheet of PELCA input Excel file'
    sheet['F'+str(1)].font = Font(
        name='Calibri',
        bold=True,
        italic=False,
        size=11,
        color="FF6347" # red
    )

    line_header=2
    sheet['A'+str(line_header)] = 'mission profile'
    sheet['B'+str(line_header)] = 'shortest lifetime (year) IGBT or diode'  # IGBT or diode or whole RU?
    # for early failure, defaults values (low fit rate) are used

    sheet['D'+str(line_header)] = 'Early failure (sigma, year)'     #  eta_early
    sheet['E'+str(line_header)] = 'Early failure (beta)'            #  beta_early
    sheet['F'+str(line_header)] = 'Random failure (sigma, year)'    #  eta_random
    sheet['G'+str(line_header)] = 'Random failure (beta)'           #  beta_random
    sheet['H'+str(line_header)] = 'Wear-out failure (sigma, year)'  #  eta_wearout
    sheet['I'+str(line_header)] = 'Wear-out failure (beta)'         #  beta_wearout

    # result here are the lifetimes for the different mission profiles
    # add the parameters for PELCA (random / wearout parts for each mission profile)

    for i in range(0,len(lifetime)):
        value = lifetime[i] # get lifetime value
        sheet['A' + str(i+line_header+1)] = 'profile '+str(i+1)
        sheet['A' + str(i + line_header + 1)].alignment = Alignment(horizontal='center', vertical='center')
        sheet['B' + str(i+line_header+1)] = value
        sheet['B' + str(i+line_header+1)].alignment = Alignment(horizontal='center', vertical='center')

        # parameters for PELCA (for whole RU: 6 power modules)
        # early life part
        sheet['D' + str(i + line_header + 1)] = PELCA_params['eta_early']
        sheet['D' + str(i + line_header + 1)].alignment = Alignment(horizontal='center', vertical='center')
        sheet['E' + str(i+line_header+1)] = PELCA_params['beta_early'] # beta<1
        sheet['E' + str(i + line_header + 1)].alignment = Alignment(horizontal='center', vertical='center')

        # (random part)
        eta = PELCA_params['eta_random'][i]
        sheet['F' + str(i+line_header+1)] = eta
        sheet['F' + str(i + line_header + 1)].alignment = Alignment(horizontal='center', vertical='center')
        sheet['G' + str(i+line_header+1)] = PELCA_params['beta_random'] # beta=1
        sheet['G' + str(i + line_header + 1)].alignment = Alignment(horizontal='center', vertical='center')

        # wearout part
        sheet['H' + str(i+line_header+1)] = PELCA_params['eta_wearout'][i]
        sheet['H' + str(i + line_header + 1)].alignment = Alignment(horizontal='center', vertical='center')
        sheet['I' + str(i+line_header+1)] = PELCA_params['beta_wearout']
        sheet['I' + str(i + line_header + 1)].alignment = Alignment(horizontal='center', vertical='center')

    # cost calculation

    # total_cost = man_hour_rate * (mounting_time + dismounting_time) + nb_capacitors * capacitor_cost
    RU_raw_cost = params['nb_parallel_sw'] * 3 * params['HB_module_cost']
    RU_assembly_cost    = params['man_hour_rate'] *  params['mounting_time']*(1/60)    # convert time in hours!
    RU_disassembly_cost = params['man_hour_rate'] *  params['dismounting_time']*(1/60)

    total_cost = RU_assembly_cost + RU_disassembly_cost + RU_raw_cost
    print("Maintenance cost:")
    print('with current topology, the replacement cost of inverter power modules (RU) would be:', total_cost, ' euros' )

    line_header_cost = i+line_header+3
    sheet['A'+str(line_header_cost)] = 'to copy into \'Cost - Price\' sheet of PELCA input Excel file'
    sheet['A'+str(line_header_cost)].font = Font(
        name='Calibri',
        bold=True,
        italic=False,
        size=11,
        color="FF6347" # red
    )
    line_header_cost = line_header_cost + 1

    # header for cost parameters
    sheet['A' + str(line_header_cost)] = 'RU raw cost/price (€)'
    #sheet['B' + str(line_header_cost)] = 'RU repair cost/price (%)' # change of format of PELCA input file
    sheet['B' + str(line_header_cost)] = 'RU assembly cost/price (€)'
    sheet['C' + str(line_header_cost)] = 'RU disassembly cost/price (€)'

    sheet['A' + str(line_header_cost + 1)] = RU_raw_cost
    sheet['A' + str(line_header_cost + 1)].alignment = Alignment(horizontal='center', vertical='center')
    # sheet['B' + str(line_header_cost + 1)] = '100.00 %' # (or 1.0 and cell type = percentage ?)
    sheet['B' + str(line_header_cost + 1)] = RU_assembly_cost
    sheet['B' + str(line_header_cost + 1)].alignment = Alignment(horizontal='center', vertical='center')
    sheet['C' + str(line_header_cost + 1)] = RU_disassembly_cost
    sheet['C' + str(line_header_cost + 1)].alignment = Alignment(horizontal='center', vertical='center')

    # resize columns (?)
    for col in sheet.columns:
        sheet.column_dimensions[col[0].column_letter].auto_size = True

    book.save(excel_path)
