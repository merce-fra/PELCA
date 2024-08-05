Cette exemple est inspiré du cas d'étude présent dans la thèse :
[Consult the thesis](https://theses.hal.science/tel-04659788)

L'exemple est contruit à partir d'un système à deux RUs :
- Un module de puissance IGBT (750V ; 820A)
- Un condensateur de filtrage bus DC

Les données utilisées sont celle présentées dans le fichier `Input - Example.xlsx`.

Lors du lancement de l'outil voici l'interface obtenue :

<div align="center">
    <img src="../Images/exemple2.png" width="1000"/>
</div> 

Il faut alors cliquer sur Browse et sélectionner le fichier `Input - Example.xlsx`. Puis appuyer sur le bouton `Run Script`.

Le terminal a gauche présentera l'ancement du script, quand le calcul est terminé l'information " PELCA executed successfully" s'affiche.
Aussi les différents plots sont affichés comme suit :
<div align="center">
    <img src="../Images/exemple1.png" width="1000"/>
</div>

Vous pouvez naviger entre les plot avec les boutons next et previous mais aussi en cliquant directement sur l'image du plot.
Pour sauvegarder un plot, il faut afficher le plot choisi et cliquer suir le bouton `save`. Pous sauvegarder tous les plots il faut cliquer sur le bouton `save all`.
Les plot seront sauvegardez dans le meme dossier que celui de `Input - Example.xlsx`. Il s'y trouvera aussi les résultats du calcul des impacts dans le dossier `Results PELCA`.
<div align="center">
    <img src="../Images/exemple3.jpg" width="200"/>
</div> 

Vous pouvez aussi choisir de sauvegarder des données sur cycle de vie de tous les RUs, pour toutes les itérations Monte Carlo. Les données sont les impacts totaux, seulement fabrication, seulement utilisation ou l'âge des RU. Pour cela cocher les données que vous souhaitez sauvegarder et cliquer sur le bouton `Save Data`, cela va ouvrir le sélectionneur de dossier et sauvegarder les données là où vous aurez choisi.
Pour pouvoir réutiliser les données sous python je vous propose le code suivant (la fonction "recover_data.py" est à retrouver dans le dossier exemple

```python
import recover_data
data=recover_data._rd_np(path,"data.npy")
```

## Example Overview

This example is inspired by the case study presented in the thesis:
[Consult the thesis](https://theses.hal.science/tel-04659788)

The example is based on a two-Resource Unit (RU) system:
- An IGBT power module (750V; 820A)
- A DC bus filtering capacitor

The data used are provided in the `Input - Example.xlsx` file.

### Running the Tool

Upon launching the tool, you will see the following interface:

<div align="center">
    <img src="../Images/exemple2.png" width="1000"/>
</div> 

Click on "Browse" to select the `Input - Example.xlsx` file, then press the `Run Script` button.

The terminal on the left will show the script execution process. When the calculation is complete, you will see the message "PELCA executed successfully". Additionally, various plots will be displayed as follows:

<div align="center">
    <img src="../Images/exemple1.png" width="1000"/>
</div>

You can navigate between plots using the "Next" and "Previous" buttons or by clicking directly on the plot image. To save a specific plot, display the chosen plot and click the `Save` button. To save all plots, click the `Save All` button. The plots will be saved in the same directory as `Input - Example.xlsx`. Calculation results will be located in the `Results PELCA` folder.

<div align="center">
    <img src="../Images/exemple3.jpg" width="200"/>
</div>

### Saving Data

You can also choose to save lifecycle data for all RUs across all Monte Carlo iterations. The data options include total impacts, manufacturing-only impacts, usage-only impacts, or RU age. Select the data you wish to save and click the `Save Data` button. This will open a folder selector, allowing you to save the data in your chosen location.

To reuse the data in Python, you can use the following code (the `recover_data.py` function can be found in the example folder):

```p
