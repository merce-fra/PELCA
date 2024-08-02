"""                   GNU LESSER GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.


  This version of the GNU Lesser General Public License incorporates
the terms and conditions of version 3 of the GNU General Public
License, supplemented by the additional permissions listed below.

  0. Additional Definitions.

  As used herein, "this License" refers to version 3 of the GNU Lesser
General Public License, and the "GNU GPL" refers to version 3 of the GNU
General Public License.

  "The Library" refers to a covered work governed by this License,
other than an Application or a Combined Work as defined below.

  An "Application" is any work that makes use of an interface provided
by the Library, but which is not otherwise based on the Library.
Defining a subclass of a class defined by the Library is deemed a mode
of using an interface provided by the Library.

  A "Combined Work" is a work produced by combining or linking an
Application with the Library.  The particular version of the Library
with which the Combined Work was made is also called the "Linked
Version".

  The "Minimal Corresponding Source" for a Combined Work means the
Corresponding Source for the Combined Work, excluding any source code
for portions of the Combined Work that, considered in isolation, are
based on the Application, and not on the Linked Version.

  The "Corresponding Application Code" for a Combined Work means the
object code and/or source code for the Application, including any data
and utility programs needed for reproducing the Combined Work from the
Application, but excluding the System Libraries of the Combined Work.

  1. Exception to Section 3 of the GNU GPL.

  You may convey a covered work under sections 3 and 4 of this License
without being bound by section 3 of the GNU GPL.

  2. Conveying Modified Versions.

  If you modify a copy of the Library, and, in your modifications, a
facility refers to a function or data to be supplied by an Application
that uses the facility (other than as an argument passed when the
facility is invoked), then you may convey a copy of the modified
version:

   a) under this License, provided that you make a good faith effort to
   ensure that, in the event an Application does not supply the
   function or data, the facility still operates, and performs
   whatever part of its purpose remains meaningful, or

   b) under the GNU GPL, with none of the additional permissions of
   this License applicable to that copy.

  3. Object Code Incorporating Material from Library Header Files.

  The object code form of an Application may incorporate material from
a header file that is part of the Library.  You may convey such object
code under terms of your choice, provided that, if the incorporated
material is not limited to numerical parameters, data structure
layouts and accessors, or small macros, inline functions and templates
(ten or fewer lines in length), you do both of the following:

   a) Give prominent notice with each copy of the object code that the
   Library is used in it and that the Library and its use are
   covered by this License.

   b) Accompany the object code with a copy of the GNU GPL and this license
   document.

  4. Combined Works.

  You may convey a Combined Work under terms of your choice that,
taken together, effectively do not restrict modification of the
portions of the Library contained in the Combined Work and reverse
engineering for debugging such modifications, if you also do each of
the following:

   a) Give prominent notice with each copy of the Combined Work that
   the Library is used in it and that the Library and its use are
   covered by this License.

   b) Accompany the Combined Work with a copy of the GNU GPL and this license
   document.

   c) For a Combined Work that displays copyright notices during
   execution, include the copyright notice for the Library among
   these notices, as well as a reference directing the user to the
   copies of the GNU GPL and this license document.

   d) Do one of the following:

       0) Convey the Minimal Corresponding Source under the terms of this
       License, and the Corresponding Application Code in a form
       suitable for, and under terms that permit, the user to
       recombine or relink the Application with a modified version of
       the Linked Version to produce a modified Combined Work, in the
       manner specified by section 6 of the GNU GPL for conveying
       Corresponding Source.

       1) Use a suitable shared library mechanism for linking with the
       Library.  A suitable mechanism is one that (a) uses at run time
       a copy of the Library already present on the user's computer
       system, and (b) will operate properly with a modified version
       of the Library that is interface-compatible with the Linked
       Version.

   e) Provide Installation Information, but only if you would otherwise
   be required to provide such information under section 6 of the
   GNU GPL, and only to the extent that such information is
   necessary to install and execute a modified version of the
   Combined Work produced by recombining or relinking the
   Application with a modified version of the Linked Version. (If
   you use option 4d0, the Installation Information must accompany
   the Minimal Corresponding Source and Corresponding Application
   Code. If you use option 4d1, you must provide the Installation
   Information in the manner specified by section 6 of the GNU GPL
   for conveying Corresponding Source.)

  5. Combined Libraries.

  You may place library facilities that are a work based on the
Library side by side in a single library together with other library
facilities that are not Applications and are not covered by this
License, and convey such a combined library under terms of your
choice, if you do both of the following:

   a) Accompany the combined library with a copy of the same work based
   on the Library, uncombined with any other library facilities,
   conveyed under the terms of this License.

   b) Give prominent notice with the combined library that part of it
   is a work based on the Library, and explaining where to find the
   accompanying uncombined form of the same work.

  6. Revised Versions of the GNU Lesser General Public License.

  The Free Software Foundation may publish revised and/or new versions
of the GNU Lesser General Public License from time to time. Such new
versions will be similar in spirit to the present version, but may
differ in detail to address new problems or concerns.

  Each version is given a distinguishing version number. If the
Library as you received it specifies that a certain numbered version
of the GNU Lesser General Public License "or any later version"
applies to it, you have the option of following the terms and
conditions either of that published version or of any later version
published by the Free Software Foundation. If the Library as you
received it does not specify a version number of the GNU Lesser
General Public License, you may choose any version of the GNU Lesser
General Public License ever published by the Free Software Foundation.

  If the Library as you received it specifies that a proxy can decide
whether future versions of the GNU Lesser General Public License shall
apply, that proxy's public statement of acceptance of any version is
permanent authorization for you to choose that version for the
Library."""

"""
Created on 2024

@author: baudais
"""

import pandas as pd
import numpy as np
import brightway2 as bw
from brightway2 import *
from stats_arrays import *


def EI_calculation(dic,path_input, name_input):

    #open project
    projects.set_current(dic["proj_name"]) #Creating/accessing the project

    bw2setup() #Importing elementary flows, LCIA methods and some other data

    #ecoinvent
    if dic["database_ecoinvent"] in bw.databases:
        print("Database has already been imported.")
    else:
        # mind that the ecoinvent file must be unzipped; then: path to the datasets subfolder
        print("Database hasn't been imported.")
        fpei37cut = dic["database_ecoinvent_path"]
        # the "r" makes sure that the path is read as a string - especially useful when you have spaces in your string
        ei37cutoff = bw.SingleOutputEcospold2Importer(fpei37cut, dic["database_ecoinvent"],use_mp=False)
        ei37cutoff
        ei37cutoff.apply_strategies()
        ei37cutoff.statistics()
        ei37cutoff.write_database()
        
    bw.create_core_migrations()

    # Export excel
    imp = bw.ExcelImporter("\\".join([path_input,name_input]))
    imp.apply_strategies()
    imp.match_database(fields=('name', 'unit', 'location'))
    imp.match_database(dic["database_ecoinvent"], fields=('name', 'unit', 'location'))
    imp.statistics()

    # imp.write_excel()  # ou can check whether the import went as expected by having a look at an Excel sheet, that includes our process data.

    imp.write_database()  # Having imported the data, we also need to write it to a database to save it

    print('\n')
    activities = bw.Database(dic["inventory_name"]) # activities presentation
    for act in activities:
        print(act)
        
    act_LCA=activities
    methods = []

    for index, row in dic["LCIA"].iterrows():
        method_tuple = (row['Method name'], row['Impact category'], row['Specific context'])
        methods.append(method_tuple)

    results = []

    print('\n')
    print('Starting LCA calculation :')
    for act in act_LCA:
        print(act)
        lca = bw.LCA({act:1})
        lca.lci()
        for method in methods:
            lca.switch_method(method)
            lca.lcia()
            results.append((act["name"], method[1].title(), lca.score))
    #results
    
    #Mise en forme des résultats
    results_df = pd.DataFrame(results, columns=["Name", "Method", "Score"])
    method_order = results_df["Method"].unique()
    results_df  = results_df.pivot(index="Method", columns="Name", values="Score")
    results_df = results_df.reindex(method_order)
    new_methods = dic["EI_name"]
    rename_dict = dict(zip(method_order, new_methods))
    results_df = results_df.rename(index=rename_dict)

    results_df

    # Basic LCA
    # results_df.to_excel("".join([dic["path_result_EI"], dic["directory"],"\\",dic["filename_result_EI"]]))
    
    
    # Diviser le DataFrame en deux parties : avec et sans 'energy per hours'
    excel = pd.ExcelFile("\\".join([path_input,name_input]))
    df = pd.read_excel(excel, sheet_name='Inventory - Use', header=None)
    excel.close()
    
    # Initialiser une liste pour stocker les valeurs
    list_energy = []
    # Parcourir chaque ligne du DataFrame
    for index, row in df.iterrows():
        # Vérifier si le contenu de la colonne 0 est 'activity'
        if row[0] == "Activity":
            # Ajouter la valeur de la colonne 1 à la liste
            list_energy.append(row[1])
    df_without_energy = results_df.drop(columns=list_energy).copy()
    df_energy_only = results_df[list_energy].copy()
    
   # Ajouter la colonne des unités de mesure
    df_without_energy["Unit"] = dic["LCIA_unit"]
    df_energy_only["Unit"] = dic["LCIA_unit"]
    
    # Réorganiser les colonnes pour placer "Unit" en deuxième position
    df_without_energy = df_without_energy[['Unit'] + [col for col in df_without_energy.columns if col != 'Unit']]
    df_energy_only = df_energy_only[['Unit'] + [col for col in df_energy_only.columns if col != 'Unit']]

    # Écrire chaque partie dans une feuille différente
    excel_path = "\\".join([dic["path_result_EI"], dic["directory"], dic["filename_result_EI"]])
    with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
    # Écrire chaque partie dans une feuille différente
        df_without_energy.to_excel(writer, sheet_name='Manufacturing', index=True)
        df_energy_only.to_excel(writer, sheet_name='Use', index=True)

    # Monte Carlo part
    if dic["simulation"] == 'Monte Carlo' :
        # define the function for MC simulation
        iterations=dic["iterations"]
        def multiImpactMonteCarloLCA(functional_unit, list_methods, iterations):
            # Step 1
            MC_lca = bw.MonteCarloLCA(functional_unit)
            MC_lca.lci() #take time
            # Step 2
            C_matrices = {}
            # Step 3
            for method in list_methods:
                MC_lca.switch_method(method)
                C_matrices[method] = MC_lca.characterization_matrix
            # Step 4
            results = np.empty((len(list_methods), iterations))
            # Step 5
            i=0
            for iteration in range(iterations):
                next(MC_lca) # take time
                i=i+1
                print('Iteration : ', iteration)
                for method_index, method in enumerate(list_methods):
                    results[method_index, iteration] = (C_matrices[method]*MC_lca.inventory).sum()
            return results
            
        
        # define the LCIA methods, functional unit, and the number of iterations       
        fu = {act: 1 for act in activities}
        
        
        # let it run!
        print('\nMonte Carlo : ', dic["proj_name"])
        test_results = multiImpactMonteCarloLCA(fu, methods, iterations)

        st_dev_list = []
        mean_list = []
        mean_list_norm = []
        max_list_norm = []
        min_list_norm = []
        for i in range(0,len(test_results)) :
            st_dev = np.std(test_results[i,:])
            st_dev_list.append(st_dev)
            mean = np.mean(test_results[i,:])
            mean_print=100
            mean_list.append(mean)
            mean_list_norm.append(mean_print)
            maxi = (mean+2*st_dev)
            max_list_norm.append(maxi)
            minim = (mean-2*st_dev)
            min_list_norm.append(minim)
        
            
        
        list_results_MC = list(zip(dic["LCIA_unit"],mean_list,st_dev_list,max_list_norm,min_list_norm))
        results_df_MC = pd.DataFrame(list_results_MC, columns=["Unit","Mean", "SD", "Max", "Min"])
        results_df_MC.index =dic["EI_name"]
        results_df_MC = results_df_MC.reset_index()
        results_df_MC = results_df_MC.rename(columns={'index': 'Method'})
        results_df_MC.to_excel("\\".join([dic["path_result_EI"], dic["directory"],dic["filename_result_EI_MC"]]))
        