# EZStudio_lab — RESET HISTORY R1

Remise à zéro des données historiques/générées du laboratoire.

Supprimé :

- `data/benchmark.sqlite`, `benchmark.sqlite-wal`, `benchmark.sqlite-shm`
- `public/benchmark-audio/`
- `H:\temp\EZStudio_lab\stems`
- `H:\temp\EZStudio_lab\observability`
- `H:\temp\EZStudio_lab\exports`
- `H:\temp\EZStudio_lab\jobs`
- `H:\temp\EZStudio_lab\uploads`
- `H:\temp\EZStudio_lab\work`
- `H:\temp\EZStudio_lab\launcher`
- `H:\temp\EZStudio_lab\worker`
- base MongoDB `ezstudio_lab`

Conservé :

- code source et Git
- dépendances runtime (`deps`)
- cache Torch
- modèles externes
- `H:\EZS_orchestrator`

Le script arrête uniquement les workers Python EZStudio_lab identifiés, puis
recrée la base SQLite vide avec le schéma courant.

## Installation

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_RESET_HISTORY_R1.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1
```

## Exécution

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\reset-history-r1.ps1
```

Taper :

```text
RESET
```

Ou sans confirmation interactive :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\reset-history-r1.ps1 -Yes
```

Sortie finale attendue :

```text
EMPTY_DB_SCHEMA_OK
EZSTUDIO_SQLITE_HISTORY_EMPTY_OK
EZSTUDIO_RUNTIME_HISTORY_EMPTY_OK
EZSTUDIO_MONGO_HISTORY_EMPTY_OK
EZSTUDIO_HISTORY_RESET_R1_OK
```

Puis redémarrer EZStudio_lab :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```
