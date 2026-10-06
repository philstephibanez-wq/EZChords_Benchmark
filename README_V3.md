# EZChords_Benchmark V3 — minimal timelines

Périmètre strict :

1. analyser une chanson à la fois ;
2. attendre la fin de l'analyse ;
3. sauvegarder le résultat ;
4. liste des chansons analysées ;
5. clic sur une chanson ;
6. **une timeline compacte par algorithme** ;
7. Bon / Pas bon pour chaque algorithme ;
8. sauvegarde des choix ;
9. score global.

Supprimé de l'interface / flux :
- queued
- scheduler
- background job
- polling
- console worker
- grilles détaillées
- phases brutes

Le moteur Python reste identique.

## Application

Arrêter le serveur, puis :

```powershell
cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V3_MINIMAL_TIMELINES.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\recette.ps1

powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

Puis ouvrir :

```text
http://127.0.0.1:8701
```
