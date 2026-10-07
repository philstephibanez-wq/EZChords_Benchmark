# EZStudio_lab — CORE R1

Première tranche de migration vers le laboratoire autonome. Cette tranche est **additive** : aucun changement de `python/engine.py`, du worker V10, de SQLite, des six méthodes métriques ni de l'observabilité V10 actuelle.

## Contrats ajoutés

- `ExperimentRecord`
- `RunRecord`
- `ArtifactRecord`
- `ObservationRecord`
- `EventRecord`
- stockage immuable adressé par SHA-256
- workspace standard par item
- registry JSON/JSONL temporaire pour valider les contrats sans recâbler V10

Items : `import`, `stems`, `chords`, `no_chord`, `lyrics`.

Runtime autonome par défaut : `H:\temp\EZStudio_lab` via `EZSTUDIO_RUNTIME_ROOT`.

Arborescence d'un run :

```text
runs/<item>/<run_id>/
  inputs/
  outputs/
  features/
  diagnostics/
  logs/
  raw/
  manifest.json
```

## Installation

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_CORE_R1.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1
```

## Preflight

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-core-r1.ps1
```

Attendu :

```text
EZSTUDIO_CORE_R1_SCHEMA_OK
EZSTUDIO_CORE_R1_CONTENT_ADDRESSING_OK
EZSTUDIO_CORE_R1_RUN_WORKSPACE_OK
EZSTUDIO_CORE_R1_EZSCORE_INDEPENDENCE_OK
EZSTUDIO_CORE_R1_OK
EZSTUDIO_CORE_R1_PREFLIGHT_OK
```

## Contrôle Git

```powershell
git status --short
git diff --stat
```

Ne pas utiliser `git add -A`.

## Étape suivante après validation

CORE R2 : registry Mongo derrière les mêmes contrats, services Symfony Run/Artifact, navigation générique par item, puis extraction progressive de STEMS sans appel runtime à EZScore.
