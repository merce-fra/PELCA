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

import numpy as np
import pandas as pd
import sys
from scipy.stats import weibull_min
import matplotlib.pyplot as plt
import random


def _wcdf(self,year,dic,nb_RU,weibull_Efault,weibull_Rfault,weibull_Wfault):
    
    weibull_E=np.array([[0 for i in range(nb_RU)] for z in range(dic["nb_ite_MC"])], dtype='float')
    weibull_R=np.array([[0 for i in range(nb_RU)] for z in range(dic["nb_ite_MC"])], dtype='float')
    weibull_W=np.array([[0 for i in range(nb_RU)] for z in range(dic["nb_ite_MC"])], dtype='float')
    if dic["Early_failure"]:    
        weibull_E=weibull_Efault[self.RU_age[year-1]][:,:,0]
    if dic["Random_failure"] :  
        weibull_R=weibull_Rfault[self.RU_age[year-1]][:,:,0]
        
    if dic["Wearout_failure"]:
        weibull_W=weibull_Wfault[self.RU_age[year-1]][:,:,0]

    wcdf=1-(1-weibull_E)*(1-weibull_R)*(1-weibull_W)
    
    return wcdf

class STAIRCASE():
    
    #%%
    def __init__(self,path_input,name_input,dic):
      self.usage_time =dic["service_life"]*dic["step"] # in month
      epsilon = 1e-10 #allow to avoid to divide by 0 during .../wcdf_sum
      self.t = np.linspace(epsilon, dic["service_life"], self.usage_time)
      
      excel = pd.ExcelFile("\\".join([dic["LCA_path"],dic["filename_result_EI"]]))
      
      # EI manufacturing of each RU
      df_manufacturing =pd.read_excel(excel, sheet_name='Manufacturing', index_col=0)
      df_manufacturing = df_manufacturing.drop(columns=['Unit'])
      self.EI_manufacturing = df_manufacturing.to_numpy()
      
      # EI manufacturing of total RU
      self.EI_manufacturing_total = self.EI_manufacturing.sum(axis=1)
      
      #losses of each RU
      df_EI_use_onestep=pd.read_excel(excel, sheet_name='Use', index_col=0)
      df_EI_use_onestep = df_EI_use_onestep.drop(columns=['Unit'])
      self.EI_use_onestep = df_EI_use_onestep.to_numpy()*dic["num_hourPerYear"]/dic["step"]
      
      #total losses
      self.EI_use_onestep_total =self.EI_use_onestep.sum(axis=1)

      # Number of component - remplacement unite
      dic["nb_RU"]=self.EI_manufacturing.shape[1]
      excel.close()

      
      excel = pd.ExcelFile("\\".join([path_input,name_input]))
      beta_sigma_ERW=pd.read_excel(excel, sheet_name='Faults', index_col=0, skiprows=[0,1,2]).to_numpy()
      excel.close()


      if beta_sigma_ERW.shape[0] != dic["nb_RU"]:
        print(f"Error: number of RU's faults ({beta_sigma_ERW.shape[0]}) is different from the expected number of RU {dic['nb_RU']}.")
        sys.exit(1)

      # Checking for the presence of "NaN" values
      if np.isnan(beta_sigma_ERW).any():
        print("Error: The fault table contains NaN.")
        sys.exit(1)
      
      dic["sigma_early"] = [sigma for sigma in beta_sigma_ERW[:, 0]]
      dic["sigma_random"] = [sigma for sigma in beta_sigma_ERW[:, 2]]
      dic["sigma_wearout"] = [sigma for sigma in beta_sigma_ERW[:, 4]]
      dic["beta_early"] = [sigma for sigma in beta_sigma_ERW[:, 1]]
      dic["beta_random"] = [sigma for sigma in beta_sigma_ERW[:, 3]]
      dic["beta_wearout"] = [sigma for sigma in beta_sigma_ERW[:, 5]]
            
      self.creation(dic)  

    #%%
    def creation(self,dic):
        nb_RU=dic["nb_RU"]
        nb_ite_MC=dic["nb_ite_MC"]
        t=self.t

        if dic["pre_set_fail"]==False:
            random_fault_time=np.array([[random.uniform(0, 1) for y in range(nb_ite_MC)] for y in range(nb_RU)], dtype='float').T
            random_fault_type=np.array([[random.uniform(0, 1) for y in range(nb_ite_MC)] for y in range(nb_RU)], dtype='float').T
       
        self.RU_age =np.array([[[0 for i in range(nb_RU)] for z in range(nb_ite_MC)] for y in range(self.usage_time)])
        self.driver_age =np.array([[[0 for i in range(nb_RU)] for z in range(nb_ite_MC)] for y in range(self.usage_time)])
        self.EI_total=np.array([[self.EI_manufacturing_total for z in range(nb_ite_MC)] for y in range(self.usage_time)], dtype='float')
        self.EI_total_manu=np.array([[self.EI_manufacturing_total for z in range(nb_ite_MC)] for y in range(self.usage_time)], dtype='float')
        self.EI_total_use=np.array([[self.EI_manufacturing_total*0 for z in range(nb_ite_MC)] for y in range(self.usage_time)], dtype='float')
        
        self.number_of_fault=np.array([[[0 for i in range(nb_RU)] for z in range(nb_ite_MC)] for y in range(self.usage_time)])

        self.fault_cause =np.array([[["" for i in range(nb_RU+nb_RU)] for z in range(nb_ite_MC)] for y in range(self.usage_time)], dtype="<U10")
      
        weibull_Efault=np.array([[0 for i in range(nb_RU)] for z in t], dtype='float')
        weibull_Rfault=np.array([[0 for i in range(nb_RU)] for z in t], dtype='float')
        weibull_Wfault=np.array([[0 for i in range(nb_RU)] for z in t], dtype='float')
       
        prob_weibull_Efault=np.array([[0 for i in range(nb_RU)] for z in t], dtype='float')
        prob_weibull_Rfault=np.array([[0 for i in range(nb_RU)] for z in t], dtype='float')
        prob_weibull_Wfault=np.array([[0 for i in range(nb_RU)] for z in t], dtype='float')
        
        time=np.array([t+1 for i in range(nb_RU)]).T
        
        (row_r,col_r)=dic["Remplacement_matrix"].shape
        remplacement=np.array([[[0 for y in range(col_r)] for z in range(nb_RU+nb_RU)] for i in range(nb_ite_MC)] , dtype='int')
        
        if dic["Early_failure"]:
            weibull_Efault=np.array(weibull_min.cdf(time-1,dic["beta_early"][:], scale=dic["sigma_early"][:]),ndmin=2, dtype='float')
            
        if dic["Random_failure"] : 
            weibull_Rfault=np.array(weibull_min.cdf(time-1,dic["beta_random"][:], scale=dic["sigma_random"][:]),ndmin=2, dtype='float')

        if dic["Wearout_failure"]:
            weibull_Wfault=np.array(weibull_min.cdf(time-1, dic["beta_wearout"], scale=dic["sigma_wearout"][:]),ndmin=2, dtype='float')
        
        wcdf_sum=np.sum([weibull_Efault,weibull_Rfault,weibull_Wfault],axis=0)
        
        wcdf=1-(1-weibull_Efault)*(1-weibull_Rfault)*(1-weibull_Wfault)
        self.wcdf_total=1-np.prod(1 - wcdf, axis=1)
        
        if dic["Early_failure"]:
            prob_weibull_Efault=weibull_Efault/wcdf_sum
        if dic["Random_failure"] :   
            prob_weibull_Rfault=weibull_Rfault/wcdf_sum

        if dic["Wearout_failure"]:
            prob_weibull_Wfault=weibull_Wfault/wcdf_sum
            
        wcdf_year=0
        
        for year in range(1,self.usage_time):
           
            self.RU_age[year,:,:]=self.RU_age[year-1,:,:]+1
            
             
            if dic["pre_set_fail"]==True:
                if year in dic["year_pre_set_fail"]:
                    indice_tuple=np.where(year==dic["year_pre_set_fail"])
                    indice = indice_tuple[0][0]
                    self.fault_cause[year,0,dic["UR_set_fail"][indice]]=dic["typefault_pre_set_fail"][indice]
                    remplacement[0,dic["UR_set_fail"][indice],:]=dic["Remplacement_matrix"].loc[dic["Remplacement_matrix"]["Fault"] == dic["typefault_pre_set_fail"][indice]].drop(["Fault"], axis=1).reset_index(drop=True).loc[dic["UR_set_fail"][indice]]
                
            else:
            
                #probabilité de défaillance individuelle de tout le système (ici driver et TO247)
                wcdf_oldyear=wcdf_year
                wcdf_year=_wcdf(self,year,dic,nb_RU,weibull_Efault,weibull_Rfault,weibull_Wfault)
                
                #détection des fautes pour chaque composant
                Fault=np.where((wcdf_oldyear<=random_fault_time) & (random_fault_time<=wcdf_year))
                notFault=np.where((wcdf_oldyear>random_fault_time) | (random_fault_time>wcdf_year))
                
                # Find the type of the fault for each RU
                Fault_E=np.where(random_fault_type[Fault] <= prob_weibull_Efault[self.RU_age[year,Fault[0],Fault[1]],Fault[1]])
                self.fault_cause[year,Fault[0][Fault_E],Fault[1][Fault_E]]="Early"
                remplacement[Fault[0][Fault_E],Fault[1][Fault_E],:]=dic["Remplacement_matrix"].loc[Fault[1][Fault_E]]
                
                down=prob_weibull_Efault[self.RU_age[year,Fault[0],Fault[1]],Fault[1]]
                up=down+prob_weibull_Rfault[self.RU_age[year]][Fault[0],0,Fault[1]]
                Fault_R=np.where((random_fault_type[Fault] >down) & (random_fault_type[Fault] <=up))
                self.fault_cause[year,Fault[0][Fault_R],Fault[1][Fault_R]+nb_RU]="Random"
                remplacement[Fault[0][Fault_R],Fault[1][Fault_R]+nb_RU,:]=dic["Remplacement_matrix"].loc[Fault[1][Fault_R]]
                
                down=up
                Fault_W=np.where((random_fault_type[Fault] >down))
                self.fault_cause[year,Fault[0][Fault_W],Fault[1][Fault_W]]="Wearout"
                remplacement[Fault[0][Fault_W],Fault[1][Fault_W],:]=dic["Remplacement_matrix"].loc[Fault[1][Fault_W]]
                
                #new random number for new component
                random_fault_time[Fault]=[random.uniform(0, 1) for y in Fault[1]]
                random_fault_type[Fault]=[random.uniform(0, 1) for y in Fault[1]] 
            
            remplacement_or=remplacement.any(axis=1).astype(int) 

            self.EI_total_manu[year,:,:]=self.EI_total_manu[year-1,:,:]+self.EI_manufacturing.dot(remplacement_or.T).T
            self.EI_total_use[year,:,:]= self.EI_total_use[year-1,:,:]+self.EI_use_onestep_total
            self.EI_total[year,:,:]= self.EI_total_use[year,:,:]+self.EI_total_manu[year,:,:]
            
            self.RU_age[year,:,:]=np.logical_not(remplacement_or[:,:nb_RU]).astype(int)*self.RU_age[year,:,:]
            self.number_of_fault[year,:,:]= self.number_of_fault[year-1,:,:]+remplacement_or[:,:nb_RU]
        
            #initialise
            remplacement=remplacement*0
        
    def get_variables(self):
        return self.EI_total, self.EI_total_manu, self.EI_total_use, self.usage_time, self.number_of_fault, self.wcdf_total, self.fault_cause, self.RU_age       
        