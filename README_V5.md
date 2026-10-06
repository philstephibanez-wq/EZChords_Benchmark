# EZChords Benchmark V5 — état réel GitHub corrigé

Ce livrable a été construit après inspection du `main` réellement poussé.

## Corrections

- menu de navigation : Analyser / Chansons / Scores ;
- corbeille par chanson ;
- suppression complète DB + audio + données associées ;
- validation par **case à cocher Bon** :
  - cochée = Bon ;
  - décochée = Pas bon lors de l'enregistrement ;
  - avant premier enregistrement : Non revu ;
- sélecteur Débutant / Intermédiaire / Confirmé déplacé hors du lecteur ;
- changement en temps réel des libellés d'accords dans toutes les timelines ;
- le piano virtuel joue exactement le niveau d'accord affiché ;
- MP3 servi directement depuis `public/benchmark-audio/` ;
- AudioContext initialisé explicitement sur geste utilisateur ;
- SoundFont chargée en arrière-plan, WebAudio audible immédiatement en fallback ;
- bouton `Test piano` pour diagnostiquer immédiatement la sortie WebAudio ;
- aucune modification EZScore.

## Application

Arrêter le serveur puis :

```powershell
cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V5_REALTIME_DISPLAY_NAV_TRASH.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1
```

Puis :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-v5.ps1
```

Attendu :

```text
V5_CONTRACT_OK
V5_CACHE_OK
V5_PREFLIGHT_OK
```

Ensuite :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\recette.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

## Test rapide

1. ouvrir une chanson ;
2. vérifier `Player V5` ;
3. cliquer `Test piano` : un La doit être audible ;
4. lancer le MP3 ;
5. sélectionner un algo et vérifier highlight + accord par beat ;
6. changer Débutant / Intermédiaire / Confirmé : les libellés changent immédiatement ;
7. vérifier que le piano joue la même simplification ;
8. revenir via le menu `Chansons` ;
9. tester la corbeille sur une chanson de test.
