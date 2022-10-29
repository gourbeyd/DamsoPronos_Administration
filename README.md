
# DamsoPronos - Paris sportifs assistés par intelligence artificielle 

# Administration

Voici la partie "administration" du projet DamsoPronos.
L'objectif de cette partie est d'automatiser les tâches quotidiennes du projet.

Deux tâches sont à faire régulièrement :
- Faire tourner les modèles d'IA sur les matchs à venir.
- Mettre à jour les résultats une fois les matchs terminés.
  

## Analyse des matchs à venir

Le script *flashscore.py* scrappe les matchs à venir pour les 5 grands championnats sur le site *flashscore.fr*. Il récupère les informations nécessaires au bon fonctionnement des modèles développés. Le module *selenium*, avec Firefox en mode headless est utilisé.

Les modèles, entraînés au préalable, sont sauvegardés dans le dossier *models*.

Une fois les informations nécessaires récupérées, le script se charge de lancer le modèle qui prédit le résultat pour chaque match et inscrit ces informations en base de données.

## Mise à jour

Le script *update_pronos.py* est lui responsable de mettre à jour les pronostics. Pour cela, il cherche les matchs pour lesquels il n'y a pas de résultat en base de données et vérifie s'ils sont terminés. Si un match est terminé, le résultat du match et du pronostic sont mis à jour. 

Aussi, il est en charge de récupérer des statistiques sur le match, qui peuvent être utiles pour les modèles. Il met alors à jour le fichier *teamStats.csv*. 

Exemple de statistiques utilisés à ce jour : buts, tirs et tirs cadrés.