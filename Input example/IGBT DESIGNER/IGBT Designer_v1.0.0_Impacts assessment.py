# -*- coding: utf-8 -*-
"""
Created on Tue Aug 6 08:46 2024

# imp.write_excel(only_unlinked=True) connaitre mauvais exchanges
# bw.Database('biosphere3').search('nickel')
# to list databases: bw.databases
# to check unlinked exchanges: list(imp.unlinked)

@authors: baudais / guillemet / pichon / lesaulnier
# %%
"""

# https://github.com/brightway-lca/brightway2-io/blob/main/bw2io/units.py

import pandas as pd
import brightway2 as bw
from brightway2 import *
from bw2data.parameters import ActivityParameter, DatabaseParameter, ProjectParameter, Group
from stats_arrays import *

# _______________________Variable définition_____________________________#

# Indicate name of device under test (DUT) #
DUT = 'IGBT die'

# Select impact assessment method / PEF: Product Environmental Footprint / CED : Cumulative Energy Demand #
type_method = 'PEF'
# type_method='CED'

# Indicate path and name of the inventory Excel file #
path_ex = r'F:\PES\PES_PHD\CIRH03\02 MERCE HMT ECODESIGN - PM LCI-LCA\5_PUBLICATIONS\0_GITHUB REPOSITORY\IGBT DESIGNER\\'
name_ex = 'IGBT Designer_v1.0.0_Manufacturing inventory.xlsx'

# Indicate path and version of the Ecoinvent database #
path_datasetEcoinvent = r'C:\\Users\\guillemet\\Downloads\\'
VersionEcoinvent = 'ecoinvent 3.9.1_cutoff_ecoSpold02'

# Indicate a name of the associated Brightway project #
proj_name = 'IGBT Designer'

# Indicate the name of the database as it appears in the inventory Excel file (sheet 'SUMMARY_LCI', box B1)
db_name = 'IGBT LCI dtb'

simulation = 'Analysis'

# Indicate paths and name of the result files #
path_result = path_ex
filename_result = 'IGBT Designer_v1.0.0_Manufacturing impacts.xlsx'

# _______________________________________________________________________#
# Open project #
projects.set_current(proj_name)

# Brightway2 set-up #
bw2setup()
print(bw.databases)

# Import ecoinvent database #
if 'ecoinvent 3.9.1_cutoff_ecoSpold02' in bw.databases:
    print('Database has already been imported.')
else:
    # mind that the ecoinvent file must be unzipped; then: path to the datasets subfolder #
    fpei37cut = path_datasetEcoinvent + VersionEcoinvent + r'/datasets'
    # the "r" makes sure that the path is read as a string - especially useful when you have spaces in your string #
    # ei37cutoff = bw.SingleOutputEcospold2Importer(fpei37cut, 'ecoinvent 3.91_cutoff_ecoSpold02') #
    ei37cutoff = bw.SingleOutputEcospold2Importer(fpei37cut, 'ecoinvent 3.9.1_cutoff_ecoSpold02', use_mp = False)
    ei37cutoff
    ei37cutoff.apply_strategies()
    ei37cutoff.statistics()
    ei37cutoff.write_database()

# bw.create_core_migrations()
# Import inventory Excel file
imp = bw.ExcelImporter("".join([path_ex, name_ex]))
imp.apply_strategies()
imp.match_database(fields=('name', 'reference product', 'unit', 'location'))
imp.match_database('ecoinvent 3.9.1_cutoff_ecoSpold02', fields=('name', 'reference product', 'unit', 'location'))
imp.statistics()

# you can check whether the import went as expected by having a look at an Excel sheet, that includes our process data #
# imp.write_excel()  

# Having imported the data, we also need to write it to a database to save it #
imp.write_database()

print('\n')
activities = bw.Database(db_name)  # activities presentation #
for act in activities:
    print(act)

# wbp = [act for act in activities][0]
# for exc in wbp.exchanges():
#     print(exc)

# activity to test for the LCA
# ex = [act for act in activities if 'Methanol, at plant' in act['name']][0]  # Check if exchange is good
# [exc for exc in ex.exchanges() ]
act_LCA=activities

###########################################

#_______________________________________________________________________#
# source Briac: https://github.com/maximikos/Brightway2_Intro/blob/master/BW2_tutorial.ipynb

# Impact assessment method and environmental impact categories
if type_method == 'PEF':
    SELECTED_IMPACT_CATEGORIES = [
        'climate change no LT',
        'ozone depletion no LT',
        'human toxicity: carcinogenic no LT',
        'human toxicity: non-carcinogenic no LT',
        'particulate matter formation no LT',
        'ionising radiation: human health no LT',
        'photochemical oxidant formation: human health no LT',
        'acidification no LT',
        'eutrophication: terrestrial no LT',
        'eutrophication: freshwater no LT',
        'eutrophication: marine no LT',
        'ecotoxicity: freshwater no LT',
        'land use no LT',
        'water use no LT',
        'material resources: metals/minerals no LT',
        'energy resources: non-renewable no LT',        
    ]

    def filter_func(m: tuple) -> bool:
        return (
            'EN15804' not in str(m)
            and m[1] in SELECTED_IMPACT_CATEGORIES
            and m[0] == 'EF v3.1 no LT'
        )

    methods = [
        method_key for method_key in bw.methods if filter_func(method_key)]

elif type_method == 'CED':
    methods = [[m for m in bw.methods if 'Cumulative Energy Demand (CED)' in str(
        m) and 'total' in str(m)][0]]

results = []

print('\n')
print('Starting LCA calculation :')
for act in act_LCA:
    print(act)
    lca = bw.LCA({act: 1})
    lca.lci()
    for method in methods:
        lca.switch_method(method)
        lca.lcia()
        results.append((act['name'], method[1].title(), lca.score))

# results
results_df = pd.DataFrame(results, columns=['Name', 'Method', 'Score'])
results_df = pd.pivot_table(results_df, index=['Method'], columns=['Name'], values='Score')
if type_method == 'PEF':
    results_df = results_df.reindex(['Climate Change No Lt','Ozone Depletion No Lt','Human Toxicity: Carcinogenic No Lt',
                                    'Human Toxicity: Non-Carcinogenic No Lt','Particulate Matter Formation No Lt','Ionising Radiation: Human Health No Lt',
                                    'Photochemical Oxidant Formation: Human Health No Lt','Acidification No Lt','Eutrophication: Terrestrial No Lt',
                                    'Eutrophication: Freshwater No Lt','Eutrophication: Marine No Lt','Ecotoxicity: Freshwater No Lt','Land Use No Lt',
                                    'Water Use No Lt','Material Resources: Metals/Minerals No Lt','Energy Resources: Non-Renewable No Lt'                                    
                                     ])
    
    results_df = results_df.rename(index={'Climate Change No Lt': 'GWP', 'Ozone Depletion No Lt': 'OD', 'Human Toxicity: Carcinogenic No Lt': 'HT',
           'Human Toxicity: Non-Carcinogenic No Lt': 'HTNC', 'Particulate Matter Formation No Lt': 'PMF',
           'Ionising Radiation: Human Health No Lt': 'IR',
           'Photochemical Oxidant Formation: Human Health No Lt': 'POF',
           'Acidification No Lt': 'TAP', 'Eutrophication: Terrestrial No Lt': 'TE',
           'Eutrophication: Freshwater No Lt': 'FE',
           'Eutrophication: Marine No Lt': 'ME', 'Ecotoxicity: Freshwater No Lt': 'FET','Land Use No Lt': 'LU',
           'Water Use No Lt': 'WD','Material Resources: Metals/Minerals No Lt': 'MRD', 'Energy Resources: Non-Renewable No Lt': 'FD',
          })

# Basic LCA
results_df.to_excel("".join([path_result, filename_result]))


# Ajouter la colonne des unités de mesure
#df_units['Unit'] = dic['LCIA_unit']

# Réorganiser les colonnes pour placer "Unit" en deuxième position
#results_df = df_units[['Unit'] + [col for col in results_df.columns if col != 'Unit']]



# Normalization and weighting part

# Global Normalization Factor PEF 2023: (Andreasi, B. S.; Biganzoli, F.; Ferrara, N.; Amadei, A.; Valente, A.; Sala, S.; Ardente, F. Updated characterisation and normalisation factors for the Environmental Footprint 3.1 method. JRC Publications Repository. https://doi.org/10.2760/798894.)
factors_global = [7.55e3, 5.23e-2, 1.73e-5, 1.29e-4, 5.95e-4, 4.22e3, 4.09e1, 5.56e1, 1.77e2, 1.61e0, 1.95e1, 5.67e4, 8.19e5, 1.15e4, 6.36e-2, 6.50e4]

# Planetary Boundaries Factor 2023: (Sala, S.; Crenna, E.; Secchi, M.; Sanyé-Mengual, E. Environmental Sustainability of European Production and Consumption Assessed against Planetary Boundaries. Journal of Environmental Management 2020, 269, 110686. https://doi.org/10.1016/j.jenvman.2020.110686.)
#factors = [6.81e12, 5.39e8, 9.62e5, 4.10e6, 5.16e5, 5.27e14, 4.07e11, 1.00e12, 6.13e12, 5.81e9, 2.01e11, 1.31e14, 1.82e14, 2.19e8, 2.24e14, 1.27e13]
factors_planet_bound = [6.81e12, 5.39e8, 9.62e5, 4.10e6, 5.16e5, 5.27e14, 4.07e11, 1.00e12, 6.13e12, 5.81e9, 2.01e11, 1.31e14, 1.27e13, 1.82e14, 2.19e8, 2.24e14]

# Weighting Factors PEF 2023: (Sala S., Cerutti A.K., Pant R., Development of a weighting approach for the Environmental Footprint, Publications Office of the European Union, Luxembourg, 2018, ISBN 978-92-7968042-7, EUR 28562, doi:10.2760/945290)
weighting_factors = [0.2106, 0.0631, 0.0213, 0.0184, 0.0896, 0.0501, 0.0478, 0.062, 0.0371, 0.028, 0.0296, 0.0192, 0.0794, 0.0851, 0.0755, 0.0832]

# Copie du DataFrame des résultats
norm_global_df = results_df.copy()
norm_planet_bound_df = results_df.copy()

# Application des normalisations
for i in range(len(factors_global)):
    norm_global_df.iloc[i] = norm_global_df.iloc[i] / factors_global[i]
    norm_planet_bound_df.iloc[i] = norm_planet_bound_df.iloc[i] / factors_planet_bound[i]

# Création des DataFrames pondérés
weight_global_df = norm_global_df.copy()
weight_planet_bound_df = norm_planet_bound_df.copy()

# Application des pondérations
for i, factor in enumerate(weighting_factors):
    weight_global_df.iloc[i] = weight_global_df.iloc[i] * factor
    weight_planet_bound_df.iloc[i] = weight_planet_bound_df.iloc[i] * factor

# Calcul de la somme des 16 premières lignes
sum_row_global = weight_global_df.iloc[:16].sum()
sum_row_planet_bound = weight_planet_bound_df.iloc[:16].sum()
weight_global_df.loc['Sum'] = sum_row_global
weight_planet_bound_df.loc['Sum'] = sum_row_planet_bound

# Écriture dans le fichier Excel
with pd.ExcelWriter("".join([path_result, filename_result]), engine='openpyxl', mode='a') as writer:
    norm_global_df.to_excel(writer, sheet_name='norm_global')
    norm_planet_bound_df.to_excel(writer, sheet_name='norm_planet_bound')
    weight_global_df.to_excel(writer, sheet_name='weight_global')
    weight_planet_bound_df.to_excel(writer, sheet_name='weight_planet_bound')