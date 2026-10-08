# R3B5A — hotfix du test fonctionnel DAG

Le défaut était dans le test R3B5, pas dans le bridge R3B5 validé.

R3B4 synchronise les anciens/current jobs STEMS dans l'ADN lorsqu'on ouvre la page STEMS.
Le script de test R3B5 cherchait directement `scientific_runs` sans effectuer cette
synchronisation préalable. Il pouvait donc répondre :

`No song with a completed STEMS ADN run and artifacts.`

alors que des jobs STEMS terminés existaient déjà.

R3B5A fait désormais, avant toute sélection de chanson :

`LabJobStore -> StemsDnaSync -> DnaRegistry`

sur l'historique STEMS réel.

Il affiche aussi un diagnostic précis :
- nombre de jobs STEMS ;
- nombre terminés ;
- nombre synchronisés ;
- nombre de runs ADN terminés avec artefacts ;
- pour chaque job : état, song_id, run_dir, existence du run_dir, run ADN et nombre d'artefacts.

Ce package ne modifie aucun moteur ni aucune classe applicative : il remplace uniquement
le script de test fonctionnel.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_R3B5A_DAG_FUNCTIONAL_TEST_HOTFIX.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\prepare-r3b5-dag-functional.ps1
```
