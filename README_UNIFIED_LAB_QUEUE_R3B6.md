# EZStudio_lab — R3B6 Unified LAB Job Queue

Issues relues avant modification : #2, #3, #4, #6, #7.

## Cause corrigée

Avant R3B6, STEMS utilisait une queue JSON indépendante :

`StemsLabController -> LabJobStore -> H:\temp\EZStudio_lab\jobs`

alors que l'orchestrator lisait exclusivement :

`AnalysisDesktopController -> Database::analysisQueue() -> analysis_jobs`

Les jobs STEMS étaient donc invisibles pour `EZS_orchestrator`.
Le worker LAB refusait aussi `kind=stems`.

## Architecture R3B6

```text
IMPORT
  ↓
STEMS scientific_run
  ↓
analysis_jobs kind=stems
  ↓
API LAB /internal/analysis/desktop/jobs/*
  ↓
EZS_orchestrator target LAB
  ↓
analysis/worker_entrypoint.py
  ↓
python/ezstudio/pipeline/stems/runner.py
  ↓
progress / complete / fail
  ↓
scientific_run STEMS + artifacts SHA-256
```

CHORDS continue à utiliser la même table `analysis_jobs`.

`LabJobStore` et `StemsDnaSync` restent uniquement comme historique de migration.
Le workflow STEMS courant ne les utilise plus.
L'ancien endpoint `/stems/run` retourne HTTP 410 afin qu'il ne puisse plus créer une seconde queue.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_UNIFIED_LAB_QUEUE_R3B6.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-unified-lab-queue-r3b6.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-unified-lab-queue-r3b6.ps1
```

## Test réel

Après Import, lancer STEMS puis immédiatement :

```powershell
cd H:\EZS_orchestrator
H:\Python\pythoncore-3.14-64\python.exe -m control_center.cli queue --target lab
```

Avant claim, attendu :

```text
LAB: 1 job(s)
  {"job_id": ..., "kind": "stems", ...}
```
