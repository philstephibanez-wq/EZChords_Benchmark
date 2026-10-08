# EZStudio_lab — WORKBENCH NAV R3B1

Relecture préalable systématique : issues #2, #3, #4, #5, #6 et #7.

Objectif : restaurer la navigation vers les vues scientifiques existantes, sans les réécrire.

## Contrat

- `/` redirige vers `/home`.
- La page d'accueil est la liste des chansons analysées et de leurs états STEMS / CHORDS / LYRICS.
- Les imports multiples d'un même fichier sont regroupés par SHA-256.
- `Chords` résout la chanson sélectionnée vers le dernier run CHORDS terminé puis redirige vers `bench_view` existant.
- `RUN` reste `lab_run` existant avec STEMS / CHORDS / NO-CHORD / LYRICS / Diagnostics / Logs / Artefacts / Export.
- `Runs` montre l'historique de la chanson.
- L'onglet actif est déterminé par la route serveur.
- Le vieux JavaScript R3A3 de suivi de hash est retiré.
- Aucun moteur, aucune méthode CHORDS, aucun diagnostic, aucun worker, aucune queue n'est modifié.
