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
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib
from matplotlib.projections.polar import PolarAxes
from matplotlib.patches import Circle, RegularPolygon
from matplotlib.path import Path
from matplotlib.projections import register_projection
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D
import math

def _decile(data, ax, var, display_decile,
            display_median, display_mean, display_max, display_legend,
           xlabel, ylabel, title, symlog=0, y_legend=1, xlog=False, ylim_min=0, x_legend=0.3):
    # Plot
    
    n_percentile = 10
    percent = np.linspace(0,100*(1-1/n_percentile), n_percentile)[1:]
    n_ite=len(data)
    n_percentile = len(percent)
    n_var = len(var)
    data_plot = np.zeros((n_var, n_percentile))
    data_max = np.zeros((n_var))
    data_min = np.zeros((n_var))
    for k in range(n_var):
        data_plot[k] = np.percentile(data[k], percent)
        data_max[k] = np.max(data[k])
        data_min[k] = np.min(data[k])
    if display_decile :
       for k in range(n_percentile):
            fill = ax.fill_between(var, data_plot[:,k], data_plot[:, n_percentile-1-k],
                            color="b", alpha =0.1, linewidth=0)
       fill.set_label("Decile")
    if display_median : ax.plot(var, data_plot[:,int(n_percentile/2)], "b", alpha= 0.7, label="Median")
    if display_mean : ax.plot(var, np.mean(data_plot, axis=1), "r", alpha= 0.7, label="Mean")
    if xlog : ax.set_xscale('log')
    if display_max :
        ax.plot(var, data_min, "b--", alpha=0.2, label="min max")
        ax.plot(var, data_max, "b--", alpha=0.2)
    if symlog != 0 :
        ax.set_yscale('symlog', linthresh=symlog)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: '{:g}'.format(y)))
    
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: '{:g}'.format(y)))
    # ax.set_xlabel(xlabel)
    if ylabel :
        ax.set_ylabel(ylabel, rotation=0, ha='right', va="bottom") # va="center" / "bottom"
    # ax.set_title(title)
    if display_legend : ax.legend(bbox_to_anchor=(x_legend, y_legend), loc='upper right')
    ax.set(xlim=(min(var), max(var)), ylim=(ylim_min, None))
    return ax

def radar_factory(num_vars, frame='circle'):
    """
    Create a radar chart with `num_vars` axes.

    This function creates a RadarAxes projection and registers it.

    Parameters
    ----------
    num_vars : int
        Number of variables for radar chart.
    frame : {'circle', 'polygon'}
        Shape of frame surrounding axes.

    """
    # calculate evenly-spaced axis angles
    theta = np.linspace(0, 2*np.pi, num_vars, endpoint=False)

    class RadarAxes(PolarAxes):

        name = 'radar'
        # use 1 line segment to connect specified points
        RESOLUTION = 1

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # rotate plot such that the first axis is at the top
            self.set_theta_zero_location('N')

        def fill(self, *args, closed=True, **kwargs):
            """Override fill so that line is closed by default"""
            return super().fill(closed=closed, *args, **kwargs)

        def plot(self, *args, **kwargs):
            """Override plot so that line is closed by default"""
            lines = super().plot(*args, **kwargs)
            for line in lines:
                self._close_line(line)

        def _close_line(self, line):
            x, y = line.get_data()
            # FIXME: markers at x[0], y[0] get doubled-up
            if x[0] != x[-1]:
                x = np.append(x, x[0])
                y = np.append(y, y[0])
                line.set_data(x, y)

        def set_varlabels(self, labels):
            self.set_thetagrids(np.degrees(theta), labels)

        def _gen_axes_patch(self):
            # The Axes patch must be centered at (0.5, 0.5) and of radius 0.5
            # in axes coordinates.
            if frame == 'circle':
                return Circle((0.5, 0.5), 0.5)
            elif frame == 'polygon':
                return RegularPolygon((0.5, 0.5), num_vars,
                                      radius=.5, edgecolor='k')
            else:
                raise ValueError("Unknown value for 'frame': %s" % frame)

        def _gen_axes_spines(self):
            if frame == 'circle':
                return super()._gen_axes_spines()
            elif frame == 'polygon':
                # spine_type must be 'left'/'right'/'top'/'bottom'/'circle'.
                spine = Spine(axes=self,
                              spine_type='circle',
                              path=Path.unit_regular_polygon(num_vars))
                # unit_regular_polygon gives a polygon of radius 1 centered at
                # (0, 0) but we want a polygon of radius 0.5 centered at (0.5,
                # 0.5) in axes coordinates.
                spine.set_transform(Affine2D().scale(.5).translate(.5, .5)
                                    + self.transAxes)
                return {'polar': spine}
            else:
                raise ValueError("Unknown value for 'frame': %s" % frame)

    register_projection(RadarAxes)
    return theta


class PLOT():
    
    def __init__(self, dic, EI, EI_manu, EI_use, usage_time, fault_cause,nb_RU,nb_ite_MC,step,wcdf):
        
        self.fig1=self.plot_allEI_manufacturing(dic, EI, EI_manu, EI_use, usage_time,nb_RU,nb_ite_MC,step)
        self.fig2=self.CDF(wcdf,usage_time)
        self.fig3=self.fault_repartition(fault_cause)
        self.fig4=self.plot_selectEI(dic,EI, EI_manu, EI_use, usage_time,nb_RU,nb_ite_MC,step)
        self.fig5=self.plot_allEI(dic, EI, EI_manu, EI_use, usage_time,nb_RU,nb_ite_MC,step)
             
    def plot_selectEI(self,dic, EI, EI_manu, EI_use, usage_time,nb_RU,nb_ite_MC,step): 
        
        t = np.arange(0, usage_time, 1)
        result_MC = EI[:, :, dic["selected_EI"]]
        result = EI[:, :, dic["selected_EI"]]
        result_fab = EI_manu[:, :, dic["selected_EI"]]
        result_use = EI_use[:, :, dic["selected_EI"]]
    
        if nb_ite_MC != 1:
            result_MC = result_MC[:, result_MC[0, :].argsort()]
            result_MC = pd.DataFrame(result_MC)
    
        fig, ax = plt.subplots(1, 1)
        var = np.arange(result_MC.shape[0]) / step
    
        if nb_ite_MC > 1:
            ax = _decile(result_MC.T, ax, var, display_decile=True, display_median=True, display_mean=True, display_max=True, display_legend=True, xlabel=True, ylabel=True, title=False)
        else:
            fab_use = pd.concat([pd.DataFrame(result_fab.T, index=['Manufacturing']).T, pd.DataFrame(result_use.T, index=['Use']).T], axis=1)
            w = 0.1
            ax.bar(var, fab_use["Manufacturing"], color=['blue'], width=w)
            ax.bar(var, fab_use["Use"], bottom=fab_use["Manufacturing"], color=['pink'], width=w)
            ax.plot(var, pd.DataFrame(result.T, index=['Total']).T)
            ax.legend(['Total', 'Manufacturing', 'Use'], loc='upper left', fontsize=14)
    
        # Ajuster les tailles des polices
        ax.set_ylabel(dic["EI_name"][dic["selected_EI"]], rotation=90, fontsize=14)
        ax.set_xlabel('Time (years)', fontsize=14)
        ax.grid(True)
    
        return fig
        
    def CDF(self,wcdf,usage_time):
        t = np.arange(0,usage_time,1)
        # Créer la figure et l'axe
        fig, ax = plt.subplots(figsize=(5, 3))  # Dimensions et résolution de la figure
        # Tracer les données
        ax.plot(t, wcdf, color='mediumvioletred', linewidth=2)
        # Ajouter des titres et des labels
        ax.set_title('Cumulative Distribution Function - All RU', fontsize=20, weight='bold')
        ax.set_xlabel('Time', fontsize=14)
        # Ajouter une grille
        ax.grid(True)
        
        # Afficher la figure
        plt.show()
        
        return fig
        
    def plot_allEI(self,dic, EI, EI_manu, EI_use, usage_time,nb_RU,nb_ite_MC,step):
        
        methods=dic["EI_name"]
        
        number_of_EI = len(dic["EI_name"])
        
        EI_plot =[[[1 for y in range(usage_time)] for y in range(nb_RU)] for z in range(nb_ite_MC)]
        # result=[[1 for y in range(usage_time)] for z in range(nb_ite_MC)]
        t = np.arange(0,usage_time,1)
        
        column, row = nb_ite_MC, usage_time
        result_MC=np.ones((row,column,number_of_EI))
        result=np.ones((column,row,number_of_EI))
        result_fab=np.ones((column,row,number_of_EI))
        result_use=np.ones((column,row,number_of_EI))
    
        #
        result_MC=EI[:,:,:]
        result=EI[:,:,:]
        result_fab=EI_manu[:,:,:]
        result_use=EI_use[:,:,:]

     
        row_fig=0
        col_fig=0
        
        # Calculer le nombre de lignes et de colonnes pour une grille carrée
        num_cols = int(math.ceil(math.sqrt(number_of_EI)))
        num_rows = int(math.ceil(number_of_EI / num_cols))
        
        # Créer les sous-graphiques
        fig, ax = plt.subplots(num_rows, num_cols, figsize=(10, 5), sharex=True)
        
        # Si num_rows ou num_cols est 1, axs peut être un tableau 1D ou 2D
        if num_rows == 1 or num_cols == 1:
            ax = np.reshape(ax, (num_rows, num_cols))  # Redimensionner en tableau 2D
    
        plt.subplots_adjust(left=0.1,
                    bottom=0.1,
                    right=0.9,
                    top=0.9,
                    wspace=0.35,
                    hspace=0.4)
        fig.add_subplot(111, frameon=False)
        # hide tick and tick label of the big axis

        for EI in range(number_of_EI):
            result_MC_EI = pd.DataFrame(result_MC[:,:,EI])
            
            if nb_ite_MC>1:        
                
                var = np.arange(result_MC_EI.shape[0])/step
                ax[row_fig,col_fig] = _decile(result_MC_EI.T, ax[row_fig,col_fig], var,display_decile=True,
                            display_median=True, display_mean=True, display_max=True, display_legend=False,
                           xlabel=True, ylabel=False, title=False)
                ax[row_fig,col_fig].ticklabel_format(axis="y", style="sci", scilimits=(0,0))
                ax[row_fig,col_fig].set_title(methods[EI],fontsize =16)
                ax[row_fig,col_fig].grid(True)
            if nb_ite_MC==1:
                ax[row_fig,col_fig].ticklabel_format(axis="y", style="sci", scilimits=(0,0))
                ax[row_fig,col_fig].set_title(methods[EI],fontsize =16)
                ax[row_fig,col_fig].grid(True)
                # ax=result.plot(kind='line',legend=False)
                # plt.figure()
                var = np.arange(result.shape[0])/step
                w=0.1
                ax[row_fig,col_fig].bar(var, result_fab[:,0,EI].T, color=['blue'],width=w)
                ax[row_fig,col_fig].bar(var, result_use[:,0,EI].T, bottom= result_fab[:,0,EI].T, color=['pink'], width=w)
                ax[row_fig,col_fig].plot(var, result[:,0,EI].T)
                # ax[row_fig,col_fig].legend(['Total','Manufacturing','Use'])
                if EI==0:
                    ax[row_fig,col_fig].legend(['Total','Manufacturing','Use'],bbox_to_anchor=(2.5, 1.30), loc='center', ncol=3)
            col_fig=col_fig+1
            if col_fig==4:
                col_fig=0
                row_fig=row_fig+1

        plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
        plt.xlabel("Time (years)",fontsize =14)

        plt.show()
        
        return fig
        
    def plot_allEI_manufacturing(self, dic, EI, EI_manu, EI_use, usage_time, nb_RU, nb_ite_MC, step):
        excel = pd.ExcelFile("\\".join([dic["LCA_path"],dic["filename_result_EI"]]))
        
        # EI manufacturing of each RU
        self.EI_manufacturing = pd.read_excel(excel, sheet_name='Manufacturing', index_col=0)
        
        self.EI_manufacturing =self.EI_manufacturing.drop(columns=['Unit'])
                
        
        index_labels = self.EI_manufacturing.columns.to_numpy()
        
        self.EI_manufacturing = self.EI_manufacturing.to_numpy()
        
        # EI manufacturing of total RU
        self.EI_manufacturing_total = self.EI_manufacturing.sum(axis=1)
        # Normalisation pour que chaque ligne somme à 1
        normalized_EI_manu = self.EI_manufacturing * 100 / self.EI_manufacturing_total[:, np.newaxis]
        
        # Création du graphique en barres empilées
        fig, ax = plt.subplots(figsize=(10, 7))
        
        # Nombre de lignes
        num_rows = normalized_EI_manu.shape[0]
        num_columns = len(index_labels)
        
        # Récupérer les noms des lignes
        line_names = dic["EI_name"]
        
        combined_labels = [f"{name} ({unit})" for name, unit in zip(line_names, dic["LCIA_unit"])]

        
        # Utilisation d'une colormap pour obtenir les couleurs
        cmap = matplotlib.colormaps.get_cmap('tab20b')
        colors = [cmap(i) for i in np.linspace(0, 1, num_columns)]
        
        
        # Barres empilées
        for i in range(num_rows):
            bottom = 0
            for j in range(num_columns):
                bar_color = colors[j % len(colors)]  # Utilisation des couleurs cycliquement
                ax.bar(i, normalized_EI_manu[i, j], color=bar_color, bottom=bottom)
                
                # Annotation pour les valeurs
                height = normalized_EI_manu[i, j]
                val=self.EI_manufacturing[i, j]
                ax.text(
                    i, 
                    bottom + height / 2, 
                    f'{val:.1e}', 
                    ha='center', 
                    va='center', 
                    fontsize=8, 
                    color='black',
                    bbox=dict(facecolor='white', alpha=0.5, edgecolor='none', boxstyle='round,pad=0.2')  # Fond gris
                )
                
                bottom += height
                
        # Labels et légende
        ax.set_ylabel('Normalized Value (%)', fontsize=14)
        ax.set_title('Manufacturing env. impact', fontsize=20, weight='bold')
        ax.set_xticks(range(num_rows))
        ax.set_xticklabels(combined_labels, rotation=45, ha='right', fontsize=12)
        ax.legend(index_labels, bbox_to_anchor=(0.5, -0.3), loc='upper center', fontsize=10)
        ax.set_ylim(0, 100)
        ax.set_yticks(np.arange(0, 101, 10))
        ax.grid(True, axis='y', alpha=0.7)
        
        plt.tight_layout()
        plt.show()
        
        return fig
        
    def fault_repartition(self, fault_cause):
            # Données
            tableau_1d = fault_cause.flatten()
            count_early = np.sum(tableau_1d == 'Early')
            count_random = np.sum(tableau_1d == 'Random')
            count_wearout = np.sum(tableau_1d == 'Wearout')
            nombres = [count_early, count_random, count_wearout]
            etiquettes = ['Early fault', 'Random fault', 'Wearout fault']
        
            # Couleurs correspondantes
            couleurs = plt.cm.tab20c(range(3))
        
            # Création du diagramme en camembert
            fig, ax = plt.subplots(figsize=(4, 4))
            ax.pie(nombres, labels=etiquettes, autopct='%1.1f%%', startangle=140, colors=couleurs, textprops={'fontsize': 14})
        
            # Ajout d'un titre avec une taille de police plus grande
            ax.set_title('Distribution of defects', fontsize=20, weight='bold')

            # Affichage du diagramme
            plt.show()
            
            return fig
            
class PLOT_MC():
    def __init__(self, dic):
        
        self.fig1=self.radar_montecarlo(dic)
        self.fig2=self.bar_with_uncertainty(dic)
        
    def radar_montecarlo(self,dic):
        N = len(dic["EI_name"])
        theta = radar_factory(N, frame='polygon')
       
        excel_LCA = pd.ExcelFile("\\".join([dic["LCA_path"],dic["filename_result_EI_MC"]]))
        df_LCA= pd.read_excel(excel_LCA, 0)
        excel_LCA.close()


        mean = df_LCA.loc[:,"Mean"]
        sd = df_LCA.loc[:,"SD"]

        
        mean=mean.to_numpy()
        sd = sd.to_numpy()
        
        mean_sum_norm=100*mean/mean
        
        min_sum_norm=100*(mean-2*sd)/mean
        max_sum_norm=100*(mean+2*sd)/mean
        
        categories = [f"{name} ({unit})" for name, unit in zip(dic["EI_name"], dic["LCIA_unit"])]
        
        # Define the data for each category
        max_values = [max_sum_norm[i] for i in range(len(categories))]
        mean_values = [mean_sum_norm[i] for i in range(len(categories))]
        min_values = [min_sum_norm[i] for i in range(len(categories))]
        
        # Package the data into a structured format
        data = [
            categories,  # List of categories
            (
                'Uncertainty Analysis - Monte Carlo',  # Title for the analysis
                [
                    max_values,  # Max values for each category
                    mean_values,  # Mean values for each category
                    min_values   # Min values for each category
                ]
            )
        ]
        
        
        spoke_labels = data.pop(0)

        colors = ['m', 'w', 'w']
        colors_line = ['mo', 'm', 'm.']
        
        title, case_data = data[0]

        fig, ax = plt.subplots(subplot_kw=dict(projection='radar'),figsize=(7, 5))
        fig.subplots_adjust(top=0.85, bottom=0.05)

        ax.set_title(title, fontsize=20, weight='bold',
                          horizontalalignment='center', verticalalignment='center', pad=20)
        alphas=[0.35,0.25,1]
        for d, color, alp, c_l in zip(case_data, colors, alphas, colors_line):
            line = ax.plot(theta, d, c_l)
            ax.fill(theta, d, facecolor=color, alpha=alp,label='_nolegend_')
            
        ax.set_varlabels(spoke_labels)
        
        # add legend relative to top-left plot
        labels = ('μ+2σ','Mean (μ)', 'μ-2σ')
        legend = ax.legend(labels, loc='upper center', bbox_to_anchor=(0.5, -0.1),
                   ncol=3, fontsize=14)
        
        plt.show()
        
        return fig
    
    def bar_with_uncertainty(self,dic):
        N = len(dic["EI_name"])
        
        # Charger les données
        excel_LCA = pd.ExcelFile("\\".join([dic["LCA_path"], dic["filename_result_EI_MC"]]))
        df_LCA = pd.read_excel(excel_LCA, 0)
        
        excel_LCA.close()

    
        # Extraire les moyennes et les écarts-types
        mean = df_LCA.loc[:, "Mean"].to_numpy()
        sd = df_LCA.loc[:, "SD"].to_numpy()
    
        # Normalisation
        mean_sum_norm = 100 * mean / mean
        min_sum_norm = 100 * (mean - 2 * sd) / mean
        max_sum_norm = 100 * (mean + 2 * sd) / mean
    
        # Labels des catégories
        categories = df_LCA.loc[:, "Method"].to_numpy()
        
        combined_labels = [f"{name} ({unit})" for name, unit in zip(categories, dic["LCIA_unit"])]
    
        # Création du graphique à barres
        fig, ax = plt.subplots(figsize=(10, 6))
    
        # Barres de moyenne
        yerr=[min_sum_norm, max_sum_norm]
        
        # Calcul des barres d'erreur avec correction des valeurs négatives
        lower_error = np.clip(mean_sum_norm - min_sum_norm, 0, None)
        upper_error = np.clip(max_sum_norm - mean_sum_norm, 0, None)
        
        bars = ax.bar(combined_labels, mean_sum_norm, yerr=[lower_error, upper_error],
                      capsize=5, color='plum', edgecolor='none', ecolor='midnightblue')
    
        # Ajouter les labels
        ax.set_ylabel('Normalized Value (%)', fontsize=14)
        ax.set_title('Uncertainty Analysis - Monte Carlo', weight='bold', fontsize=20)
        ax.tick_params(axis='x', rotation=45, labelsize=14)
        ax.tick_params(axis='y', labelsize=14)
        ax.set_xticks(np.arange(len(categories)))  # Assurez-vous que les ticks sont au bon endroit
        ax.set_xticklabels(combined_labels, rotation=45, ha='right', fontsize=12)

        
        # Add grid
        ax.yaxis.grid(True, linestyle='--', linewidth=0.7, color='grey')
    
        # Ajouter la légende
        ax.legend(['Uncertainty (μ±2σ)'], loc='upper center', bbox_to_anchor=(0.5, -0.4), fontsize=14, ncol=1)

    
        plt.tight_layout()
        plt.show()
        return fig
