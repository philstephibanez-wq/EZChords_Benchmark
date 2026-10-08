# EZStudio_lab — ORCHESTRATOR LAB R2

Issue : #7 — raccordement d'EZStudio_lab à la target LAB native d'EZS_orchestrator.

## Architecture

```text
upload EZStudio_lab
   ↓
analysis_jobs (SQLite LAB)
   ↓
EZS_orchestrator target=LAB
   ↓
claim
   ↓
Global\EZS_orchestrator_analysis_executor_v1
   ↓
H:\EZStudio_lab\analysis\worker_entrypoint.py
   ↓
python\worker.py
   ↓
progress / complete / fail
```

`BenchmarkLauncher::launch()` ne lance plus aucun processus Python : il enregistre
uniquement une job `queued`.

Le vieux script `scripts/start-benchmark-worker.ps1` est conservé comme artefact
historique mais n'est plus appelé par le workflow R2.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_ORCHESTRATOR_LAB_R2.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-orchestrator-lab-r2.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-orchestrator-lab-r2.ps1
```

## Démarrage LAB

```powershell
cd H:\EZStudio_lab
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

## Contrôle orchestrator

Une fois LAB démarré :

```powershell
cd H:\EZS_orchestrator
python -m control_center.cli queue --target lab
```

Puis, si le service permanent tournait encore avec l'ancien code :

```powershell
python -m service.service_cli stop
python -m service.service_cli start --target all --poll-seconds 2
python -m service.service_cli status
```

## Recette

Importer un morceau dans EZStudio_lab. Avant claim, la queue orchestrator doit
afficher un job `LAB / benchmark`. Après claim, l'exécution doit apparaître sous :

```text
H:\EZS_orchestrator\runtime\jobs\lab\<job>\
```

La progression doit remonter dans EZStudio_lab et le run doit finir `done`.

## Non-régression

- aucun import/runtime EZScore ;
- aucun write EZScore ;
- pipeline scientifique actuel conservé ;
- cache STEMS autonome conservé ;
- UI existante conservée ;
- aucun second worker permanent.
