# EZStudio_lab — WORKBENCH R3A

Cette tranche est fondée sur la relecture systématique des issues #2, #3, #4, #5, #6 et #7.

Elle restaure :
- le catalogue des chansons ;
- la sélection explicite de la chanson de travail ;
- le contexte commun STEMS / CHORDS / LYRICS ;
- l'historique complet des runs de la chanson ;
- les paramètres déjà stockés : signature demandée/détectée, tempo, moteur/version, état, progression, dates ;
- les accès aux vues run et CHORDS existantes ;
- aucun vocabulaire queue/job/orchestrator dans l'UI métier.

Elle ne modifie pas :
- les six méthodes métriques CHORDS ;
- les moteurs Python ;
- la queue LAB ;
- l'orchestrator ;
- le player CHORDS ;
- les résultats historiques.

R3A ne simule pas encore des runs STEMS/CHORDS/LYRICS séparés : le modèle historique reste visible tel quel.
La tranche suivante introduira le Run Registry par item, puis STEMS autonome avec paramètres, génération, progression, historique, player multi-stems, diagnostics, comparaisons, logs et artefacts.
