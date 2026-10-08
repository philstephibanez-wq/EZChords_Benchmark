# R3B5 — test fonctionnel réel du DAG

Ce package ne modifie pas l'application.

Il crée deux branches CHORDS sur :
- la même chanson ;
- le même run STEMS parent ;
- la même sélection NO-CHORD ;
- deux sélections CHORDS différentes.

Branche A :
`bass + guitar + piano + other`

Branche B :
`bass + guitar`

Puis il met les deux jobs `chords_scientific` dans la queue LAB.

Après exécution par EZS_orchestrator, le checker valide :
- deux scientific runs distincts ;
- deux analysis jobs distincts ;
- deux benchmark runs distincts ;
- même parent STEMS ;
- sélections CHORDS différentes ;
- sélection NO-CHORD identique ;
- SHA-256 des stems encore conformes ;
- état final `done` des trois niveaux ;
- `analysis_source=selected_stems` ;
- provenance `ezstudio.chords.selection.v1` conservée dans le résultat ;
- variante active `E_positive_harmonic_support_selected`.

## Installation

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_R3B5_DAG_FUNCTIONAL_TEST.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1
```

## 1. Préparer les deux branches

Auto-sélection de la dernière chanson ayant un STEMS ADN terminé :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare-r3b5-dag-functional.ps1
```

Ou avec un `song_id` précis :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare-r3b5-dag-functional.ps1 12
```

## 2. Vérifier la queue orchestrator

```powershell
cd H:\EZS_orchestrator
H:\Python\pythoncore-3.14-64\python.exe -m control_center.cli queue --target lab
```

Si le service orchestrator LAB est permanent, le laisser travailler normalement.

## 3. Vérifier le résultat

```powershell
cd H:\EZStudio_lab
powershell -ExecutionPolicy Bypass -File .\scripts\check-r3b5-dag-functional.ps1
```

Pendant l'analyse, le checker retourne :

```text
EZSTUDIO_R3B5_DAG_TEST_PENDING
```

Quand les deux branches sont réellement terminées :

```text
EZSTUDIO_R3B5_DAG_FUNCTIONAL_OK
EZSTUDIO_R3B5_DAG_FUNCTIONAL_PREFLIGHT_OK
```
