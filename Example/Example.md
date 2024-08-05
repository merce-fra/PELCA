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
